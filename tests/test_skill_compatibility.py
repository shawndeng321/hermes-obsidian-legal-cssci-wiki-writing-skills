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
EXPECTED_VERSIONS = {
    "chinese-law-paper-writing": "5.1.0",
    "legal-research-wiki": "4.1.0",
    "legal-wiki-audit-repair": "4.2.0",
}
MULTIMODAL_FILES = (
    "chinese-law-paper-writing/references/multimodal-citation-format.md",
    "legal-research-wiki/references/multimodal-audio-ingest.md",
    "legal-research-wiki/references/multimodal-bulk-refs.md",
    "legal-research-wiki/references/multimodal-image-ingest.md",
    "legal-research-wiki/references/multimodal-obsidian-headless.md",
    "legal-research-wiki/references/multimodal-pdf-extraction.md",
    "legal-wiki-audit-repair/references/multimodal-reingest-stubs.md",
    "legal-wiki-audit-repair/references/multimodal-sha256-bulk-fix.md",
    "legal-wiki-audit-repair/scripts/multimodal_audit.py",
)


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
                self.assertEqual(
                    str(metadata["version"]),
                    EXPECTED_VERSIONS[skill_name],
                )
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
        self.assertIn("--yes", root_readme)
        self.assertIn("$hermesHome", root_readme)
        self.assertIn("复制完整技能目录", root_readme)
        self.assertIn("## 2026-08 更新内容", root_readme)
        self.assertIn("git clone", root_readme)
        self.assertIn("#安装", root_readme)
        self.assertNotIn("hermes skills install <本仓库地址>", root_readme)
        for skill_name in SKILLS:
            skill_readme = (ROOT / skill_name / "README.md").read_text(
                encoding="utf-8"
            )
            self.assertNotIn("git clone <本仓库地址>", skill_readme)
            self.assertIn("../README.md#安装", skill_readme)
            self.assertIn("--yes", skill_readme)

    def test_documentation_has_no_known_stale_metadata_or_placeholders(self) -> None:
        readmes = [ROOT / "README.md"]
        readmes.extend(ROOT / skill_name / "README.md" for skill_name in SKILLS)
        combined = "\n".join(path.read_text(encoding="utf-8") for path in readmes)
        root_readme = readmes[0].read_text(encoding="utf-8")
        paper_readme = (ROOT / "chinese-law-paper-writing" / "README.md").read_text(
            encoding="utf-8"
        )
        paper_skill = (ROOT / "chinese-law-paper-writing" / "SKILL.md").read_text(
            encoding="utf-8"
        )
        self.assertNotIn("Obisidian", root_readme)
        self.assertIn("SKILL.md", root_readme)
        self.assertIn("agents/openai.yaml", root_readme)
        self.assertIn("X.Y.Z", root_readme)
        self.assertIn("Hermes 与 Codex", root_readme)
        self.assertIn("兼容性测试 8/8", root_readme)
        self.assertIn("脚本安全测试 9/9", root_readme)
        self.assertNotIn("尚未合并到 `main`", combined)
        self.assertNotIn("当前优化分支", combined)
        self.assertNotIn("合并到 `main` 后", combined)
        self.assertNotIn("<本技能包仓库地址>", paper_readme)
        self.assertIn("版本号格式：X.Y.Z", paper_skill)

    def test_large_skill_uses_reference_for_pitfalls(self) -> None:
        skill_path = ROOT / "legal-research-wiki" / "SKILL.md"
        skill_content = skill_path.read_text(encoding="utf-8")
        pitfalls_reference = (
            ROOT / "legal-research-wiki" / "references" / "pitfalls-and-lessons.md"
        )
        self.assertIn("references/pitfalls-and-lessons.md", skill_content)
        self.assertLessEqual(len(skill_content), 95_000)
        self.assertTrue(pitfalls_reference.exists())
        self.assertTrue(pitfalls_reference.read_text(encoding="utf-8").strip())

    def test_multimodal_package_is_complete_and_versions_are_consistent(self) -> None:
        root_readme = (ROOT / "README.md").read_text(encoding="utf-8")
        for skill_name, version in EXPECTED_VERSIONS.items():
            with self.subTest(skill=skill_name):
                skill_readme = (ROOT / skill_name / "README.md").read_text(
                    encoding="utf-8"
                )
                self.assertIn(f"v{version}", root_readme)
                self.assertIn(f"v{version}", skill_readme)

        for relative_path in MULTIMODAL_FILES:
            with self.subTest(path=relative_path):
                path = ROOT / relative_path
                self.assertTrue(path.exists(), relative_path)
                self.assertTrue(path.read_text(encoding="utf-8").strip())

    def test_obsidian_headless_guidance_protects_credentials_and_concurrent_edits(
        self,
    ) -> None:
        guidance = (
            ROOT
            / "legal-research-wiki"
            / "references"
            / "multimodal-obsidian-headless.md"
        ).read_text(encoding="utf-8")
        self.assertIn("\nob login\n", guidance)
        self.assertNotRegex(guidance, r"ob login[^\n]*--(?:email|password)")
        self.assertIn("并发", guidance)
        self.assertIn("备份", guidance)

    def test_local_markdown_links_in_integrated_skills_resolve(self) -> None:
        documents = [ROOT / skill_name / "SKILL.md" for skill_name in SKILLS]
        documents.extend(
            ROOT / relative_path
            for relative_path in MULTIMODAL_FILES
            if relative_path.endswith(".md")
        )
        for document in documents:
            with self.subTest(document=document.relative_to(ROOT)):
                self.assertTrue(document.exists(), document)
                content = document.read_text(encoding="utf-8")
                for target in re.findall(r"\[[^\]]+\]\(([^)]+)\)", content):
                    if "://" in target or target.startswith("#"):
                        continue
                    resolved = (document.parent / target.split("#", 1)[0]).resolve()
                    self.assertTrue(
                        resolved.exists(),
                        f"{document.relative_to(ROOT)} -> {target}",
                    )


if __name__ == "__main__":
    unittest.main()
