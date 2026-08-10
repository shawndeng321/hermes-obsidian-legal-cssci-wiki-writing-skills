from __future__ import annotations

import argparse
import contextlib
import difflib
import hashlib
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import time
import zipfile
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import ContextManager
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen


CHECK_INTERVAL_SECONDS = 6 * 60 * 60
DEFAULT_SNOOZE_SECONDS = 4 * 60 * 60
NETWORK_TIMEOUT_SECONDS = 3.0
MAX_ARCHIVE_BYTES = 50 * 1024 * 1024
MAX_UNCOMPRESSED_BYTES = 200 * 1024 * 1024
MAX_ARCHIVE_FILES = 2_000
MAX_DIFF_TEXT_BYTES = 1024 * 1024
MAX_MANIFEST_BYTES = 1024 * 1024
MANIFEST_URL = (
    "https://raw.githubusercontent.com/shawndeng321/"
    "hermes-obsidian-legal-cssci-wiki-writing-skills/main/bundle-release.json"
)
ALLOWED_DOWNLOAD_HOSTS = {
    "github.com",
    "raw.githubusercontent.com",
    "codeload.github.com",
    "objects.githubusercontent.com",
    "release-assets.githubusercontent.com",
}

BUNDLE_ID = "hermes-legal-research-skills"
SKILLS = (
    "chinese-law-paper-writing",
    "legal-research-wiki",
    "legal-wiki-audit-repair",
)
STATE_FILE_NAME = "state.json"
LOCK_FILE_NAME = "operation.lock"
SEMVER_RE = re.compile(r"^(\d+)\.(\d+)\.(\d+)$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
DRIVE_PATH_RE = re.compile(r"^[A-Za-z]:")
MANIFEST_SEMANTIC_FIELDS = (
    "schema_version",
    "bundle_id",
    "bundle_version",
    "skills",
    "files",
)


class LockBusyError(RuntimeError):
    """Raised when another updater process holds the operation lock."""


class ArchiveError(RuntimeError):
    """Raised when an update archive or staged bundle is unsafe or invalid."""


@dataclass(frozen=True)
class FetchResult:
    manifest: dict | None
    etag: str | None
    not_modified: bool


def parse_semver(value: str) -> tuple[int, int, int]:
    if not isinstance(value, str):
        raise ValueError(f"invalid semantic version: {value!r}")
    match = SEMVER_RE.fullmatch(value)
    if not match:
        raise ValueError(f"invalid semantic version: {value!r}")
    return tuple(int(part) for part in match.groups())


def _validate_history(history: object, current_version: str) -> list[dict]:
    if not isinstance(history, list) or not history:
        raise ValueError("manifest history must be a non-empty list")
    validated: list[dict] = []
    versions: set[str] = set()
    for entry in history:
        if not isinstance(entry, dict):
            raise ValueError("manifest history entries must be objects")
        version = entry.get("bundle_version")
        parse_semver(version)
        if version in versions:
            raise ValueError(f"duplicate manifest history version: {version}")
        versions.add(version)
        for field in ("published_at", "update_level", "summary"):
            if not isinstance(entry.get(field), str) or not entry[field]:
                raise ValueError(f"invalid history {field}")
        changes = entry.get("changes")
        if not isinstance(changes, list) or not all(isinstance(item, str) for item in changes):
            raise ValueError("history changes must be a list[str]")
        validated.append(dict(entry))
    if current_version not in versions:
        raise ValueError("manifest history must include the current bundle version")
    return validated


def validate_manifest(data: object) -> dict:
    if not isinstance(data, dict):
        raise ValueError("manifest must be a JSON object")
    required = {
        "schema_version",
        "bundle_id",
        "bundle_version",
        "published_at",
        "update_level",
        "summary",
        "skills",
        "compatibility",
        "changes",
        "archive_url",
        "files",
        "history",
    }
    missing = required - set(data)
    if missing:
        raise ValueError(f"manifest is missing fields: {sorted(missing)}")
    if data["schema_version"] != 1 or data["bundle_id"] != BUNDLE_ID:
        raise ValueError("unsupported manifest identity")

    version = data["bundle_version"]
    parse_semver(version)
    for field in ("published_at", "update_level", "summary"):
        if not isinstance(data[field], str) or not data[field]:
            raise ValueError(f"invalid manifest {field}")
    if not isinstance(data["changes"], list) or not all(
        isinstance(item, str) for item in data["changes"]
    ):
        raise ValueError("manifest changes must be a list[str]")

    skills = data["skills"]
    if not isinstance(skills, dict) or set(skills) != set(SKILLS):
        raise ValueError("manifest skills must match the managed skill set")
    for skill_version in skills.values():
        parse_semver(skill_version)
    if not isinstance(data["compatibility"], dict):
        raise ValueError("manifest compatibility must be an object")

    archive_url = data["archive_url"]
    if not isinstance(archive_url, str):
        raise ValueError("manifest archive_url is not an approved HTTPS URL")
    parsed_url = urlparse(archive_url)
    if (
        parsed_url.scheme != "https"
        or parsed_url.hostname not in ALLOWED_DOWNLOAD_HOSTS
    ):
        raise ValueError("manifest archive_url is not an approved HTTPS URL")

    files = data["files"]
    if not isinstance(files, dict) or not files:
        raise ValueError("manifest files must be a non-empty object")
    for path, digest in files.items():
        if not isinstance(path, str) or not isinstance(digest, str) or not SHA256_RE.fullmatch(digest):
            raise ValueError("manifest files must map paths to SHA256 values")
    for skill_name in SKILLS:
        for required_path in ("SKILL.md", "agents/openai.yaml"):
            if f"{skill_name}/{required_path}" not in files:
                raise ValueError(f"manifest files missing {skill_name}/{required_path}")

    manifest = dict(data)
    manifest["history"] = _validate_history(data["history"], version)
    return manifest


def _safe_relative_path(value: object, *, label: str) -> PurePosixPath:
    if not isinstance(value, str) or not value or "\\" in value or "\0" in value:
        raise ArchiveError(f"unsafe {label}: {value!r}")
    if value.startswith("/") or value.endswith("/"):
        raise ArchiveError(f"unsafe {label}: {value!r}")
    parts = value.split("/")
    if any(part in {"", ".", ".."} for part in parts):
        raise ArchiveError(f"unsafe {label}: {value!r}")
    if DRIVE_PATH_RE.match(parts[0]) or any(":" in part for part in parts):
        raise ArchiveError(f"unsafe {label}: {value!r}")
    return PurePosixPath(*parts)


def _checked_manifest_files(manifest: dict) -> tuple[dict, dict[str, str]]:
    try:
        checked = validate_manifest(manifest)
    except (TypeError, ValueError) as exc:
        raise ArchiveError(f"invalid checked manifest: {exc}") from exc
    files: dict[str, str] = {}
    casefolded: set[str] = set()
    for raw_path, digest in checked["files"].items():
        path = _safe_relative_path(raw_path, label="manifest path")
        if path.parts[0] not in SKILLS:
            raise ArchiveError(f"manifest path is outside managed Skills: {raw_path}")
        normalized = path.as_posix()
        folded = normalized.casefold()
        if folded in casefolded:
            raise ArchiveError(f"manifest has a case-fold collision: {raw_path}")
        casefolded.add(folded)
        files[normalized] = digest
    return checked, files


def _manifest_semantics(manifest: dict) -> dict:
    return {field: manifest.get(field) for field in MANIFEST_SEMANTIC_FIELDS}


def _load_json_object(content: bytes, *, label: str) -> dict:
    try:
        data = json.loads(content.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ArchiveError(f"invalid {label}") from exc
    if not isinstance(data, dict):
        raise ArchiveError(f"invalid {label}")
    return data


def _verify_release_manifest(release: dict, manifest: dict) -> None:
    if _manifest_semantics(release) != _manifest_semantics(manifest):
        raise ArchiveError("archive manifest differs from checked manifest")


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _zip_member_path(info: zipfile.ZipInfo) -> tuple[PurePosixPath, bool]:
    name = getattr(info, "orig_filename", info.filename)
    if not isinstance(name, str) or not name or "\\" in name or "\0" in name:
        raise ArchiveError(f"unsafe archive member path: {name!r}")
    if name.startswith("/"):
        raise ArchiveError(f"unsafe archive member path: {name!r}")
    is_directory = info.is_dir()
    stripped = name[:-1] if is_directory else name
    if not stripped or stripped.endswith("/"):
        raise ArchiveError(f"unsafe archive member path: {name!r}")
    path = _safe_relative_path(stripped, label="archive member path")
    mode = (info.external_attr >> 16) & 0xFFFF
    if stat.S_ISLNK(mode):
        raise ArchiveError(f"archive contains a symlink: {name}")
    if mode and stat.S_ISDIR(mode) and not is_directory:
        raise ArchiveError(f"ambiguous archive directory entry: {name}")
    if info.flag_bits & 0x1:
        raise ArchiveError(f"encrypted archive member is not supported: {name}")
    return path, is_directory


def _read_zip_member(
    bundle: zipfile.ZipFile,
    info: zipfile.ZipInfo,
    *,
    maximum: int,
) -> bytes:
    if info.file_size > maximum:
        raise ArchiveError(f"archive member exceeds its read limit: {info.filename}")
    chunks: list[bytes] = []
    size = 0
    with bundle.open(info, "r") as stream:
        while True:
            chunk = stream.read(min(1024 * 1024, maximum - size + 1))
            if not chunk:
                break
            size += len(chunk)
            if size > maximum:
                raise ArchiveError(f"archive member exceeds its read limit: {info.filename}")
            chunks.append(chunk)
    if size != info.file_size:
        raise ArchiveError(f"archive member size mismatch: {info.filename}")
    return b"".join(chunks)


def _hash_zip_member(bundle: zipfile.ZipFile, info: zipfile.ZipInfo) -> str:
    digest = hashlib.sha256()
    size = 0
    with bundle.open(info, "r") as stream:
        while True:
            chunk = stream.read(1024 * 1024)
            if not chunk:
                break
            size += len(chunk)
            if size > info.file_size or size > MAX_UNCOMPRESSED_BYTES:
                raise ArchiveError(f"archive member size mismatch: {info.filename}")
            digest.update(chunk)
    if size != info.file_size:
        raise ArchiveError(f"archive member size mismatch: {info.filename}")
    return digest.hexdigest()


def _validate_archive_directory(
    bundle: zipfile.ZipFile,
    manifest: dict,
) -> tuple[tuple[str, ...], list[tuple[zipfile.ZipInfo, PurePosixPath, bool]]]:
    checked, manifest_files = _checked_manifest_files(manifest)
    infos = bundle.infolist()
    if len(infos) > MAX_ARCHIVE_FILES:
        raise ArchiveError("archive contains too many entries")
    if sum(info.file_size for info in infos) > MAX_UNCOMPRESSED_BYTES:
        raise ArchiveError("archive exceeds the uncompressed size limit")

    entries: list[tuple[zipfile.ZipInfo, PurePosixPath, bool]] = []
    seen: dict[str, str] = {}
    files_by_path: dict[PurePosixPath, zipfile.ZipInfo] = {}
    for info in infos:
        if info.file_size < 0 or info.compress_size < 0:
            raise ArchiveError(f"invalid archive member size: {info.filename}")
        path, is_directory = _zip_member_path(info)
        normalized = path.as_posix()
        folded = normalized.casefold()
        if folded in seen:
            raise ArchiveError(
                f"archive has a case-fold collision: {seen[folded]} and {normalized}"
            )
        seen[folded] = normalized
        entries.append((info, path, is_directory))
        if not is_directory:
            files_by_path[path] = info

    folded_files = {path.as_posix().casefold() for path in files_by_path}
    for path in files_by_path:
        for parent in path.parents:
            if parent == PurePosixPath("."):
                break
            if parent.as_posix().casefold() in folded_files:
                raise ArchiveError(f"archive file is also a parent path: {parent}")

    top_levels = {path.parts[0] for _, path, _ in entries}
    if len(top_levels) != 1:
        raise ArchiveError("archive must have one common top directory")
    prefix = (next(iter(top_levels)),)
    release_path = PurePosixPath(*prefix, "bundle-release.json")
    if release_path not in files_by_path:
        raise ArchiveError("archive must contain one bundle-release.json at its root")

    managed_files: dict[str, zipfile.ZipInfo] = {}
    for path, info in files_by_path.items():
        if path.parts[: len(prefix)] != prefix:
            raise ArchiveError("archive contains files outside the bundle root")
        relative = PurePosixPath(*path.parts[len(prefix) :]).as_posix()
        if relative.split("/", 1)[0] in SKILLS:
            managed_files[relative] = info

    missing = sorted(set(manifest_files) - set(managed_files))
    extra = sorted(set(managed_files) - set(manifest_files))
    if missing or extra:
        raise ArchiveError(f"archive file coverage mismatch; missing={missing}, extra={extra}")

    release_bytes = _read_zip_member(
        bundle, files_by_path[release_path], maximum=MAX_MANIFEST_BYTES
    )
    release = _load_json_object(release_bytes, label="archive bundle-release.json")
    _verify_release_manifest(release, checked)
    for relative, expected_digest in manifest_files.items():
        actual_digest = _hash_zip_member(bundle, managed_files[relative])
        if actual_digest != expected_digest:
            raise ArchiveError(f"archive file hash mismatch: {relative}")
    selected_entries = [
        (files_by_path[release_path], release_path, False)
    ]
    selected_entries.extend(
        (managed_files[relative], PurePosixPath(*prefix, relative), False)
        for relative in manifest_files
    )
    return prefix, selected_entries


def safe_extract_bundle(archive: Path, destination: Path, manifest: dict) -> Path:
    try:
        if archive.stat().st_size > MAX_ARCHIVE_BYTES:
            raise ArchiveError("archive exceeds the compressed size limit")
        with zipfile.ZipFile(archive, "r") as bundle:
            prefix, entries = _validate_archive_directory(bundle, manifest)
            if destination.is_symlink():
                raise ArchiveError("staging destination must not be a symlink")
            if destination.exists():
                if not destination.is_dir() or any(destination.iterdir()):
                    raise ArchiveError("staging destination must be an empty directory")
            else:
                destination.mkdir(parents=True)

            extracted_size = 0
            for info, relative, is_directory in entries:
                target = destination.joinpath(*relative.parts)
                if is_directory:
                    target.mkdir(parents=True, exist_ok=True)
                    continue
                target.parent.mkdir(parents=True, exist_ok=True)
                with bundle.open(info, "r") as source, target.open("xb") as output:
                    while True:
                        chunk = source.read(1024 * 1024)
                        if not chunk:
                            break
                        extracted_size += len(chunk)
                        if extracted_size > MAX_UNCOMPRESSED_BYTES:
                            raise ArchiveError("archive exceeds the uncompressed size limit")
                        output.write(chunk)
        bundle_root = destination.joinpath(*prefix) if prefix else destination
        verify_staged_bundle(bundle_root, manifest)
        return bundle_root
    except ArchiveError:
        raise
    except (OSError, RuntimeError, zipfile.BadZipFile, NotImplementedError) as exc:
        raise ArchiveError(f"unable to extract update archive: {exc}") from exc


def _walk_staged_files(bundle_root: Path) -> dict[str, Path]:
    files: dict[str, Path] = {}
    casefolded: set[str] = set()
    for current, directories, filenames in os.walk(bundle_root, followlinks=False):
        current_path = Path(current)
        for name in list(directories):
            path = current_path / name
            if path.is_symlink():
                raise ArchiveError(
                    f"staged bundle contains a symlink: {path.relative_to(bundle_root).as_posix()}"
                )
        for name in filenames:
            path = current_path / name
            relative = path.relative_to(bundle_root).as_posix()
            if path.is_symlink() or not path.is_file():
                raise ArchiveError(f"staged bundle contains an unsafe file: {relative}")
            folded = relative.casefold()
            if folded in casefolded:
                raise ArchiveError(f"staged bundle has a case-fold collision: {relative}")
            casefolded.add(folded)
            files[relative] = path
    return files


def verify_staged_bundle(bundle_root: Path, manifest: dict) -> None:
    checked, manifest_files = _checked_manifest_files(manifest)
    if bundle_root.is_symlink() or not bundle_root.is_dir():
        raise ArchiveError("staged bundle root is missing or unsafe")
    for skill_name in SKILLS:
        skill_root = bundle_root / skill_name
        if skill_root.is_symlink() or not skill_root.is_dir():
            raise ArchiveError(f"staged bundle is missing Skill directory: {skill_name}")

    staged_files = _walk_staged_files(bundle_root)
    expected_files = {"bundle-release.json", *manifest_files}
    missing = sorted(expected_files - set(staged_files))
    extra = sorted(set(staged_files) - expected_files)
    if missing or extra:
        raise ArchiveError(f"staged file coverage mismatch; missing={missing}, extra={extra}")

    release_path = staged_files["bundle-release.json"]
    if release_path.stat().st_size > MAX_MANIFEST_BYTES:
        raise ArchiveError("staged bundle-release.json exceeds its size limit")
    release = _load_json_object(
        release_path.read_bytes(), label="staged bundle-release.json"
    )
    _verify_release_manifest(release, checked)
    for relative, expected_digest in manifest_files.items():
        if _sha256_file(staged_files[relative]) != expected_digest:
            raise ArchiveError(f"staged file hash mismatch: {relative}")


def _ignored_installation_path(relative: PurePosixPath) -> bool:
    return (
        "bundle-lock.json" in relative.parts
        or "__pycache__" in relative.parts
        or ".DS_Store" in relative.parts
        or relative.suffix == ".pyc"
    )


def _installed_entries(skill_root: Path) -> dict[str, Path]:
    entries: dict[str, Path] = {}
    for current, directories, filenames in os.walk(skill_root, followlinks=False):
        current_path = Path(current)
        for name in list(directories):
            path = current_path / name
            relative = PurePosixPath(path.relative_to(skill_root).as_posix())
            if _ignored_installation_path(relative):
                directories.remove(name)
            elif path.is_symlink():
                entries[relative.as_posix()] = path
                directories.remove(name)
        for name in filenames:
            path = current_path / name
            relative = PurePosixPath(path.relative_to(skill_root).as_posix())
            if not _ignored_installation_path(relative):
                entries[relative.as_posix()] = path
    return entries


def _valid_local_lock(lock: object, skill_name: str) -> dict[str, str] | None:
    if not isinstance(lock, dict):
        return None
    if (
        lock.get("schema_version") != 1
        or lock.get("bundle_id") != BUNDLE_ID
        or lock.get("skill_name") != skill_name
    ):
        return None
    try:
        parse_semver(lock.get("bundle_version"))
        parse_semver(lock.get("skill_version"))
    except ValueError:
        return None
    files = lock.get("files")
    if not isinstance(files, dict):
        return None
    checked: dict[str, str] = {}
    casefolded: set[str] = set()
    try:
        for raw_path, digest in files.items():
            path = _safe_relative_path(raw_path, label="bundle lock path")
            normalized = path.as_posix()
            if (
                not isinstance(digest, str)
                or not SHA256_RE.fullmatch(digest)
                or normalized.casefold() in casefolded
            ):
                return None
            casefolded.add(normalized.casefold())
            checked[normalized] = digest
    except ArchiveError:
        return None
    return checked


def inspect_installation(skills_root: Path, manifest: dict) -> dict:
    checked, _ = _checked_manifest_files(manifest)
    modified: list[str] = []
    deleted: list[str] = []
    added: list[str] = []
    missing_skills: list[str] = []

    for skill_name in SKILLS:
        if skill_name not in checked["skills"]:
            continue
        skill_root = skills_root / skill_name
        if skill_root.is_symlink() or not skill_root.is_dir():
            missing_skills.append(skill_name)
            continue
        lock_path = skill_root / "bundle-lock.json"
        lock_relative = f"{skill_name}/bundle-lock.json"
        if lock_path.is_symlink() or not lock_path.is_file():
            deleted.append(lock_relative)
            continue
        try:
            lock = json.loads(lock_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            modified.append(lock_relative)
            continue
        expected = _valid_local_lock(lock, skill_name)
        if expected is None:
            modified.append(lock_relative)
            continue

        actual = _installed_entries(skill_root)
        for relative, expected_digest in expected.items():
            installed_path = actual.get(relative)
            repository_relative = f"{skill_name}/{relative}"
            if installed_path is None or not installed_path.exists():
                deleted.append(repository_relative)
            elif installed_path.is_symlink() or not installed_path.is_file():
                modified.append(repository_relative)
            elif _sha256_file(installed_path) != expected_digest:
                modified.append(repository_relative)
        for relative in set(actual) - set(expected):
            added.append(f"{skill_name}/{relative}")

    modified.sort()
    deleted.sort()
    added.sort()
    missing_skills.sort()
    has_changes = any((modified, deleted, added, missing_skills))
    return {
        "status": "local_changes" if has_changes else "clean",
        "modified": modified,
        "deleted": deleted,
        "added": added,
        "missing_skills": missing_skills,
    }


def _diff_path(root: Path, relative: str) -> Path:
    path = _safe_relative_path(relative, label="diff path")
    return root.joinpath(*path.parts)


def _text_for_diff(path: Path) -> str | None:
    if not path.exists():
        return ""
    if path.is_symlink() or not path.is_file() or path.stat().st_size >= MAX_DIFF_TEXT_BYTES:
        return None
    content = path.read_bytes()
    if b"\0" in content:
        return None
    try:
        return content.decode("utf-8")
    except UnicodeDecodeError:
        return None


def _hash_for_diff(path: Path) -> str:
    if not path.exists():
        return "missing"
    if path.is_symlink():
        return "symlink"
    if not path.is_file():
        return "not-a-file"
    return _sha256_file(path)


def format_incoming_diff(
    skills_root: Path,
    staged_root: Path,
    changed_paths: list[str],
) -> str:
    sections: list[str] = []
    for relative in sorted(set(changed_paths)):
        installed_path = _diff_path(skills_root, relative)
        incoming_path = _diff_path(staged_root, relative)
        installed_text = _text_for_diff(installed_path)
        incoming_text = _text_for_diff(incoming_path)
        if installed_text is not None and incoming_text is not None:
            diff = "".join(
                difflib.unified_diff(
                    installed_text.splitlines(keepends=True),
                    incoming_text.splitlines(keepends=True),
                    fromfile=f"installed/{relative}",
                    tofile=f"incoming/{relative}",
                )
            ).rstrip("\n")
            if diff:
                sections.append(diff)
                continue
        sections.append(
            f"[hash] {relative}: {_hash_for_diff(installed_path)} -> "
            f"{_hash_for_diff(incoming_path)}"
        )
    return "\n\n".join(sections)


def _remove_tree(path: Path) -> None:
    if path.is_symlink() or path.is_file():
        path.unlink()
    elif path.exists():
        shutil.rmtree(path)


def detect_installation_mode(
    skills_root: Path, skill_names: Sequence[str]
) -> str:
    """Identify a normal copied-source installation without following links."""
    skills_root = Path(skills_root)
    if skills_root.is_symlink():
        raise ArchiveError("Skills root is a symlink")
    if not skills_root.is_dir():
        raise ArchiveError(f"Skills root is not a directory: {skills_root}")
    if (skills_root / ".git").exists():
        raise ArchiveError("Git worktree installations are not supported")

    seen: set[str] = set()
    for raw_name in skill_names:
        if not isinstance(raw_name, str) or raw_name in seen:
            raise ArchiveError("invalid or duplicate Skill name")
        seen.add(raw_name)
        relative = _safe_relative_path(raw_name, label="Skill name")
        if len(relative.parts) != 1:
            raise ArchiveError(f"invalid Skill name: {raw_name}")
        skill_root = skills_root / raw_name
        if skill_root.is_symlink():
            raise ArchiveError(f"Skill directory is a symlink: {raw_name}")
        if not skill_root.exists():
            continue
        if not skill_root.is_dir():
            raise ArchiveError(f"Skill path is not a directory: {raw_name}")
        if (skill_root / ".git").exists():
            raise ArchiveError(f"Git worktree Skill is not supported: {raw_name}")
    return "source-copy"


def _copy_worker_script(state_root: Path) -> Path:
    worker_root = state_root / "worker"
    worker_root.mkdir(parents=True, exist_ok=True)
    worker_path = worker_root / Path(__file__).name
    if worker_path.is_symlink():
        raise ArchiveError("worker path is a symlink")
    if worker_path.resolve() != Path(__file__).resolve():
        shutil.copy2(Path(__file__), worker_path)
    return worker_path


def _verify_installed_bundle(skills_root: Path, manifest: dict) -> None:
    checked, manifest_files = _checked_manifest_files(manifest)
    for skill_name in SKILLS:
        skill_root = skills_root / skill_name
        if skill_root.is_symlink() or not skill_root.is_dir():
            raise ArchiveError(f"installed Skill is missing or unsafe: {skill_name}")
        lock_path = skill_root / "bundle-lock.json"
        try:
            lock = json.loads(lock_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ArchiveError(f"installed lock is invalid: {skill_name}") from exc
        expected_lock = {
            path[len(skill_name) + 1 :]: digest
            for path, digest in manifest_files.items()
            if path.startswith(f"{skill_name}/")
            and path != f"{skill_name}/bundle-lock.json"
        }
        if _valid_local_lock(lock, skill_name) != expected_lock:
            raise ArchiveError(f"installed lock contents are invalid: {skill_name}")
        if lock.get("bundle_version") != checked["bundle_version"]:
            raise ArchiveError(f"installed Bundle version is invalid: {skill_name}")
        if lock.get("skill_version") != checked["skills"][skill_name]:
            raise ArchiveError(f"installed Skill version is invalid: {skill_name}")

    for relative, expected_digest in manifest_files.items():
        path = skills_root.joinpath(*PurePosixPath(relative).parts)
        if path.is_symlink() or not path.is_file() or _sha256_file(path) != expected_digest:
            raise ArchiveError(f"installed file hash mismatch: {relative}")


def _write_transaction(path: Path, transaction: dict) -> None:
    save_state(path, transaction)


def _rollback_source_transaction(
    skills_root: Path,
    backup_root: Path,
    installed_names: set[str],
) -> None:
    for skill_name in installed_names:
        _remove_tree(skills_root / skill_name)
    for skill_name in SKILLS:
        backup_skill = backup_root / skill_name
        if backup_skill.is_dir():
            target = skills_root / skill_name
            _remove_tree(target)
            shutil.copytree(backup_skill, target, symlinks=True)


def _apply_source_transaction_locked(
    skills_root: Path,
    staged_root: Path,
    manifest: dict,
    state_root: Path,
    *,
    allow_local_changes: bool,
    install_missing: bool,
    fault_hook,
) -> dict:
    detect_installation_mode(skills_root, SKILLS)
    if staged_root.is_symlink() or not staged_root.is_dir():
        raise ArchiveError("staged bundle root is missing or unsafe")
    skills_resolved = skills_root.resolve()
    staged_resolved = staged_root.resolve()
    if skills_resolved == staged_resolved:
        raise ArchiveError("staging and installation roots must differ")
    if (
        staged_resolved == skills_resolved
        or staged_resolved.is_relative_to(skills_resolved)
        or skills_resolved.is_relative_to(staged_resolved)
    ):
        raise ArchiveError("staging and installation roots must not overlap")
    if os.stat(skills_root).st_dev != os.stat(staged_root).st_dev:
        raise ArchiveError("staging must be on the same filesystem as Skills")

    checked, _ = _checked_manifest_files(manifest)
    verify_staged_bundle(staged_root, checked)
    report = inspect_installation(skills_root, checked)
    has_local_changes = any(
        report[key] for key in ("modified", "deleted", "added")
    )
    has_missing_skills = bool(report["missing_skills"])
    if (has_local_changes and not allow_local_changes) or (
        has_missing_skills and not install_missing
    ):
        return {
            "status": "confirmation_required",
            "fatal": False,
            "report": report,
            "modification_report": report,
        }

    worker_path = _copy_worker_script(state_root)
    backup_root = state_root / "backups" / (
        time.strftime("%Y%m%dT%H%M%S", time.gmtime()) + f"-{time.time_ns()}"
    )
    backup_root.mkdir(parents=True, exist_ok=False)
    transaction_path = backup_root / "transaction.json"
    transaction = {
        "status": "started",
        "bundle_version": checked["bundle_version"],
        "skills": list(SKILLS),
        "skills_root": str(skills_root.resolve()),
        "staged_root": str(staged_root.resolve()),
        "worker": str(worker_path),
    }
    for skill_name in SKILLS:
        source = skills_root / skill_name
        if source.is_dir() and not source.is_symlink():
            shutil.copytree(source, backup_root / skill_name, symlinks=True)
    _write_transaction(transaction_path, transaction)

    installed_names: set[str] = set()
    try:
        for skill_name in SKILLS:
            target = skills_root / skill_name
            staged_skill = staged_root / skill_name
            _remove_tree(target)
            os.replace(staged_skill, target)
            installed_names.add(skill_name)
            if fault_hook is not None:
                fault_hook(skill_name)
        _verify_installed_bundle(skills_root, checked)
    except Exception as exc:
        try:
            _rollback_source_transaction(skills_root, backup_root, installed_names)
            transaction["status"] = "rolled_back"
            transaction["error"] = str(exc)
            _write_transaction(transaction_path, transaction)
            return {
                "status": "rolled_back",
                "fatal": False,
                "backup_path": str(backup_root),
                "message": str(exc),
                "report": report,
            }
        except Exception as rollback_error:
            transaction["status"] = "rollback_failed"
            transaction["error"] = str(exc)
            transaction["rollback_error"] = str(rollback_error)
            _write_transaction(transaction_path, transaction)
            return {
                "status": "rollback_failed",
                "fatal": True,
                "backup_path": str(backup_root),
                "message": str(rollback_error),
            }

    transaction["status"] = "updated"
    _write_transaction(transaction_path, transaction)
    return {
        "status": "updated",
        "fatal": False,
        "bundle_version": checked["bundle_version"],
        "backup_path": str(backup_root),
        "report": report,
    }


def apply_source_transaction(
    skills_root: Path,
    staged_root: Path,
    manifest: dict,
    state_root: Path,
    *,
    allow_local_changes: bool = False,
    install_missing: bool = False,
    fault_hook=None,
) -> dict:
    skills_root = Path(skills_root)
    staged_root = Path(staged_root)
    state_root = Path(state_root)
    try:
        if state_root.is_symlink():
            raise ArchiveError("state root is a symlink")
        state_root.mkdir(parents=True, exist_ok=True)
        with operation_lock(state_root / LOCK_FILE_NAME):
            return _apply_source_transaction_locked(
                skills_root,
                staged_root,
                manifest,
                state_root,
                allow_local_changes=allow_local_changes,
                install_missing=install_missing,
                fault_hook=fault_hook,
            )
    except LockBusyError:
        return {"status": "busy", "fatal": False}
    except ArchiveError as exc:
        return {"status": "rejected", "fatal": False, "message": str(exc)}
    except (OSError, ValueError) as exc:
        return {"status": "failed", "fatal": True, "message": str(exc)}


def get_state_root(
    env: Mapping[str, str] | None = None,
    platform_name: str | None = None,
) -> Path:
    values = os.environ if env is None else env
    platform_value = sys.platform if platform_name is None else platform_name
    if platform_value.startswith("win"):
        base = values.get("LOCALAPPDATA") or values.get("APPDATA")
        if base:
            return Path(base) / BUNDLE_ID
        return Path.home() / "AppData" / "Local" / BUNDLE_ID
    base = values.get("XDG_STATE_HOME") or str(Path(values.get("HOME", str(Path.home()))) / ".local" / "state")
    return Path(base) / BUNDLE_ID


def load_state(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def save_state(path: Path, state: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        dir=path.parent,
        prefix=f".{path.name}.",
        suffix=".tmp",
    )
    temporary_path = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
            json.dump(state, stream, ensure_ascii=False, sort_keys=True)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary_path, path)
    finally:
        with contextlib.suppress(FileNotFoundError):
            temporary_path.unlink()


@contextlib.contextmanager
def operation_lock(path: Path) -> ContextManager[None]:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a+b") as stream:
        stream.seek(0, os.SEEK_END)
        if stream.tell() == 0:
            stream.write(b"\0")
            stream.flush()
        stream.seek(0)
        if os.name == "nt":
            import msvcrt

            try:
                msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
            except OSError as exc:
                raise LockBusyError("another update operation is active") from exc
            try:
                yield
            finally:
                stream.seek(0)
                msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            import fcntl

            try:
                fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError as exc:
                raise LockBusyError("another update operation is active") from exc
            try:
                yield
            finally:
                fcntl.flock(stream.fileno(), fcntl.LOCK_UN)


def fetch_manifest(
    url: str,
    etag: str | None,
    timeout: float = NETWORK_TIMEOUT_SECONDS,
) -> FetchResult:
    headers = {"Accept": "application/json"}
    if etag:
        headers["If-None-Match"] = etag
    request = Request(url, headers=headers)
    try:
        with urlopen(request, timeout=timeout) as response:
            content = response.read().decode("utf-8")
            data = json.loads(content)
            return FetchResult(validate_manifest(data), response.headers.get("ETag"), False)
    except HTTPError as exc:
        if exc.code == 304:
            return FetchResult(None, etag, True)
        raise


def _read_current_version(skill_dir: Path) -> str:
    path = skill_dir / "bundle-lock.json"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return str(data["bundle_version"])
    except (OSError, json.JSONDecodeError, KeyError, TypeError) as exc:
        raise ValueError(f"invalid bundle lock: {path}") from exc


def _aggregate_history(*sources: object) -> list[dict]:
    entries: dict[str, dict] = {}
    for source in sources:
        if isinstance(source, dict):
            source = source.get("history", [])
        if not isinstance(source, list):
            continue
        for entry in source:
            if isinstance(entry, dict) and isinstance(entry.get("bundle_version"), str):
                entries[entry["bundle_version"]] = dict(entry)
    return [entries[version] for version in sorted(entries, key=parse_semver)]


def _status_for_manifest(
    current_version: str,
    manifest: dict,
    state: dict,
    now: float,
    history: list[dict],
) -> dict:
    latest_version = str(manifest["bundle_version"])
    result = {
        "fatal": False,
        "current_version": current_version,
        "latest_version": latest_version,
        "manifest": manifest,
        "history": history,
    }
    if parse_semver(latest_version) <= parse_semver(current_version):
        return {"status": "up_to_date", **result}
    if state.get("ignored_version") == latest_version:
        return {"status": "ignored", **result}
    if isinstance(state.get("snooze_until"), (int, float)) and state["snooze_until"] > now:
        return {"status": "snoozed", **result}
    return {"status": "update_available", **result}


def _state_paths() -> tuple[Path, Path]:
    root = get_state_root()
    return root / STATE_FILE_NAME, root / LOCK_FILE_NAME


def _record_nonfatal_attempt(
    state_path: Path,
    state: dict,
    checked_at: float,
    status: str,
    current_version: str,
    message: str,
) -> dict:
    state["last_network_check"] = checked_at
    state["last_nonfatal_status"] = status
    state["last_nonfatal_message"] = message
    save_state(state_path, state)
    return {
        "status": status,
        "fatal": False,
        "current_version": current_version,
        "message": message,
    }


def check_for_update(
    skill_dir: Path,
    *,
    force: bool = False,
    now: float | None = None,
    fetcher=fetch_manifest,
) -> dict:
    checked_at = time.time() if now is None else now
    try:
        current_version = _read_current_version(skill_dir)
        parse_semver(current_version)
    except ValueError as exc:
        return {"status": "invalid_manifest", "fatal": False, "message": str(exc)}

    state_path, lock_path = _state_paths()
    try:
        with operation_lock(lock_path):
            state = load_state(state_path)
            cached_manifest = state.get("cached_manifest")
            last_check = state.get("last_network_check")
            last_nonfatal_status = state.get("last_nonfatal_status")
            failed_attempt_fresh = (
                not force
                and isinstance(last_check, (int, float))
                and checked_at - last_check < CHECK_INTERVAL_SECONDS
                and last_nonfatal_status in {"offline", "invalid_manifest"}
            )
            if failed_attempt_fresh:
                result = {
                    "status": last_nonfatal_status,
                    "fatal": False,
                    "current_version": current_version,
                }
                if isinstance(state.get("last_nonfatal_message"), str):
                    result["message"] = state["last_nonfatal_message"]
                return result
            cache_fresh = (
                isinstance(last_check, (int, float))
                and checked_at - last_check < CHECK_INTERVAL_SECONDS
                and isinstance(cached_manifest, dict)
            )
            snoozed = (
                not force
                and isinstance(state.get("snooze_until"), (int, float))
                and state["snooze_until"] > checked_at
            )
            if (cache_fresh and not force) or snoozed:
                if isinstance(cached_manifest, dict):
                    try:
                        manifest = validate_manifest(cached_manifest)
                        history = _aggregate_history(state.get("history"), manifest)
                        result = _status_for_manifest(
                            current_version, manifest, state, checked_at, history
                        )
                        if result["status"] == "up_to_date":
                            result["status"] = "cached"
                        return result
                    except ValueError:
                        pass
                return {"status": "cached", "fatal": False, "current_version": current_version}

            etag = state.get("etag") if isinstance(state.get("etag"), str) else None
            try:
                fetched = fetcher(MANIFEST_URL, etag, NETWORK_TIMEOUT_SECONDS)
            except (OSError, URLError, HTTPError, TimeoutError) as exc:
                return _record_nonfatal_attempt(
                    state_path, state, checked_at, "offline", current_version, str(exc)
                )
            except ValueError as exc:
                return _record_nonfatal_attempt(
                    state_path,
                    state,
                    checked_at,
                    "invalid_manifest",
                    current_version,
                    str(exc),
                )
            if not isinstance(fetched, FetchResult):
                message = "manifest fetcher returned an invalid result"
                return _record_nonfatal_attempt(
                    state_path,
                    state,
                    checked_at,
                    "invalid_manifest",
                    current_version,
                    message,
                )
            try:
                if fetched.not_modified:
                    if not isinstance(cached_manifest, dict):
                        raise ValueError(
                            "server returned not-modified without a cached manifest"
                        )
                    manifest = validate_manifest(cached_manifest)
                elif fetched.manifest is None:
                    raise ValueError("manifest response was empty")
                else:
                    manifest = validate_manifest(fetched.manifest)
                history = _aggregate_history(
                    state.get("history"), cached_manifest, manifest
                )
            except ValueError as exc:
                return _record_nonfatal_attempt(
                    state_path,
                    state,
                    checked_at,
                    "invalid_manifest",
                    current_version,
                    str(exc),
                )
            state["last_network_check"] = checked_at
            state.pop("last_nonfatal_status", None)
            state.pop("last_nonfatal_message", None)
            state["cached_manifest"] = manifest
            state["history"] = history
            state["etag"] = fetched.etag or etag
            save_state(state_path, state)
            return _status_for_manifest(current_version, manifest, state, checked_at, history)
    except LockBusyError:
        return {"status": "busy", "fatal": False, "current_version": current_version}
    except ValueError as exc:
        return {
            "status": "invalid_manifest",
            "fatal": False,
            "current_version": current_version,
            "message": str(exc),
        }


def snooze(
    skill_dir: Path,
    hours: float = DEFAULT_SNOOZE_SECONDS / 60 / 60,
    now: float | None = None,
) -> dict:
    if hours <= 0:
        raise ValueError("snooze hours must be positive")
    timestamp = time.time() if now is None else now
    state_path, lock_path = _state_paths()
    with operation_lock(lock_path):
        state = load_state(state_path)
        state["snooze_until"] = timestamp + hours * 60 * 60
        save_state(state_path, state)
    return {"status": "snoozed", "fatal": False, "snooze_until": state["snooze_until"]}


def ignore(skill_dir: Path, version: str) -> dict:
    parse_semver(version)
    state_path, lock_path = _state_paths()
    with operation_lock(lock_path):
        state = load_state(state_path)
        state["ignored_version"] = version
        save_state(state_path, state)
    return {"status": "ignored", "fatal": False, "ignored_version": version}


def details(skill_dir: Path) -> dict:
    state_path, lock_path = _state_paths()
    try:
        current_version = _read_current_version(skill_dir)
    except ValueError:
        current_version = None
    with operation_lock(lock_path):
        state = load_state(state_path)
    manifest = state.get("cached_manifest") if isinstance(state.get("cached_manifest"), dict) else None
    return {
        "status": "details",
        "fatal": False,
        "current_version": current_version,
        "cached_manifest": manifest,
        "history": _aggregate_history(state.get("history"), manifest),
        "snooze_until": state.get("snooze_until"),
        "ignored_version": state.get("ignored_version"),
    }


def _load_manifest_path(manifest_path: Path, state_root: Path) -> dict:
    path = Path(manifest_path)
    if not path.exists():
        state = load_state(state_root / STATE_FILE_NAME)
        cached = state.get("cached_manifest")
        if isinstance(cached, dict):
            return validate_manifest(cached)
        raise ValueError(f"cached manifest does not exist: {path}")
    try:
        return validate_manifest(json.loads(path.read_text(encoding="utf-8")))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        raise ValueError(f"invalid cached manifest: {path}") from exc


def _cli_paths(args) -> tuple[Path, Path, Path, Path]:
    state_root = Path(args.state_root) if args.state_root else get_state_root()
    skills_root = (
        Path(args.skills_root) if args.skills_root else _skill_dir().parent
    )
    if not args.staged_root:
        raise ValueError("--staged-root is required")
    staged_root = Path(args.staged_root)
    manifest_path = (
        Path(args.manifest_path)
        if args.manifest_path
        else state_root / STATE_FILE_NAME
    )
    return skills_root, staged_root, manifest_path, state_root


def _diff_result(
    skills_root: Path,
    staged_root: Path,
    manifest: dict,
) -> dict:
    report = inspect_installation(skills_root, manifest)
    changed = set(manifest["files"])
    changed.update(report["modified"])
    changed.update(report["deleted"])
    changed.update(report["added"])
    return {
        "status": report["status"],
        "fatal": False,
        "report": report,
        "modification_report": report,
        "diff": format_incoming_diff(skills_root, staged_root, sorted(changed)),
    }


def _run_source_worker(
    worker_path: Path,
    skills_root: Path,
    staged_root: Path,
    manifest_path: Path,
    state_root: Path,
    *,
    allow_local_changes: bool,
    install_missing: bool,
) -> dict:
    command = [
        sys.executable,
        "-X",
        "utf8",
        str(worker_path),
        "worker-apply",
        "--skills-root",
        str(skills_root.resolve()),
        "--staged-root",
        str(staged_root.resolve()),
        "--manifest",
        str(manifest_path.resolve()),
        "--state-root",
        str(state_root.resolve()),
        "--json",
    ]
    if allow_local_changes:
        command.append("--allow-local-changes")
    if install_missing:
        command.append("--install-missing")
    completed = subprocess.run(
        command,
        cwd=str(state_root.resolve()),
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    output = completed.stdout.strip().splitlines()
    if output:
        try:
            return json.loads(output[-1])
        except json.JSONDecodeError:
            pass
    return {
        "status": "failed",
        "fatal": True,
        "message": completed.stderr.strip() or "source worker returned invalid output",
    }


def _skill_dir() -> Path:
    return Path(__file__).resolve().parents[1]


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Check for legal Skill bundle updates.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    check = subparsers.add_parser("check")
    check.add_argument("--force", action="store_true")
    check.add_argument("--json", action="store_true")
    snooze_parser = subparsers.add_parser("snooze")
    snooze_parser.add_argument(
        "--hours", type=float, default=DEFAULT_SNOOZE_SECONDS / 60 / 60
    )
    snooze_parser.add_argument("--json", action="store_true")
    ignore_parser = subparsers.add_parser("ignore")
    ignore_parser.add_argument("version")
    ignore_parser.add_argument("--json", action="store_true")
    details_parser = subparsers.add_parser("details")
    details_parser.add_argument("--json", action="store_true")

    def add_transaction_paths(command):
        command.add_argument("--skills-root", type=Path)
        command.add_argument("--staged-root", "--staged", dest="staged_root", type=Path)
        command.add_argument(
            "--manifest", "--manifest-path", dest="manifest_path", type=Path
        )
        command.add_argument("--state-root", type=Path)

    diff = subparsers.add_parser("diff")
    add_transaction_paths(diff)
    diff.add_argument("--json", action="store_true")
    apply = subparsers.add_parser("apply")
    add_transaction_paths(apply)
    apply.add_argument("--allow-local-changes", action="store_true")
    apply.add_argument("--install-missing", action="store_true")
    apply.add_argument("--json", action="store_true")
    worker = subparsers.add_parser("worker-apply", help=argparse.SUPPRESS)
    add_transaction_paths(worker)
    worker.add_argument("--allow-local-changes", action="store_true")
    worker.add_argument("--install-missing", action="store_true")
    worker.add_argument("--json", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    try:
        if args.command == "check":
            result = check_for_update(_skill_dir(), force=args.force)
        elif args.command == "snooze":
            result = snooze(_skill_dir(), args.hours)
        elif args.command == "ignore":
            result = ignore(_skill_dir(), args.version)
        elif args.command == "diff":
            skills_root, staged_root, manifest_path, state_root = _cli_paths(args)
            result = _diff_result(
                skills_root,
                staged_root,
                _load_manifest_path(manifest_path, state_root),
            )
        elif args.command == "apply":
            skills_root, staged_root, manifest_path, state_root = _cli_paths(args)
            manifest = _load_manifest_path(manifest_path, state_root)
            detect_installation_mode(skills_root, SKILLS)
            report = inspect_installation(skills_root, manifest)
            if (
                not args.allow_local_changes
                or (report["missing_skills"] and not args.install_missing)
            ):
                result = {
                    "status": "confirmation_required",
                    "fatal": False,
                    "report": report,
                    "modification_report": report,
                }
            else:
                worker_path = _copy_worker_script(state_root)
                result = _run_source_worker(
                    worker_path,
                    skills_root,
                    staged_root,
                    manifest_path,
                    state_root,
                    allow_local_changes=args.allow_local_changes,
                    install_missing=args.install_missing,
                )
        elif args.command == "worker-apply":
            skills_root, staged_root, manifest_path, state_root = _cli_paths(args)
            result = apply_source_transaction(
                skills_root,
                staged_root,
                _load_manifest_path(manifest_path, state_root),
                state_root,
                allow_local_changes=args.allow_local_changes,
                install_missing=args.install_missing,
            )
        else:
            result = details(_skill_dir())
    except ArchiveError as exc:
        result = {"status": "rejected", "fatal": False, "message": str(exc)}
    except (LockBusyError, OSError, ValueError) as exc:
        result = {"status": "invalid_input", "fatal": False, "message": str(exc)}
    if args.json:
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    else:
        print(result["status"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
