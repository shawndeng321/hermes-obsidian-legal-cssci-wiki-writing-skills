from __future__ import annotations

import argparse
import contextlib
import json
import os
import re
import sys
import tempfile
import time
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import ContextManager
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen


CHECK_INTERVAL_SECONDS = 6 * 60 * 60
DEFAULT_SNOOZE_SECONDS = 4 * 60 * 60
NETWORK_TIMEOUT_SECONDS = 3.0
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


class LockBusyError(RuntimeError):
    """Raised when another updater process holds the operation lock."""


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

    parsed_url = urlparse(data["archive_url"])
    if (
        not isinstance(data["archive_url"], str)
        or parsed_url.scheme != "https"
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
                return {
                    "status": "offline",
                    "fatal": False,
                    "current_version": current_version,
                    "message": str(exc),
                }
            if not isinstance(fetched, FetchResult):
                return {
                    "status": "invalid_manifest",
                    "fatal": False,
                    "current_version": current_version,
                    "message": "manifest fetcher returned an invalid result",
                }
            if fetched.not_modified:
                if not isinstance(cached_manifest, dict):
                    return {
                        "status": "invalid_manifest",
                        "fatal": False,
                        "current_version": current_version,
                        "message": "server returned not-modified without a cached manifest",
                    }
                manifest = validate_manifest(cached_manifest)
            elif fetched.manifest is None:
                return {
                    "status": "invalid_manifest",
                    "fatal": False,
                    "current_version": current_version,
                    "message": "manifest response was empty",
                }
            else:
                manifest = validate_manifest(fetched.manifest)

            history = _aggregate_history(state.get("history"), cached_manifest, manifest)
            state["last_network_check"] = checked_at
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
        else:
            result = details(_skill_dir())
    except (LockBusyError, ValueError) as exc:
        result = {"status": "invalid_input", "fatal": False, "message": str(exc)}
    if args.json:
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    else:
        print(result["status"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
