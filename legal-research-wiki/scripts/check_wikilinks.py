#!/usr/bin/env python3
"""Vault-wide wikilink checker for Obsidian legal wikis.

Usage:
    python3 check_wikilinks.py /path/to/wiki [target_page] [--strict]

Resolution follows Obsidian's real rules:
- links resolve by file name anywhere in the vault (nested directories are fine);
- aliases use `[[target|alias]]` in prose and `[[target\\|alias]]` in tables;
- `[[target#anchor]]`, `[[target#^block]]` and `[[target.md]]` resolve to `target`;
- embeds of attachments (`![[image.png]]`) resolve against any file name.

Reported separately:
- DEAD      real dead links in content pages;
- MALFORMED `&#124;` aliases (Obsidian does not treat them as a separator),
            links that swallow a heading (`[[x## ...`), or `[[` without a
            matching `]]` on the same line;
- TOLERATED links inside drafts/ (read-only historical drafts; footnote markers
            such as [[脚注12]] in draft working copies are expected there);
- FALSE     links inside maintenance documents: SCHEMA.md, log.md, rotated
            log-YYYY.md and root-level ledgers whose name contains 台账
            (rule examples and history — never "fix" these).

Hidden directories (`.maintenance/`, `.obsidian/`, `.trash/` ...) and backup
folders are skipped: backups must not make a deleted page look alive.

With target_page (page stem, no [[]] or .md), counts inbound backlinks from
every content page. Exit code is 0 unless --strict is given and DEAD or
MALFORMED links exist.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

KNOWN_FALSE_POSITIVE_FILES = {"SCHEMA.md", "log.md"}
ROTATED_LOG_RE = re.compile(r"^log-\d{4}.*\.md$")
DRAFT_DIR_NAMES = {"drafts"}
SKIPPED_DIR_NAMES = {"ghosts", "backup", "backups", "_scripts", "node_modules"}
LINK_RE = re.compile(r"(!?)\[\[([^\[\]\n]+?)\]\]")
ALIAS_SPLIT_RE = re.compile(r"\\\||(?<!\\)\|")
SWALLOWED_HEADING_RE = re.compile(r"\[\[[^\]\n]*##")


def is_skipped(path: Path, wiki: Path) -> bool:
    parts = path.relative_to(wiki).parts[:-1]
    return any(part.startswith(".") or part.lower() in SKIPPED_DIR_NAMES for part in parts)


def vault_files(wiki: Path) -> list[Path]:
    return [p for p in wiki.rglob("*") if p.is_file() and not is_skipped(p, wiki)]


def is_maintenance_doc(path: Path, wiki: Path) -> bool:
    if path.name in KNOWN_FALSE_POSITIVE_FILES or ROTATED_LOG_RE.match(path.name):
        return True
    return path.parent == wiki and "台账" in path.name


def is_draft(path: Path, wiki: Path) -> bool:
    return path.relative_to(wiki).parts[0] in DRAFT_DIR_NAMES


def link_target(raw: str) -> str:
    """Return the file part of a wikilink body, following Obsidian's parsing."""
    target = ALIAS_SPLIT_RE.split(raw, maxsplit=1)[0]
    target = target.split("#", 1)[0].strip()
    if target.lower().endswith(".md"):
        target = target[:-3]
    return target.rsplit("/", 1)[-1]


def malformed_links(line: str) -> list[str]:
    problems = []
    if "&#124;" in line and "[[" in line:
        problems.append("&#124; 不是别名分隔符（表格中请用 \\|）")
    if SWALLOWED_HEADING_RE.search(line):
        problems.append("链接吞掉了后面的标题（缺少 ]]）")
    if line.count("[[") > line.count("]]"):
        problems.append("[[ 与 ]] 数量不匹配（截断或缺右括号）")
    return problems


def check(wiki: Path, target: str | None = None) -> tuple[int, int]:
    files = vault_files(wiki)
    pages = [p for p in files if p.suffix.lower() == ".md"]
    stems = {p.stem for p in pages}
    names = {p.name for p in files}
    dead, false_pos, malformed, tolerated = [], [], [], []
    backlink_sources = []

    for page in sorted(pages):
        relative = str(page.relative_to(wiki))
        is_doc = is_maintenance_doc(page, wiki)
        in_drafts = is_draft(page, wiki)
        linked = set()
        for number, line in enumerate(page.read_text(encoding="utf-8").splitlines(), 1):
            if not is_doc and not in_drafts:
                for problem in malformed_links(line):
                    malformed.append((relative, number, problem, line.strip()[:80]))
            for _bang, raw in LINK_RE.findall(line):
                if "&#124;" in raw:
                    continue  # already reported as malformed
                name = link_target(raw)
                if not name:
                    continue  # [[#heading]] points into the same page
                linked.add(name)
                # Attachments (image.png, file.pdf) resolve by full file name;
                # notes resolve by stem. A stem that merely contains a dot
                # (e.g. "论文v2.0") still counts as a note.
                exists = name in stems or name in names
                if not exists:
                    bucket = false_pos if is_doc else tolerated if in_drafts else dead
                    bucket.append((relative, number, name))
        if target and target in linked and not is_doc and not in_drafts:
            backlink_sources.append(relative)

    print(f"Vault: {wiki}")
    print(
        f"Pages: {len(stems)} | Dead links: {len(dead)} | Malformed: {len(malformed)} | "
        f"Tolerated (drafts/): {len(tolerated)} | "
        f"False positives (SCHEMA/log/台账): {len(false_pos)}"
    )
    for path, number, name in dead:
        print(f"  DEAD       {path}:{number} -> [[{name}]]")
    for path, number, problem, snippet in malformed:
        print(f"  MALFORMED  {path}:{number} {problem} | {snippet}")
    footnote_markers = sum(1 for _, _, name in tolerated if re.fullmatch(r"脚注\d+", name))
    if footnote_markers:
        print(f"  TOLERATED  drafts/: {footnote_markers} footnote markers like [[脚注N]] (expected)")
    for path, number, name in tolerated:
        if not re.fullmatch(r"脚注\d+", name):
            print(f"  TOLERATED  {path}:{number} -> [[{name}]] (draft — not a live page)")
    for path, number, name in false_pos:
        print(f"  FALSE      {path}:{number} -> [[{name}]] (doc example / history — ignore)")
    if target:
        print(f"Backlinks to [[{target}]]: {len(backlink_sources)}")
        for source in backlink_sources:
            print(f"  <- {source}")
    return len(dead), len(malformed)


def main(argv: list[str]) -> int:
    args = [arg for arg in argv if arg != "--strict"]
    strict = len(args) != len(argv)
    if not args:
        print(__doc__)
        return 1
    wiki = Path(args[0]).expanduser()
    if not wiki.is_dir():
        print(f"Wiki root is not a directory: {wiki}", file=sys.stderr)
        return 1
    dead, malformed = check(wiki, args[1] if len(args) > 1 else None)
    return 1 if strict and (dead or malformed) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
