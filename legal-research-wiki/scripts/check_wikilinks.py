#!/usr/bin/env python3
"""Vault-wide wikilink checker for Obsidian legal wikis (handles nested dirs).

Usage:
    python3 check_wikilinks.py /path/to/wiki [target_page]

- Recursively collects all .md page stems (Path.rglob) — handles nested dirs
  like entities/引用文献/, entities/案例/, entities/底稿/ (a flat os.listdir
  scan falsely reports valid links as dead).
- Reports dead links vault-wide, with known false positives separated:
  SCHEMA.md documentation examples (e.g. [[wikilinks]]) and log.md historical
  references to renamed pages are NOT defects.
- With target_page (page stem, no [[]] or .md), counts inbound backlinks
  from every page — use to verify a center-node page (研究设计/争议地图/矩阵)
  is not an island.

Exit code 0 even with dead links (reporting tool); false positives are listed
separately so they are never "fixed".
"""
import re
import sys
from pathlib import Path

KNOWN_FALSE_POSITIVE_FILES = {"SCHEMA.md", "log.md"}


def page_stems(wiki: Path) -> set[str]:
    return {p.stem for p in wiki.rglob("*.md")}


def check(wiki: Path, target: str | None = None):
    stems = page_stems(wiki)
    dead, false_pos = [], []
    backlinks = 0
    backlink_sources = []
    for p in sorted(wiki.rglob("*.md")):
        text = p.read_text(encoding="utf-8")
        links = set(re.findall(r"\[\[([^\]|#]+)", text))
        for link in links:
            if link not in stems:
                entry = (str(p.relative_to(wiki)), link)
                (false_pos if p.name in KNOWN_FALSE_POSITIVE_FILES else dead).append(entry)
        if target and target in links:
            backlinks += 1
            backlink_sources.append(str(p.relative_to(wiki)))

    print(f"Vault: {wiki}")
    print(f"Pages: {len(stems)} | Dead links: {len(dead)} | False positives (SCHEMA/log): {len(false_pos)}")
    for path, link in dead:
        print(f"  DEAD  {path} -> [[{link}]]")
    for path, link in false_pos:
        print(f"  FALSE {path} -> [[{link}]] (doc example / history — ignore)")
    if target:
        print(f"Backlinks to [[{target}]]: {backlinks}")
        for s in backlink_sources:
            print(f"  <- {s}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    check(Path(sys.argv[1]), sys.argv[2] if len(sys.argv) > 2 else None)
