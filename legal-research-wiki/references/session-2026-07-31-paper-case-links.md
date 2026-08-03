# Paper–Case Bidirectional Linking: Reusable Recipe

This reference records the verified workflow for linking existing literature pages to existing Chinese administrative-law case pages without creating false or dead edges.

## 1. Build the mapping before editing

For a vault with `entities/引用文献/` and `entities/案例/`:

1. Recursively inventory both page sets. Read each case page's YAML `title:` and the identifying sections (`基本信息`, `基本案情`, `裁判结果`, `裁判要旨`).
2. Extract each literature page's `## 引用案例` section. Treat each bullet as a citation candidate, not automatically as a graph edge.
3. Create a table with:
   - paper filename
   - original cited display name
   - proposed case-page stem
   - evidence (exact title, official identifier, case number, or distinctive facts)
   - confidence (`exact`, `identifier`, `verified anonymized`, or `unmatched`)
4. Freeze the affected-page list before a 10+ page edit.

## 2. Confidence rules

### Safe matches

- Exact case title to an existing case-page title.
- Guiding-case or procuratorial-case identifier to the case page whose `基本信息` carries that identifier.
- Official Gazette case with an exact title variant such as `劳动局` versus `劳保局`, after checking the case page's title and source.
- Anonymized paper citation only after comparing the administrative agency, procedural outcome, distinctive facts, and source material. Preserve the paper's wording as the alias:

```markdown
[[案例-2009-王长淮诉江苏省盱眙县劳动和社会保障局工伤行政确认案|王某某诉江苏省盱眙县劳动和社会保障局工伤行政确认案]]
```

### Keep as plain text

- Foreign cases, generic sample counts, unnamed statistics, and judicial materials for which the vault has no corresponding page.
- A case-number candidate that does not occur in the case page and has no distinctive factual match.
- Loose substring matches based only on common phrases (`工伤认定案`, a city, or a year). These produce false candidates.

## 3. Surgical editing pattern

Change only the case name or official identifier inside `## 引用案例`; retain the holding, source description, and explanatory text. For reverse edges, use the case page's existing `## 相关论文` section when it is already the vault convention. Add missing direct citing-paper links only; do not duplicate existing links or re-label a thematic link as a direct citation.

When a short `patch` target does not match, reread the actual section and retry with the full bullet line. A failed short replacement may reflect punctuation or wording differences; never assume the file changed. Recheck the file after every retry.

## 4. Verification skeleton

The following checks should be run after the batch (adapt `wiki`):

```python
from pathlib import Path
import re, yaml

wiki = Path("/path/to/wiki")
lit = wiki / "entities/引用文献"
cases = wiki / "entities/案例"
paper_stems = {p.stem for p in lit.glob("*.md")}
case_stems = {p.stem for p in cases.glob("*.md")}

edges = []
for page in lit.glob("*.md"):
    text = page.read_text(encoding="utf-8")
    m = re.search(r"^## 引用案例\n(.*?)(?=^## |\Z)", text, re.S | re.M)
    for target in re.findall(r"\[\[([^\]|]+)(?:\|[^\]]+)?\]\]", m.group(1) if m else ""):
        if target in case_stems:
            edges.append((page.stem, target))

assert all((cases / f"{case}.md").exists() for _, case in edges)
for paper, case in edges:
    case_text = (cases / f"{case}.md").read_text(encoding="utf-8")
    assert paper in re.findall(r"\[\[([^\]|]+)(?:\|[^\]]+)?\]\]", case_text), (paper, case)

# Recursive live-page dead-link check; classify SCHEMA/log examples separately.
existing = {p.stem for p in wiki.rglob("*.md")}
entity_dead = []
for page in wiki.rglob("*.md"):
    if page.name in {"SCHEMA.md", "log.md"}:
        continue
    for target in re.findall(r"\[\[([^\]|#]+)(?:#[^\]|]+)?(?:\|[^\]]+)?\]\]", page.read_text(encoding="utf-8")):
        if target not in existing:
            entity_dead.append((page, target))
assert not entity_dead, entity_dead
```

Report both counts: total link occurrences and unique `(paper, case)` pairs. One paper may show two display names for the same underlying case. Also report unmatched citations rather than implying that plain text is a defect.

## 5. User-facing completion format

Keep the report concise and action-first:

1. **Scope** — number of edited papers and case pages.
2. **Concrete changes** — important exact and anonymized mappings.
3. **Unmatched policy** — citations left plain because no existing page could be verified.
4. **Verification** — paper→case occurrences, unique edges, reverse-edge failures, live-page dead links, YAML/source checks.
5. **Deferred work** — statutes or new case ingestion explicitly not started.
