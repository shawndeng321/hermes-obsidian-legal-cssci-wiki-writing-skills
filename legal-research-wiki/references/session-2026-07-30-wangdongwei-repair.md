# Session 2026-07-30: Wang Dongwei Paper Repair

## Core Arguments Section Header Leak (NEW DEFECT TYPE)

### Problem
One of Wang Dongwei's papers (论工伤认定行政诉讼案件中的举证责任) had its `## 核心论点`
section filled with **raw PDF paragraph text containing section headers**. The PDF's
internal structure headers — `**一、问题的提出**`, `**二、溯因**`, `**三、再造**` —
were dumped verbatim as if they were core argument statements. Result: unreadable.

### Detection
Scan `## 核心论点` section for PDF structural markers:
```python
import re
core_args = extract_section(content, "核心论点")
if re.search(r'\*\*[一二三四五六]、[^，]{2,20}\*\*', core_args):
    print("⚠️ 核心论点含PDF小节标题残留 — needs rewrite")
```

### Root cause
When pymupdf extraction fails to parse structured arguments, the fallback grabs
the full body text including section headers, which the ingestion pipeline
doesn't filter out of the core arguments field.

### Fix
Read the PDF's actual section structure, then rewrite as numbered thesis statements
(3-4 items, each 200+ chars, with a bold topic prefix).

## Wrong Section as Conclusion

### Problem
Same Wang Dongwei paper: the `## 主要结论` section contained the paper's third
section text ("三、再造：工伤认定...") — a mid-body analytical section, not a
conclusion. The real conclusion was in a `余论` section at the very end of the PDF.

### Conclusion Header: 余论

`余论` (lit. "remaining remarks") is a common concluding header in Chinese legal
papers, appearing after the last numbered section but before `参考文献` or
`（责任编辑)`. It functions identically to `结语`/`结论`.

### Fix
Search PDF for `余论` OR the last text before `（收稿` or `（责任编辑`:
```python
conclusion = text[text.find("余 论"):text.find("（责任编辑")].strip()
```

## Abstract Typo Survival

### Problem
After multiple cleanup passes, "社会转型时期" still read "社社会转型时期" —
a single stray character from PDF extraction that regex-based cleanup missed.

### Detection
Scan first 20 chars of abstracts for doubled characters:
```python
abstract_start = abstract[:20]
if re.search(r'(.)\\1', abstract_start):
    print(f"⚠️ Possible typo at start: {abstract_start}")
```

## Three-Section Batch Repair Pattern

When one section on a page has issues, check ALL THREE key sections:
- `## 摘要`
- `## 核心论点`
- `## 主要结论`

Wang Dongwei's article had defects in all three: abstract typo, core-argument
header leak, and mid-body text as conclusion. Triage all three simultaneously.
