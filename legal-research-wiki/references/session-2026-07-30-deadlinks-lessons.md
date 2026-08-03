# Session 2026-07-30: Dead Links + Missing Content Lessons

## The Dead Link Crisis

After ingesting 25 papers into the wiki, the user found 133 dead `[[wikilinks]]`
in Obsidian — links pointing to pages that didn't exist.

### Root cause

When generating "涉及概念" sections for paper entity pages, every concept keyword
extracted from the PDF was wrapped in `[[]]`:
```
涉及概念: [[工伤认定]], [[举证责任]], [[劳动关系]], [[经济从属性]], ...
```

But only ~15 of these 133 keywords had actual concept pages. The rest were
generic legal terms used in 1-2 papers.

### Resolution applied

1. **16 high-frequency links (3+ refs)**: Created 5 themed concept pages:
   - 工伤认定的核心要件 (absorbs: 工作时间, 工作场所, 工作原因, 上下班途中, 因工外出, 因果关系, 过错)
   - 工伤保险制度 (absorbs: 工伤保险, 工伤保险条例, 社会保险, 工伤补偿, 社会法)
   - 工伤认定的司法审查 (absorbs: 司法审查, 行政诉讼, 行政确认, 撤销重作判决)
   - 劳动关系与工伤认定 (absorbs: 劳动关系, 经济从属性, 职业伤害保障)
   - 工伤认定中的举证责任 (absorbs: 举证责任)

2. **117 low-frequency links (1-2 refs)**: Batch-converted `[[term]]` → plain `term`
   using string replacement in Python.

3. **Result: 0 dead links.**

### Key lesson

Not every keyword deserves a `[[]]` link. Only link to concepts that:
- Already have a page, OR
- Are important enough (3+ papers reference them) to warrant creating one

## The "详见原文" Persistence Problem

Despite `wiki-content-completeness` explicitly prohibiting placeholder text,
4 paper entity pages still had "详见原文" for abstract or conclusion.

### Root cause

Auto-extraction with pymupdf failed for certain PDFs because:
- Some PDFs use non-standard "摘要" formatting (brackets, full-width colons)
- Conclusion sections use varying headings (结语 vs 结论 vs 四、结语)
- Only reading first 10 pages missed conclusions in longer papers

### Fix applied

Wrote a dedicated re-extraction script (`/tmp/fix_papers.py`) that:
- Reads ALL pages (not just first 10)
- Tries multiple regex patterns for abstract
- Searches last 6000 chars for conclusion with multiple patterns
- Extracts section headings + first 500 chars as key paragraphs

All 4 papers successfully re-extracted with 457-800 char abstracts and conclusions.

## Verification Commands Used

### Dead link check (Python)
```python
import os, re
from collections import Counter
# ... see SKILL.md for full script
```

### Thin page check (bash)
```bash
find wiki/entities wiki/concepts -name "*.md" -exec wc -c {} \; | sort -n | head -20
```

### Content audit (Python)
```python
# Check for "详见原文" or "待补充" in all pages
for d in ["entities", "concepts"]:
    for f in os.listdir(f"{wiki}/{d}"):
        if f.endswith('.md'):
            content = open(f"{wiki}/{d}/{f}").read()
            if "详见原文" in content or "待补充" in content:
                print(f"⚠️ {f}")
```
