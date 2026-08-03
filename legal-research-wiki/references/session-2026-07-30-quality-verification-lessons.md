# Session 2026-07-30 (Phase 2): Unified Quality Verification & Conclusion Re-extraction

## Context

After the cross-reference network was built and dead links were resolved (Phase 1),
the user continued finding quality issues across multiple turns. Each turn revealed
a new dimension of quality failure that should have been caught proactively.

## The Multi-Pass Quality Crisis

The user found issues incrementally, each requiring a separate fix cycle:

| Turn | Issue Found | Scope | Root Cause |
|------|-------------|-------|------------|
| 1 | Dead links (133) | All entity pages | Every keyword wrapped in `[[]]` |
| 2 | Papers not connected to each other or draft | All 25 papers | No cross-reference sections |
| 3 | PDF format artifacts (］［, broken lines) | 8 pages | pymupdf extraction residue |
| 4 | Fragmented conclusions (starts with `，`) | 2 pages | Regex matched mid-text |
| 5 | YAML quote escaping (Obsidian red pages) | 5 pages | Curly quotes from PDF filenames |
| 6 | English text in abstracts | 3 pages | Bilingual PDFs, English Abstract extracted |
| 7 | Conclusions too short (<200 chars) | 15 pages | Subagent extraction returned short fragments |
| 8 | Section heading missing empty line | 29 pages | Subagent wrote `## Heading\nText` not `## Heading\n\nText` |

**Root cause**: No unified post-ingestion quality check. Each dimension was
discovered reactively by the user, not proactively by the agent.

## Solution: Unified 6-Dimension Quality Check

After ALL ingestion, cross-reference building, and dead-link resolution is complete,
run ONE comprehensive quality check that covers ALL dimensions:

```python
import os, re

wiki = "/path/to/wiki/entities"
all_files = [f for f in os.listdir(wiki) if f.endswith('.md')]

for fname in sorted(all_files):
    with open(os.path.join(wiki, fname)) as f:
        content = f.read()
    
    issues = []
    
    # 1. Abstract: 50+ chars, no English
    s = content.find("## 摘要\n\n")
    ns = content.find("\n## ", s + 10) if s >= 0 else -1
    abstract = content[s+8:ns].strip() if s >= 0 and ns > 0 else ""
    if len(abstract) < 50: issues.append(f"摘要过短({len(abstract)}字)")
    if re.search(r'[A-Za-z]{10,}', abstract): issues.append("摘要含英文")
    
    # 2. Conclusion: 200+ chars, no punctuation start
    s = content.find("## 主要结论\n\n")
    ns = content.find("\n## ", s + 15) if s >= 0 else -1
    concl = content[s+12:ns].strip() if s >= 0 and ns > 0 else ""
    if len(concl) < 200: issues.append(f"结论过短({len(concl)}字)")
    if concl and concl[0] in '，。；、的而;': issues.append("结论标点开头")
    
    # 3. No PDF artifacts
    if '］' in content or '［' in content: issues.append("含］［符号")
    
    # 4. Keywords clean
    s = content.find("## 关键词\n\n")
    ns = content.find("\n## ", s + 10) if s >= 0 else -1
    kw = content[s+8:ns].strip() if s >= 0 and ns > 0 else ""
    if '\n' in kw or '］' in kw: issues.append("关键词格式异常")
    
    # 5. YAML frontmatter: no curly quotes
    fm = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
    if fm and ('\u201c' in fm.group(1) or '\u201d' in fm.group(1)):
        issues.append("YAML含中文引号")
    
    # 6. Section headings have empty line after
    for heading in ["摘要", "关键词", "核心论点", "主要结论"]:
        if f"## {heading}\n[^#\n]" in content and f"## {heading}\n\n" not in content:
            issues.append(f"## {heading}后缺空行")
    
    if issues:
        print(f"⚠️ {fname}: {issues}")
    else:
        print(f"✅ {fname}")
```

**Rule: ALL 6 dimensions must pass before declaring ingestion complete.
Do NOT declare "all done" after fixing one dimension.**

## Key Lessons

### 1. English in abstracts (bilingual PDFs)

Chinese academic PDFs from CNKI often have bilingual abstracts. pymupdf extracts
both, and the English text leaks into the wiki page's abstract section.

**Fix**: After extraction, strip English sentences from abstract:
```python
abstract = re.sub(r'[A-Za-z]{3,}[^，。；！？\n]*', '', abstract)
```

### 2. Conclusion section heading heterogeneity

PDF conclusion sections use varied headers. Don't assume `结语` or `结论`:
- `五、结语` (most common in 法学 papers)
- `五、结论与政策建议` (some 社会保障 papers)
- No explicit section — use last 1-2 paragraphs
- Some papers (e.g., 郑尚元) have the conclusion embedded in the 摘要/提要

### 3. Section heading empty line

Subagents writing wiki pages may use `## Heading\nText` (single newline) instead
of `## Heading\n\nText` (double newline = empty line). This causes Obsidian to
render the heading and text on the same line.

**Fix**: Regex pass after all writes:
```python
for heading in ["摘要", "关键词", "核心论点", "研究方法", "主要结论", ...]:
    content = re.sub(f'(## {heading})\\n(?!\\n|##)', r'\1\n\n', content)
```

### 4. Subagent conclusion extraction reliability

Subagents tasked with extracting conclusions from PDFs may:
- Extract English abstracts instead of Chinese conclusions
- Return section headings only (not actual content)
- Write with different section formatting than the main agent

**Mitigation**: After subagent completion, always run the unified quality check
and manually fix any failures. Do not trust subagent "completed" status.

### 5. The user's patience is finite

The user found 8 separate quality issues across 8 turns. Each time they had to
report it, the agent had to diagnose and fix it. This erodes trust.

**Rule**: After any batch ingestion, run ALL quality checks proactively.
Present a single quality report showing all dimensions passing, rather than
declaring "done" and waiting for the user to find the next issue.

## Parallel Subagent Strategy for Quality Fixes

When 15+ files need conclusion re-extraction or other fixes:

1. Split into 3 groups of ~7 files each
2. Each subagent reads PDF, extracts proper conclusion, writes to wiki file
3. Main agent runs unified quality check after ALL subagents complete
4. Manually fix any remaining failures (subagents will not achieve 100% quality)

**Critical**: Subagent output is unreliable for:
- Abstract extraction (may include English)
- Conclusion extraction (may match mid-text fragments)
- Section formatting (may use single newline instead of double)

Always verify subagent output against the 6-dimension quality bar.
