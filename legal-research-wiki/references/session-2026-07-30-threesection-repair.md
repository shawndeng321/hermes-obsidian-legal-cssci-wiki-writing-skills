# Session: Three-Section Batch Quality Repair (2026-07-30)

## Context

7 paper entity pages had quality defects across three sections (摘要, 核心论点,
主要结论). The task was to re-extract PDF原文 and repair all three sections
to match a known-good benchmark page (梁琼芳, 403-char conclusion, 3-item
核心论点 with avg 259 chars/item).

This session extends the conclusion re-extraction workflow documented in
`session-2026-07-30-conclusion-reextraction.md` to cover **all three
content sections simultaneously**.

## Three Defect Types Identified

### 1. 摘要: English Abstract contamination

CNKI academic PDFs contain BOTH a Chinese 内容提要/摘要 AND an English
Abstract section. Auto-extraction sometimes grabs the **English** version
instead of the Chinese one, producing a 摘要 section full of English text
like:

```
Taking the close relationship between injuries and work as guidance，
Article 14 of theＲegulations on Work-Ｒelated Injury Insurance define...
```

**Detection**: Check 摘要 section for `[a-zA-Z]{10,}` patterns (long English
word runs). Any match indicates English contamination.

**Fix**: Extract the Chinese 内容提要/摘要 from the PDF (usually the first
text block after the title/author block) and replace the English text.

### 2. 核心论点: PDF extraction residue

Auto-extracted 核心论点 sections often contain PDF layout artifacts:

- **Page numbers**: `· 9 1 1 ·`, `· 0 2 1 ·` (centered page numbers from
  two-column academic journal layout)
- **Footnote markers**: `瑏瑠`, `瑔瑦` (Unicode private-use area characters
  from PDF footnote rendering)
- **Citation markers**: `〔1 〕`, `〔34〕` (bracketed footnote references)
- **Broken lines**: PDF page-width line breaks preserved as `\n`,
  splitting sentences mid-clause
- **PDF section headers**: `**一、问题的提出**` with bold markdown
  formatting from PDF heading detection

**Detection**: Regex scan for `·\s*\d+\s*\d*\s*·`, `瑏瑠|瑔瑦`, `〔\d+\s*〕`,
and `**[一二三四五]、` patterns.

**Fix**: Manually rewrite the 核心论点 section as clean, numbered arguments
(3-4 items, each 200+ chars) based on the PDF's actual section structure.
Do NOT attempt to clean PDF residue with find-replace — the underlying text
is too fragmented. Rewrite from scratch using the PDF content as source.

### 3. 主要结论: Multiple defect subtypes

- **Fragmented start**: conclusion begins with `;` or `，` (mid-sentence
  fragment from regex matching wrong occurrence of 结语/结论)
- **English Abstract appended**: the English Abstract text appears at the
  end of the conclusion section (pymupdf extracted it as part of the
  concluding text)
- **Too short**: conclusion under 200 chars (incomplete extraction)

**Fix**: Read the last 2000-3000 chars of the full PDF text to find the
real 结语/结語/结论 section. Manually synthesize a 200-400 char conclusion
if no explicit section exists.

## Workflow That Worked

### Step 1: Extract all PDFs to /tmp/ via execute_code

```python
import fitz, os
pdf_base = "/path/to/wiki/raw/papers"
pdfs = {"author": "filename.pdf", ...}
for author, fname in pdfs.items():
    doc = fitz.open(os.path.join(pdf_base, fname))
    text = "".join(page.get_text() for page in doc)
    doc.close()
    with open(f"/tmp/pdf_{author}.txt", "w", encoding="utf-8") as f:
        f.write(text)
```

### Step 2: Read PDF text to locate source sections

Read first 3000 chars (for 摘要/内容提要) and last 2000-3000 chars (for
结语/结论) of each /tmp/ file. Also read middle sections (8000-16000) for
核心论点 source material.

### Step 3: Write replacement text via execute_code

**IMPORTANT**: This session successfully inlined Chinese text (including
full-width punctuation `、""——：；`) directly in Python string literals
inside `execute_code` without any SyntaxError. The previously documented
pitfall about Chinese punctuation causing SyntaxError appears to be
resolved in the current Hermes runtime. However, `write_file` to /tmp/
remains the safest fallback if any encoding issue arises.

Use a `replace_section()` helper for surgical replacement:

```python
import re

def replace_section(content, section_name, new_content):
    """Replace content between ## section_name and next ## header."""
    pattern = r'(## ' + re.escape(section_name) + r'\n\n).*?(\n\n## )'
    replacement = r'\g<1>' + new_content + r'\g<2>'
    return re.sub(pattern, replacement, content, count=1, flags=re.DOTALL)
```

### Step 4: Batch verification

Run a comprehensive check across all repaired pages:

```python
# For each paper, check:
# 1. 摘要: no English words ≥10 chars
# 2. 核心论点: no PDF residue (page numbers, footnote markers, citation brackets)
# 3. 主要结论: ≥200 chars, no fragment start (；), no English Abstract
# 4. Compare against benchmark metrics (梁琼芳: 摘要≥100, 3+ args, avg≥100/item, 结论≥200)
```

## Benchmark-Driven Quality Repair Pattern

1. **Identify a known-good page** as the quality benchmark (梁琼芳 in this
   session: 摘要 176 chars, 核心论点 3 items avg 259 chars, 主要结论 403 chars)
2. **Extract benchmark metrics**: min abstract length, min arg count, min
   avg arg length, min conclusion length
3. **Scan all target pages** against benchmark thresholds
4. **Repair failing pages** by re-extracting from PDF原文
5. **Re-verify** all pages pass benchmark thresholds

## Results

| Paper | 摘要 | 核心论点 | Items | Avg/item | 主要结论 | Defects Fixed |
|-------|------|----------|-------|----------|----------|---------------|
| 郑晓珊 | 385 | 1130 | 4 | 278 | 386 | 英文摘要+PDF残留论点+英文结论 |
| 侯玲玲 | 272 | 1022 | 4 | 251 | 447 | 英文摘要+PDF残留论点+碎片结论 |
| 杨曙光 | 373 | 949 | 3 | 312 | 423 | 英文摘要+PDF残留论点+分号碎片结论 |
| 王东伟 | 146 | 1233 | 4 | 304 | 442 | PDF残留论点 |
| 黎建飞 | 194 | 1085 | 4 | 267 | 422 | PDF残留论点 |
| 张相军 | 244 | 974 | 4 | 239 | 394 | 结论过短(134→394) |
| 沈建峰 | 286 | 903 | 4 | 221 | 466 | 结论过短(188→466)+引用规范格式 |

All 7 pages passed verification: 0 English残留, 0 PDF残留, 0 碎片结论,
all conclusions ≥200 chars.

## Key Lessons

1. **English Abstract contamination is a distinct defect type** — separate
   from PDF format artifacts. CNKI PDFs always have both Chinese and English
   abstracts; auto-extraction may grab either. Always check for English text
   in the 摘要 section.

2. **核心论点 sections need full rewrite, not cleanup** — PDF residue in
   核心论点 is too pervasive (page numbers, footnotes, broken lines) for
   find-replace. Rewrite the section as clean numbered arguments based on
   the PDF's section structure.

3. **execute_code handles Chinese Unicode text properly** — inline Chinese
   text with full-width punctuation in Python string literals works in the
   current Hermes runtime. The `write_file` to /tmp/ approach remains a
   safe fallback but is no longer strictly required.

4. **Benchmark-driven repair ensures uniform quality** — using a known-good
   page as the standard, then systematically raising all pages to that
   standard, produces consistent results that the user can trust.
