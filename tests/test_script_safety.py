import hashlib
import os
import zipfile
import xml.etree.ElementTree as ET
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CLEAN_SCRIPT = ROOT / "legal-research-wiki" / "scripts" / "clean_pdf_artifacts.py"
EXTRACT_SCRIPT = ROOT / "legal-research-wiki" / "scripts" / "batch_extract_papers.py"
SYNC_SCRIPT = ROOT / "legal-wiki-audit-repair" / "scripts" / "sync_paper_case_links.py"
INSERT_NORM_SCRIPT = ROOT / "legal-wiki-audit-repair" / "scripts" / "insert_norm_sections.py"
DOCX_SCRIPT = ROOT / "chinese-law-paper-writing" / "scripts" / "md2docx_footnotes.py"
MULTIMODAL_AUDIT_SCRIPT = (
    ROOT / "legal-wiki-audit-repair" / "scripts" / "multimodal_audit.py"
)


class ScriptSafetyTests(unittest.TestCase):
    def run_script(self, script, *args):
        return subprocess.run(
            [sys.executable, "-X", "utf8", str(script), *map(str, args)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )

    def test_clean_pdf_dry_run_is_recursive_and_does_not_write(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "entities"
            page = root / "nested" / "paper.md"
            page.parent.mkdir(parents=True)
            page.write_text(
                "# Paper\n\n## 关键词\n\n甲\n乙\n\n## 摘要\n\n摘要］\n\n## 结论\n",
                encoding="utf-8",
            )
            before = hashlib.sha256(page.read_bytes()).digest()

            result = self.run_script(CLEAN_SCRIPT, root, "--dry-run")

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("paper.md", result.stdout)
            self.assertIn("DRY-RUN", result.stdout)
            self.assertEqual(before, hashlib.sha256(page.read_bytes()).digest())

    def test_clean_pdf_requires_backup_and_rejects_files_outside_scope(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "entities"
            page = root / "paper.md"
            outside = Path(tmp) / "outside.md"
            root.mkdir()
            content = "# Paper\n\n［artifact］\n"
            page.write_text(content, encoding="utf-8")
            outside.write_text(content, encoding="utf-8")

            missing_backup = self.run_script(CLEAN_SCRIPT, root)
            self.assertNotEqual(missing_backup.returncode, 0)
            self.assertEqual(page.read_text(encoding="utf-8"), content)

            outside_result = self.run_script(CLEAN_SCRIPT, root, str(outside), "--dry-run")
            self.assertNotEqual(outside_result.returncode, 0)
            self.assertEqual(outside.read_text(encoding="utf-8"), content)

    def test_clean_pdf_creates_backup_before_writing(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "entities"
            page = root / "paper.md"
            backup = Path(tmp) / "backup"
            root.mkdir()
            page.write_text("# Paper\n\n［artifact］\n", encoding="utf-8")

            result = self.run_script(CLEAN_SCRIPT, root, "--backup-dir", backup)

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue((backup / "paper.md").exists())
            self.assertIn("［artifact］", (backup / "paper.md").read_text(encoding="utf-8"))
            self.assertNotIn("［artifact］", page.read_text(encoding="utf-8"))

    def test_batch_extract_dry_run_does_not_clobber_existing_text(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pdf = root / "article.pdf"
            txt = root / "article.txt"
            pdf.write_bytes(b"not a real pdf")
            txt.write_text("keep me", encoding="utf-8")

            result = self.run_script(EXTRACT_SCRIPT, root, "--dry-run")

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("article.txt", result.stdout)
            self.assertIn("keep me", txt.read_text(encoding="utf-8"))

    def test_mutating_wiki_scripts_require_a_caller_supplied_vault(self):
        for script in (SYNC_SCRIPT, INSERT_NORM_SCRIPT):
            result = self.run_script(script)
            self.assertNotEqual(result.returncode, 0, script.name)
            self.assertIn("WIKI_PATH", result.stderr)
            self.assertNotIn("/Users/shawndeng/Desktop/", script.read_text(encoding="utf-8"))

    def test_sync_and_norm_scripts_expose_read_only_preview(self):
        for script in (SYNC_SCRIPT, INSERT_NORM_SCRIPT):
            result = self.run_script(script, "--help")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("--dry-run", result.stdout)

    def test_docx_script_generates_real_footnotes_from_cli_inputs(self):
        try:
            from docx import Document
            from docx.enum.style import WD_STYLE_TYPE
        except ImportError as exc:  # pragma: no cover - environment-specific
            self.skipTest(f"python-docx unavailable: {exc}")

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            template = root / "template.docx"
            draft = root / "draft.md"
            output = root / "output.docx"
            doc = Document()
            for name in ("一级标题", "二级标题", "三级标题", "正文1", "FootnoteText", "FootnoteReference"):
                if name not in [style.name for style in doc.styles]:
                    doc.styles.add_style(name, WD_STYLE_TYPE.PARAGRAPH)
            doc.save(template)
            draft.write_text(
                "题目\n作者姓名\n摘要：摘要内容\n关键词：工伤；举证\n一、正文\n正文含脚注[1]。\n\n## 脚注\n[1] 判决书，第1页。\n",
                encoding="utf-8",
            )

            result = self.run_script(DOCX_SCRIPT, "--src", template, "--md", draft, "--dst", output)

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(output.exists())
            Document(output)
            with zipfile.ZipFile(output) as archive:
                document_xml = archive.read("word/document.xml")
                footnotes_xml = archive.read("word/footnotes.xml")
            ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
            document_root = ET.fromstring(document_xml)
            footnotes_root = ET.fromstring(footnotes_xml)
            refs = document_root.findall(".//w:footnoteReference", ns)
            ids = [node.attrib["{%s}id" % ns["w"]] for node in footnotes_root.findall("w:footnote", ns)]
            self.assertEqual(len(refs), 1)
            self.assertIn("1", ids)
            self.assertIn("判决书，第1页。", footnotes_xml.decode("utf-8"))

    def test_multimodal_audit_normalizes_windows_raw_paths(self):
        with tempfile.TemporaryDirectory() as tmp:
            wiki = Path(tmp) / "wiki"
            entities = wiki / "entities"
            screenshots = wiki / "raw" / "screenshots"
            entities.mkdir(parents=True)
            screenshots.mkdir(parents=True)

            (wiki / "index.md").write_text(
                "当前纳入导航的页面：1\n\n- [[Topic]]\n",
                encoding="utf-8",
            )
            (wiki / "SCHEMA.md").write_text(
                "### A. 概念类\n- topic\n",
                encoding="utf-8",
            )
            (wiki / "log.md").write_text(
                "## [2026-08-07] ingest\n\n- raw/screenshots/sample.md\n",
                encoding="utf-8",
            )
            (entities / "Topic.md").write_text(
                "---\n"
                "title: Topic\n"
                "created: 2026-08-07\n"
                "updated: 2026-08-07\n"
                "type: concept\n"
                "tags: [topic]\n"
                "sources: [raw/screenshots/sample.md]\n"
                "---\n\n"
                "# Topic\n\n[[Topic]]\n",
                encoding="utf-8",
            )
            (screenshots / "sample.png").write_bytes(b"test-image")
            (screenshots / "sample.md").write_text(
                "---\n"
                "title: Sample\n"
                "sha256: abc123\n"
                "---\n\n"
                "line one\nline two\nline three\n",
                encoding="utf-8",
            )

            result = self.run_script(MULTIMODAL_AUDIT_SCRIPT, wiki)

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("All raw .md referenced in log", result.stdout)
            self.assertIn("sample.png — extract has 3 body lines", result.stdout)

    def test_multimodal_audit_requires_an_explicit_wiki_path(self):
        env = os.environ.copy()
        env.pop("WIKI_PATH", None)

        result = subprocess.run(
            [sys.executable, "-X", "utf8", str(MULTIMODAL_AUDIT_SCRIPT)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            env=env,
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("WIKI_PATH", result.stderr)


if __name__ == "__main__":
    unittest.main()
