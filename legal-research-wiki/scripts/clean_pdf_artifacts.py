#!/usr/bin/env python3
"""
Clean PDF extraction artifacts from wiki entity pages.

Usage:
    python3 clean_pdf_artifacts.py /path/to/wiki/entities --dry-run
    python3 clean_pdf_artifacts.py /path/to/wiki/entities --backup-dir /path/to/backup
    python3 clean_pdf_artifacts.py /path/to/wiki/entities --backup-dir /path/to/backup file1.md file2.md ...

If no specific files are given, recursively scans all .md files below the directory.
Dry-run is read-only. A backup directory is required before any in-place write.
"""
import argparse
import os
import re
import shutil
import sys
import tempfile
from pathlib import Path

def clean_pdf_artifacts(text):
    """Remove PDF extraction artifacts from wiki page content."""
    
    # 1. Remove full-width bracket artifacts
    text = text.replace('］', '').replace('［', '')
    text = text.replace('】', '').replace('【', '')
    
    # 2. Fix keywords section - remove newlines, normalize
    kw_pattern = r'(## 关键词\n\n)(.*?)(\n\n##)'
    kw_match = re.search(kw_pattern, text, re.DOTALL)
    if kw_match:
        kw_content = kw_match.group(2).replace('\n', '').strip().strip(';；')
        text = text[:kw_match.start()] + kw_match.group(1) + kw_content + kw_match.group(3) + text[kw_match.end():]
    
    # 3. Fix abstract - join broken lines (preserve paragraph breaks)
    for section_name in ['摘要', '主要结论']:
        pattern = rf'(## {section_name}\n\n)(.*?)(\n\n##)'
        match = re.search(pattern, text, re.DOTALL)
        if match:
            content = match.group(2)
            content = re.sub(r'([^\n])\n([^\n])', r'\1\2', content)
            text = text[:match.start()] + match.group(1) + content + match.group(3) + text[match.end():]
    
    # 4. Fix key arguments - join lines within paragraphs
    args_pattern = r'(## 核心论点\n\n)(.*?)(\n\n##)'
    args_match = re.search(args_pattern, text, re.DOTALL)
    if args_match:
        args_content = args_match.group(2)
        paragraphs = args_content.split('\n\n')
        fixed = [re.sub(r'([^\n])\n([^\n])', r'\1\2', p) for p in paragraphs]
        args_content = '\n\n'.join(fixed)
        text = text[:args_match.start()] + args_match.group(1) + args_content + args_match.group(3) + text[args_match.end():]
    
    return text


def scan_for_issues(filepath):
    """Check a single file for PDF artifacts."""
    content = Path(filepath).read_text(encoding="utf-8")
    issues = []
    if '］' in content or '［' in content: issues.append("PDF方括号残留")
    if 'Vo1.' in content: issues.append("OCR错误(Vo1.)")
    
    kw_match = re.search(r'## 关键词\n\n(.*?)\n\n##', content, re.DOTALL)
    if kw_match:
        kw = kw_match.group(1).strip()
        if '\n' in kw or '］' in kw or '【' in kw: issues.append("关键词格式异常")
    
    for section in ['摘要', '主要结论']:
        pattern = rf'## {section}\n\n(.*?)\n\n##'
        m = re.search(pattern, content, re.DOTALL)
        if m and re.search(r'[，；。]\n[^\n]', m.group(1)):
            issues.append(f"{section}PDF换行残留")
    
    return issues


def collect_files(entities_dir, specific_files=None):
    """Resolve inputs and reject explicit files outside the requested scope."""
    root = Path(entities_dir).expanduser().resolve()
    if not root.is_dir():
        raise ValueError(f"entities directory does not exist: {root}")
    if not specific_files:
        return root, sorted(root.rglob("*.md"))

    files = []
    for raw in specific_files:
        candidate = Path(raw).expanduser()
        if not candidate.is_absolute():
            candidate = root / candidate
        candidate = candidate.resolve()
        try:
            candidate.relative_to(root)
        except ValueError as exc:
            raise ValueError(f"file is outside entities directory: {raw}") from exc
        if candidate.suffix.lower() != ".md":
            raise ValueError(f"file is not a Markdown page: {raw}")
        files.append(candidate)
    return root, files


def validate_backup_dir(root, backup_dir):
    if not backup_dir:
        raise ValueError("in-place writes require --backup-dir")
    backup_root = Path(backup_dir).expanduser().resolve()
    if backup_root == root or root in backup_root.parents:
        raise ValueError("backup directory must not be inside entities directory")
    return backup_root


def write_atomic(path, text):
    """Replace one page atomically after its backup has been created."""
    path = Path(path)
    fd, tmp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as fh:
            fh.write(text)
        os.replace(tmp_name, path)
    except Exception:
        try:
            os.unlink(tmp_name)
        except FileNotFoundError:
            pass
        raise


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("entities_dir", help="directory containing wiki entity pages")
    parser.add_argument("files", nargs="*", help="optional Markdown files relative to entities_dir")
    parser.add_argument("--dry-run", action="store_true", help="report changes without writing")
    parser.add_argument("--backup-dir", help="backup destination required for writes")
    args = parser.parse_args(argv)

    try:
        root, files = collect_files(args.entities_dir, args.files)
    except ValueError as exc:
        parser.error(str(exc))

    changes = []
    for path in files:
        if not path.exists():
            print(f"  ⏭️ {path.relative_to(root)} (not found)")
            continue
        issues = scan_for_issues(path)
        if not issues:
            continue
        original = path.read_text(encoding="utf-8")
        cleaned = clean_pdf_artifacts(original)
        if cleaned == original:
            print(f"⚠️ {path.relative_to(root)}: issues detected but no changes made: {issues}")
            continue
        changes.append((path, issues, original, cleaned))

    if args.dry_run:
        for path, issues, _, _ in changes:
            print(f"[DRY-RUN] {path.relative_to(root)}: would fix {', '.join(issues)}")
        print(f"\nFixed: 0 files | Planned changes: {len(changes)} files | Remaining issues: not rewritten")
        return 0

    backup_root = validate_backup_dir(root, args.backup_dir) if changes else None
    # Preflight every backup path before changing any page, preventing partial batches.
    if backup_root is None:
        print("\nFixed: 0 files | Remaining issues: 0")
        return 0
    backup_root.mkdir(parents=True, exist_ok=True)
    destinations = []
    for path, _, _, _ in changes:
        destination = backup_root / path.relative_to(root)
        if destination.exists():
            raise RuntimeError(f"backup already exists; refusing to clobber it: {destination}")
        destinations.append((path, destination))
    for path, destination in destinations:
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, destination)

    fixed_count = 0
    for path, issues, _, cleaned in changes:
        write_atomic(path, cleaned)
        print(f"✅ {path.relative_to(root)}: fixed {', '.join(issues)}")
        fixed_count += 1

    remaining = sum(bool(scan_for_issues(path)) for path in files if path.exists())
    print(f"\nFixed: {fixed_count} files | Remaining issues: {remaining}")
    return 0


if __name__ == '__main__':
    main()
