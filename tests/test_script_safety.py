import hashlib
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


if __name__ == "__main__":
    unittest.main()
