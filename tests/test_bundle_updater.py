from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PREPARE = ROOT / "tools" / "prepare_bundle_release.py"
SKILLS = (
    "chinese-law-paper-writing",
    "legal-research-wiki",
    "legal-wiki-audit-repair",
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


class ReleaseContractTests(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
