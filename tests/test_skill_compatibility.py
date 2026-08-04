from __future__ import annotations

import re
import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
SKILLS = (
    "chinese-law-paper-writing",
    "legal-research-wiki",
    "legal-wiki-audit-repair",
)
ALLOWED_FRONTMATTER_KEYS = {"name", "description", "license", "metadata"}
EXPECTED_DESCRIPTIONS = {
    "chinese-law-paper-writing":
        "Use when planning, writing or checking Chinese legal papers.",
    "legal-research-wiki":
        "Use when building a Chinese legal research wiki.",
    "legal-wiki-audit-repair":
        "Use when auditing or repairing a legal research wiki.",
}


def load_yaml(path: Path) -> dict:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise AssertionError(f"{path} must contain a YAML mapping")
    return data


def load_skill(path: Path) -> tuple[dict, str]:
    content = path.read_text(encoding="utf-8")
    match = re.match(r"\A---\r?\n(.*?)\r?\n---\r?\n", content, re.DOTALL)
    if not match:
        raise AssertionError(f"{path} has invalid frontmatter fences")
    frontmatter = yaml.safe_load(match.group(1))
    if not isinstance(frontmatter, dict):
        raise AssertionError(f"{path} frontmatter must be a mapping")
    return frontmatter, content[match.end():]


class SkillCompatibilityTests(unittest.TestCase):
    def test_common_frontmatter_contract(self) -> None:
        for skill_name in SKILLS:
            with self.subTest(skill=skill_name):
                skill_path = ROOT / skill_name / "SKILL.md"
                frontmatter, body = load_skill(skill_path)
                self.assertEqual(frontmatter["name"], skill_name)
                self.assertEqual(
                    set(frontmatter) - ALLOWED_FRONTMATTER_KEYS,
                    set(),
                )
                self.assertEqual(
                    frontmatter["description"],
                    EXPECTED_DESCRIPTIONS[skill_name],
                )
                self.assertLessEqual(len(frontmatter["description"]), 60)
                self.assertTrue(frontmatter["description"].startswith("Use when"))
                self.assertTrue(frontmatter["description"].endswith("."))
                self.assertEqual(frontmatter["license"], "MIT")
                metadata = frontmatter["metadata"]
                self.assertIsInstance(metadata, dict)
                self.assertRegex(str(metadata["version"]), r"^\d+\.\d+\.\d+$")
                if "hermes" in metadata:
                    self.assertIsInstance(metadata["hermes"], dict)
                self.assertTrue(body.strip())
                self.assertLessEqual(
                    len(skill_path.read_text(encoding="utf-8")),
                    100_000,
                )

    def test_codex_openai_yaml_contract(self) -> None:
        for skill_name in SKILLS:
            with self.subTest(skill=skill_name):
                data = load_yaml(ROOT / skill_name / "agents" / "openai.yaml")
                self.assertEqual(set(data), {"interface"})
                interface = data["interface"]
                self.assertEqual(
                    set(interface),
                    {"display_name", "short_description", "default_prompt"},
                )
                self.assertTrue(interface["display_name"].strip())
                self.assertGreaterEqual(len(interface["short_description"]), 25)
                self.assertLessEqual(len(interface["short_description"]), 64)
                self.assertIn(f"${skill_name}", interface["default_prompt"])

    def test_installation_docs_use_real_skill_identifiers(self) -> None:
        repository = (
            "shawndeng321/"
            "hermes-obsidian-legal-cssci-wiki-writing-skills"
        )
        root_readme = (ROOT / "README.md").read_text(encoding="utf-8")
        for skill_name in SKILLS:
            self.assertIn(
                f"hermes skills install {repository}/{skill_name}",
                root_readme,
            )
        self.assertIn(".codex\\skills", root_readme)
        self.assertIn("Copy-Item", root_readme)
        self.assertNotIn("hermes skills install <本仓库地址>", root_readme)
        for skill_name in SKILLS:
            skill_readme = (ROOT / skill_name / "README.md").read_text(
                encoding="utf-8"
            )
            self.assertNotIn("git clone <本仓库地址>", skill_readme)

    def test_documentation_has_no_known_stale_metadata_or_placeholders(self) -> None:
        root_readme = (ROOT / "README.md").read_text(encoding="utf-8")
        paper_readme = (ROOT / "chinese-law-paper-writing" / "README.md").read_text(
            encoding="utf-8"
        )
        paper_skill = (ROOT / "chinese-law-paper-writing" / "SKILL.md").read_text(
            encoding="utf-8"
        )
        self.assertNotIn("Obisidian", root_readme)
        self.assertIn("frontmatter 含 name/description/license/metadata", root_readme)
        self.assertNotIn("frontmatter 含 name/description/version", root_readme)
        self.assertIn("X.Y.Z", root_readme)
        self.assertNotIn("<本技能包仓库地址>", paper_readme)
        self.assertIn("版本号格式：X.Y.Z", paper_skill)


if __name__ == "__main__":
    unittest.main()
