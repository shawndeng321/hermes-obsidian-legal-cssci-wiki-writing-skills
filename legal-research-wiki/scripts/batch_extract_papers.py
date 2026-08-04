#!/usr/bin/env python3
"""Extract text from PDFs without silently clobbering companion files.

Usage:
    python3 batch_extract_papers.py /path/to/papers --dry-run
    python3 batch_extract_papers.py /path/to/papers
    python3 batch_extract_papers.py /path/to/papers --force

By default, an existing ``.txt`` companion is skipped. ``--force`` is an
explicit opt-in to overwrite it; ``--dry-run`` never opens or writes a PDF.
"""
import argparse
import hashlib
import json
from pathlib import Path


def extract_pdf(pdf_path, txt_path):
    """Extract one PDF and return the original script's result fields."""
    import pymupdf

    sha = hashlib.sha256(pdf_path.read_bytes()).hexdigest()
    doc = pymupdf.open(str(pdf_path))
    try:
        text_parts = [page.get_text() for page in doc]
    finally:
        doc.close()
    text = "\n".join(text_parts)
    txt_path.write_text(text, encoding="utf-8")
    return {
        "file": pdf_path.name,
        "sha256": sha,
        "pages": len(text_parts),
        "chars": len(text),
        "status": "extracted",
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("papers_dir", nargs="?", default=".", help="directory containing PDF files")
    parser.add_argument("--dry-run", action="store_true", help="list planned work without reading or writing PDFs")
    parser.add_argument("--force", action="store_true", help="overwrite existing .txt companions")
    args = parser.parse_args(argv)

    root = Path(args.papers_dir).expanduser().resolve()
    if not root.is_dir():
        parser.error(f"papers directory does not exist: {root}")

    results = []
    for pdf_path in sorted(root.rglob("*.pdf")):
        txt_path = pdf_path.with_suffix(".txt")
        relative_pdf = str(pdf_path.relative_to(root))
        relative_txt = str(txt_path.relative_to(root))
        if txt_path.exists() and not args.force:
            results.append({
                "file": relative_pdf,
                "output": relative_txt,
                "status": "skipped_existing",
            })
            continue
        if args.dry_run:
            results.append({
                "file": relative_pdf,
                "output": relative_txt,
                "status": "planned",
            })
            continue
        results.append(extract_pdf(pdf_path, txt_path) | {"file": relative_pdf, "output": relative_txt})

    print(json.dumps(results, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
