from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
PREPARE = ROOT / "tools" / "prepare_bundle_release.py"
UPDATER = ROOT / "chinese-law-paper-writing" / "scripts" / "legal_skills_update.py"
SKILLS = (
    "chinese-law-paper-writing",
    "legal-research-wiki",
    "legal-wiki-audit-repair",
)


def make_manifest(version: str, history: list[dict] | None = None) -> dict:
    return {
        "schema_version": 1,
        "bundle_id": "hermes-legal-research-skills",
        "bundle_version": version,
        "published_at": "2026-08-10T00:00:00+08:00",
        "update_level": "feature",
        "summary": f"Bundle {version}",
        "skills": {
            "chinese-law-paper-writing": "5.1.0",
            "legal-research-wiki": "4.1.0",
            "legal-wiki-audit-repair": "4.2.0",
        },
        "compatibility": {"hermes": True, "codex": True, "python": ">=3.11"},
        "changes": [f"Change {version}"],
        "archive_url": (
            "https://github.com/shawndeng321/"
            "hermes-obsidian-legal-cssci-wiki-writing-skills/"
            "archive/refs/heads/main.zip"
        ),
        "files": {
            "chinese-law-paper-writing/SKILL.md": "a" * 64,
            "chinese-law-paper-writing/agents/openai.yaml": "b" * 64,
            "legal-research-wiki/SKILL.md": "c" * 64,
            "legal-research-wiki/agents/openai.yaml": "d" * 64,
            "legal-wiki-audit-repair/SKILL.md": "e" * 64,
            "legal-wiki-audit-repair/agents/openai.yaml": "f" * 64,
        },
        "history": history if history is not None else [
            {
                "bundle_version": version,
                "published_at": "2026-08-10T00:00:00+08:00",
                "update_level": "feature",
                "summary": f"Bundle {version}",
                "changes": [f"Change {version}"],
            }
        ],
    }


@contextmanager
def updater_fixture(
    state: dict | None = None,
    last_check: float | None = None,
):
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        skill_dir = root / "chinese-law-paper-writing"
        skill_dir.mkdir()
        (skill_dir / "bundle-lock.json").write_text(
            json.dumps({"bundle_version": "1.0.0"}), encoding="utf-8"
        )
        state_base = root / "state-base"
        state_root = state_base / "hermes-legal-research-skills"
        state_root.mkdir(parents=True)
        initial = dict(state or {})
        if last_check is not None:
            initial["last_network_check"] = last_check
        if initial:
            (state_root / "state.json").write_text(
                json.dumps(initial), encoding="utf-8"
            )
        with patch.dict(os.environ, {"LOCALAPPDATA": str(state_base)}, clear=False):
            yield SimpleNamespace(
                root=root,
                skill_dir=skill_dir,
                state_root=state_root,
                state_path=state_root / "state.json",
            )


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def write_skill(root: Path, name: str, version: str) -> Path:
    skill = root / name
    (skill / "agents").mkdir(parents=True)
    (skill / "SKILL.md").write_text(
        "---\n"
        f'name: "{name}"\n'
        'description: "Use when updating a legal skill bundle."\n'
        'license: "MIT"\n'
        "metadata:\n"
        f'  version: "{version}"\n'
        "---\n\n"
        "# Demo\n",
        encoding="utf-8",
    )
    (skill / "agents" / "openai.yaml").write_text(
        "interface:\n"
        f'  display_name: "{name}"\n'
        '  short_description: "demo skill"\n'
        f'  default_prompt: "Use ${name} to update."\n',
        encoding="utf-8",
    )
    return skill


def prepare_temporary_repository(root: Path) -> None:
    tool = root / "tools" / "prepare_bundle_release.py"
    tool.parent.mkdir(parents=True)
    shutil.copy2(PREPARE, tool)
    for skill_name, version in zip(SKILLS, ("5.1.0", "4.1.0", "4.2.0")):
        write_skill(root, skill_name, version)


def run_prepare(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    tool = root / "tools" / "prepare_bundle_release.py"
    return subprocess.run(
        [sys.executable, "-X", "utf8", str(tool), *args],
        cwd=root,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )


def write_release(root: Path) -> subprocess.CompletedProcess[str]:
    return run_prepare(
        root,
        "--write",
        "--bundle-version",
        "1.0.0",
        "--published-at",
        "2026-08-10T00:00:00+08:00",
        "--update-level",
        "feature",
        "--summary",
        "增加按需更新检查、统一备份和回滚",
        "--change",
        "增加每6小时一次的按需更新检查",
    )


class ReleaseContractTests(unittest.TestCase):
    def test_cli_write_and_check_succeeds(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            prepare_temporary_repository(root)

            written = write_release(root)

            self.assertEqual(written.returncode, 0, written.stderr)
            self.assertTrue((root / "bundle-release.json").is_file())
            for skill_name in SKILLS:
                self.assertTrue((root / skill_name / "bundle-lock.json").is_file())

            checked = run_prepare(root, "--check")

            self.assertEqual(checked.returncode, 0, checked.stderr)
            self.assertIn("Bundle 1.0.0 is consistent", checked.stdout)

    def test_cli_check_rejects_tampered_lock_even_when_manifest_hash_matches(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            prepare_temporary_repository(root)
            written = write_release(root)
            self.assertEqual(written.returncode, 0, written.stderr)

            skill_name = SKILLS[0]
            lock_path = root / skill_name / "bundle-lock.json"
            lock = json.loads(lock_path.read_text(encoding="utf-8"))
            lock["bundle_version"] = "9.9.9"
            lock_path.write_text(
                json.dumps(lock, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )

            manifest_path = root / "bundle-release.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["files"][f"{skill_name}/bundle-lock.json"] = hashlib.sha256(
                lock_path.read_bytes()
            ).hexdigest()
            manifest_path.write_text(
                json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )

            checked = run_prepare(root, "--check")

            self.assertNotEqual(checked.returncode, 0)
            self.assertIn("bundle-lock.json", checked.stderr)

    def test_collect_skill_files_is_stable_and_excludes_lock_and_cache(self):
        module = load_module(PREPARE, "prepare_bundle_release_collect")
        with tempfile.TemporaryDirectory() as tmp:
            skill = Path(tmp) / "demo"
            (skill / "scripts" / "__pycache__").mkdir(parents=True)
            (skill / "SKILL.md").write_text("demo", encoding="utf-8")
            (skill / "bundle-lock.json").write_text("{}", encoding="utf-8")
            (skill / "scripts" / "tool.py").write_text("print(1)\n", encoding="utf-8")
            (skill / "scripts" / "__pycache__" / "tool.pyc").write_bytes(b"cache")

            files = module.collect_skill_files(skill)

            self.assertEqual(set(files), {"SKILL.md", "scripts/tool.py"})
            self.assertRegex(files["SKILL.md"], r"^[0-9a-f]{64}$")

    def test_read_skill_version_reads_metadata_version(self):
        module = load_module(PREPARE, "prepare_bundle_release_version")
        with tempfile.TemporaryDirectory() as tmp:
            skill = write_skill(Path(tmp), "demo-skill", "2.3.4")

            version = module.read_skill_version(skill)

            self.assertEqual(version, "2.3.4")

    def test_build_lock_uses_exact_contract(self):
        module = load_module(PREPARE, "prepare_bundle_lock")
        lock = module.build_lock("demo-skill", "2.3.4", "1.0.0", {"SKILL.md": "a" * 64})
        self.assertEqual(lock, {
            "schema_version": 1,
            "bundle_id": "hermes-legal-research-skills",
            "bundle_version": "1.0.0",
            "skill_name": "demo-skill",
            "skill_version": "2.3.4",
            "files": {"SKILL.md": "a" * 64},
        })

    def test_build_manifest_replaces_existing_history_entry(self):
        module = load_module(PREPARE, "prepare_bundle_manifest")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for skill_name, version in zip(SKILLS, ("5.1.0", "4.1.0", "4.2.0")):
                write_skill(root, skill_name, version)

            first_release = {
                "bundle_version": "1.0.0",
                "published_at": "2026-08-10T00:00:00+08:00",
                "update_level": "feature",
                "summary": "旧说明",
                "changes": ["旧说明"],
                "archive_url": (
                    "https://github.com/shawndeng321/"
                    "hermes-obsidian-legal-cssci-wiki-writing-skills/"
                    "archive/refs/heads/main.zip"
                ),
            }
            first_manifest = module.build_manifest(root, first_release)
            (root / "bundle-release.json").write_text(
                json.dumps(first_manifest, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

            second_release = {
                "bundle_version": "1.0.0",
                "published_at": "2026-08-10T00:00:00+08:00",
                "update_level": "feature",
                "summary": "增加按需更新检查、统一备份和回滚",
                "changes": [
                    "增加每6小时一次的按需更新检查",
                    "增加三个Skill统一备份、校验、更新和失败回滚",
                    "增加本地修改检测、稍后提醒和忽略当前版本",
                ],
                "archive_url": (
                    "https://github.com/shawndeng321/"
                    "hermes-obsidian-legal-cssci-wiki-writing-skills/"
                    "archive/refs/heads/main.zip"
                ),
            }

            manifest = module.build_manifest(root, second_release)

            self.assertEqual(len(manifest["history"]), 1)
            self.assertEqual(manifest["history"][0]["bundle_version"], "1.0.0")
            self.assertEqual(
                manifest["history"][0]["changes"],
                [
                    "增加每6小时一次的按需更新检查",
                    "增加三个Skill统一备份、校验、更新和失败回滚",
                    "增加本地修改检测、稍后提醒和忽略当前版本",
                ],
            )

    def test_build_manifest_rejects_missing_metadata_and_invalid_archive_url(self):
        module = load_module(PREPARE, "prepare_bundle_validation")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_skill(root, "chinese-law-paper-writing", "5.1.0")
            write_skill(root, "legal-research-wiki", "4.1.0")
            broken = write_skill(root, "legal-wiki-audit-repair", "4.2.0")
            (broken / "SKILL.md").unlink()

            release = {
                "bundle_version": "1.0.0",
                "published_at": "2026-08-10T00:00:00+08:00",
                "update_level": "feature",
                "summary": "增加按需更新检查、统一备份和回滚",
                "changes": ["增加每6小时一次的按需更新检查"],
                "archive_url": (
                    "https://github.com/shawndeng321/"
                    "hermes-obsidian-legal-cssci-wiki-writing-skills/"
                    "archive/refs/heads/main.zip"
                ),
            }

            with self.assertRaises(ValueError):
                module.build_manifest(root, release)

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for skill_name, version in zip(SKILLS, ("5.1.0", "4.1.0", "4.2.0")):
                write_skill(root, skill_name, version)

            release = {
                "bundle_version": "1.0.0",
                "published_at": "2026-08-10T00:00:00+08:00",
                "update_level": "feature",
                "summary": "增加按需更新检查、统一备份和回滚",
                "changes": ["增加每6小时一次的按需更新检查"],
                "archive_url": "http://example.com/archive.zip",
            }

            with self.assertRaises(ValueError):
                module.build_manifest(root, release)


class UpdateCheckTests(unittest.TestCase):
    def test_fresh_cache_avoids_network_for_six_hours(self):
        module = load_module(UPDATER, "legal_skills_update")
        calls = []
        state = {
            "last_network_check": 1_000.0,
            "cached_manifest": make_manifest("1.0.0"),
            "etag": '"abc"',
        }
        with updater_fixture(state=state) as fixture:
            result = module.check_for_update(
                fixture.skill_dir,
                now=1_000.0 + 21_599,
                fetcher=lambda *args: calls.append(args),
            )
        self.assertEqual(result["status"], "cached")
        self.assertEqual(calls, [])

    def test_six_hour_boundary_fetches_and_finds_newer_version(self):
        module = load_module(UPDATER, "legal_skills_update_boundary")
        with updater_fixture(last_check=1_000.0) as fixture:
            result = module.check_for_update(
                fixture.skill_dir,
                now=1_000.0 + 21_600,
                fetcher=lambda *_: module.FetchResult(make_manifest("1.1.0"), '"new"', False),
            )
        self.assertEqual(result["status"], "update_available")
        self.assertEqual(result["current_version"], "1.0.0")
        self.assertEqual(result["latest_version"], "1.1.0")

    def test_force_bypasses_a_fresh_cache(self):
        module = load_module(UPDATER, "legal_skills_update_force")
        calls = []
        state = {
            "last_network_check": 1_000.0,
            "cached_manifest": make_manifest("1.0.0"),
        }
        with updater_fixture(state=state) as fixture:
            result = module.check_for_update(
                fixture.skill_dir,
                force=True,
                now=1_001.0,
                fetcher=lambda *args: (
                    calls.append(args),
                    module.FetchResult(make_manifest("1.1.0"), '"new"', False),
                )[1],
            )
        self.assertEqual(result["status"], "update_available")
        self.assertEqual(len(calls), 1)

    def test_not_modified_reuses_cached_manifest(self):
        module = load_module(UPDATER, "legal_skills_update_not_modified")
        state = {
            "last_network_check": 1_000.0,
            "cached_manifest": make_manifest("1.1.0"),
            "etag": '"old"',
        }
        with updater_fixture(state=state) as fixture:
            result = module.check_for_update(
                fixture.skill_dir,
                now=1_000.0 + 21_600,
                fetcher=lambda *_: module.FetchResult(None, '"old"', True),
            )
            saved = json.loads(fixture.state_path.read_text(encoding="utf-8"))
        self.assertEqual(result["status"], "update_available")
        self.assertEqual(result["latest_version"], "1.1.0")
        self.assertEqual(saved["last_network_check"], 22_600.0)
        self.assertEqual(saved["etag"], '"old"')

    def test_offline_is_not_reported_as_up_to_date(self):
        module = load_module(UPDATER, "legal_skills_update_offline")
        with updater_fixture() as fixture:
            result = module.check_for_update(
                fixture.skill_dir,
                now=1_000.0,
                fetcher=lambda *_: (_ for _ in ()).throw(OSError("offline")),
            )
        self.assertEqual(result["status"], "offline")
        self.assertFalse(result["fatal"])
        self.assertNotEqual(result["status"], "up_to_date")

    def test_save_state_replaces_a_complete_sibling_file_atomically(self):
        module = load_module(UPDATER, "legal_skills_update_atomic_state")
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "state.json"
            module.save_state(path, {"etag": '"new"', "last_network_check": 123.0})
            self.assertEqual(
                json.loads(path.read_text(encoding="utf-8")),
                {"etag": '"new"', "last_network_check": 123.0},
            )
            self.assertEqual(list(Path(tmp).glob("*.tmp")), [])

    def test_state_root_uses_local_app_data_on_windows_and_xdg_on_posix(self):
        module = load_module(UPDATER, "legal_skills_update_state_roots")
        self.assertEqual(
            module.get_state_root(
                {"LOCALAPPDATA": r"C:\\Users\\Ada\\AppData\\Local"}, "win32"
            ),
            Path(r"C:\\Users\\Ada\\AppData\\Local") / "hermes-legal-research-skills",
        )
        self.assertEqual(
            module.get_state_root({"XDG_STATE_HOME": "/var/state", "HOME": "/home/ada"}, "linux"),
            Path("/var/state/hermes-legal-research-skills"),
        )
        self.assertEqual(
            module.get_state_root({"HOME": "/home/ada"}, "darwin"),
            Path("/home/ada/.local/state/hermes-legal-research-skills"),
        )

    def test_expired_snooze_allows_a_new_update_notice(self):
        module = load_module(UPDATER, "legal_skills_update_snooze_expiry")
        with updater_fixture(state={"snooze_until": 999.0}) as fixture:
            result = module.check_for_update(
                fixture.skill_dir,
                now=1_000.0,
                fetcher=lambda *_: module.FetchResult(make_manifest("1.1.0"), '"new"', False),
            )
        self.assertEqual(result["status"], "update_available")

    def test_ignored_current_version_suppresses_the_notice(self):
        module = load_module(UPDATER, "legal_skills_update_ignore")
        with updater_fixture(state={"ignored_version": "1.1.0"}) as fixture:
            result = module.check_for_update(
                fixture.skill_dir,
                now=1_000.0,
                fetcher=lambda *_: module.FetchResult(make_manifest("1.1.0"), '"new"', False),
            )
        self.assertEqual(result["status"], "ignored")

    def test_higher_version_after_ignored_version_is_announced(self):
        module = load_module(UPDATER, "legal_skills_update_higher_version")
        with updater_fixture(state={"ignored_version": "1.1.0"}) as fixture:
            result = module.check_for_update(
                fixture.skill_dir,
                now=1_000.0,
                fetcher=lambda *_: module.FetchResult(make_manifest("1.2.0"), '"new"', False),
            )
        self.assertEqual(result["status"], "update_available")
        self.assertEqual(result["latest_version"], "1.2.0")

    def test_history_aggregates_cached_and_new_bundle_versions(self):
        module = load_module(UPDATER, "legal_skills_update_history")
        cached = make_manifest("1.0.0")
        incoming = make_manifest(
            "1.1.0",
            history=[
                {
                    "bundle_version": "0.9.0",
                    "published_at": "2026-08-01T00:00:00+08:00",
                    "update_level": "feature",
                    "summary": "Bundle 0.9.0",
                    "changes": ["Change 0.9.0"],
                },
                *cached["history"],
                {
                    "bundle_version": "1.1.0",
                    "published_at": "2026-08-10T00:00:00+08:00",
                    "update_level": "feature",
                    "summary": "Bundle 1.1.0",
                    "changes": ["Change 1.1.0"],
                },
            ],
        )
        with updater_fixture(state={"cached_manifest": cached}) as fixture:
            result = module.check_for_update(
                fixture.skill_dir,
                now=1_000.0,
                fetcher=lambda *_: module.FetchResult(incoming, '"new"', False),
            )
            details = module.details(fixture.skill_dir)
        self.assertEqual(
            [entry["bundle_version"] for entry in result["history"]],
            ["0.9.0", "1.0.0", "1.1.0"],
        )
        self.assertEqual(details["history"], result["history"])

    def test_cli_state_actions_emit_json_without_touching_skill_directory(self):
        with updater_fixture() as fixture:
            before = sorted(path.relative_to(fixture.skill_dir) for path in fixture.skill_dir.rglob("*"))
            base_command = [sys.executable, "-X", "utf8", str(UPDATER)]
            env = dict(os.environ)
            env["LOCALAPPDATA"] = str(fixture.root / "state-base")
            snoozed = subprocess.run(
                [*base_command, "snooze", "--hours", "2", "--json"],
                capture_output=True,
                text=True,
                encoding="utf-8",
                cwd=fixture.skill_dir,
                env=env,
                check=False,
            )
            ignored = subprocess.run(
                [*base_command, "ignore", "1.1.0", "--json"],
                capture_output=True,
                text=True,
                encoding="utf-8",
                cwd=fixture.skill_dir,
                env=env,
                check=False,
            )
            detailed = subprocess.run(
                [*base_command, "details", "--json"],
                capture_output=True,
                text=True,
                encoding="utf-8",
                cwd=fixture.skill_dir,
                env=env,
                check=False,
            )
            after = sorted(path.relative_to(fixture.skill_dir) for path in fixture.skill_dir.rglob("*"))
        self.assertEqual(snoozed.returncode, 0, snoozed.stderr)
        self.assertEqual(ignored.returncode, 0, ignored.stderr)
        self.assertEqual(detailed.returncode, 0, detailed.stderr)
        self.assertIn("snooze_until", json.loads(snoozed.stdout))
        self.assertEqual(json.loads(ignored.stdout)["ignored_version"], "1.1.0")
        self.assertIn("history", json.loads(detailed.stdout))
        self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
