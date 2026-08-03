# Session: Second Batch Conclusion Re-extraction (2026-07-30)

## Context

7 paper entity pages had conclusions under 200 chars (84–151 chars each).
Task: re-extract from PDFs and replace the `## 主要结论` section, bringing all 7
to 200+ chars with unified quality.

This session discovered 6 new PDF-extraction pitfalls beyond those in the
first conclusion re-extraction batch (`session-2026-07-30-conclusion-reextraction.md`).

## Results

| Paper | Old (chars) | New (chars) | Source in PDF |
|-------|------------|------------|---------------|
| 杜强强 | 151 | 439 | 六、结语 |
| 谭金可 | 117 | 385 | 四、结语 |
| 葛翔 | 127 | 215 | Last paragraph (no explicit header) |
| 莫良元 | 123 | 204 | 结　语 (fullwidth space between chars) |
| 王敏 | 144 | 1077 | 结语 (chars split across newline: 结\n语) |
| 黄辉 | 141 | 586 | Last theoretical section (类型化), not a 结语 |
| 李超 | 94 | 1926 | Section 四 (standards discussion serves as conclusion) |

## New Pitfalls Discovered

### 1. Fullwidth English Abstract Contamination

CNKI PDFs often contain English abstracts in **fullwidth characters**
(`ＯｎｔｈｅＪｕｄｉｃｉａｌＡｐｐｌｉｃａｔｉｏｎ...`) after the Chinese conclusion.
These appear as continuous blocks of fullwidth ASCII (U+FF01–U+FF5E range).

**Naive fix fails**: The regex `[Ａ-Ｚａ-ｚ０-９...]+` is too aggressive — it
matches individual fullwidth chars scattered in Chinese text (like fullwidth
digits in page numbers) and nukes the Chinese text around them.

**Correct fix**: Remove fullwidth-English-dominant LINES, not individual chars:

```python
lines = text.split('\n')
cleaned_lines = []
for line in lines:
    fw_count = sum(1 for c in line if '\uff01' <= c <= '\uff5e')
    cn_count = sum(1 for c in line if '\u4e00' <= c <= '\u9fff')
    total_chars = len(line.strip())
    # Skip lines that are predominantly fullwidth English (abstracts)
    if total_chars > 10 and fw_count > cn_count * 2 and fw_count > 10:
        continue
    cleaned_lines.append(line)
text = '\n'.join(cleaned_lines)
```

### 2. Embedded Page Headers in Mid-sentence Text

PDF page headers like `0\n6\n中州学刊2020 年第12 期\n` get embedded in the
middle of a sentence during extraction. The line-joining regex
`([^\n。！？；：\n])\n([^\n])` merges them into the text, creating garbage
like "在06中州学刊2020年第12期效果上是存疑的".

**Fix**: Strip page-header patterns BEFORE joining lines:

```python
text = re.sub(r'\d+\n\d+\n[^\n]*学刊[^\n]*期\n', '', text)
text = re.sub(r'\d+\n\d+[^\n]*学刊[^\n]*期', '', text)
text = re.sub(r'\d+\n[^\n]*法学[^\n]*期\n', '', text)
text = re.sub(r'\d+\n[^\n]*研究[^\n]*\n', '', text)
```

### 3. Section Headers Split Across Newlines

王敏's `结语` header appears as `结\n语\n` in the extracted text (the two
characters are on separate lines). A `find("结语")` search fails.

**Fix**: Search for the split pattern:

```python
idx = raw.find("结\n语\n工伤认定行政诉讼")
if idx < 0:
    idx = raw.find("结\n语")
```

Also applies to `结　语` (fullwidth space between chars, as in 莫良元) —
search for `"结　语"` with the fullwidth space U+3000.

### 4. No Explicit Conclusion Section — Use Last Paragraph(s)

Three of seven papers had NO `结语`/`结论` header:

| Paper | Strategy |
|-------|----------|
| 葛翔 | Last paragraph starting with "从统计样本的分析来看" — serves as summary/conclusion |
| 黄辉 | Last theoretical section (（三）类型化) — the conclusion is the theory itself |
| 李超 | Entire section 四 (standards discussion) — the framework IS the conclusion |

**Detection**: If no `结语`/`结论`/`结　语`/`总结`/`余论` marker is found,
search for the last substantive paragraph before `责任编辑` or `（责任编辑`.

### 5. Leaked Section Headers in Extracted Text

When extracting from a section that starts with a numbered header like
`（三）通过利益衡量确立法律内部体系和"类型化"`, the header text leaks into
the conclusion. Must be stripped after extraction:

```python
# Remove leaked section title (Chinese curly quotes \u201c \u201d)
leaked_title = '通过利益衡量确立法律内部体系和\u201c 类型化\u201d\u201c 类型化\u201d'
if conclusion_text.startswith(leaked_title):
    conclusion_text = conclusion_text[len(leaked_title):]
```

### 6. Trailing Paper/Journal Footers

After the conclusion paragraph, PDF text may contain:
- Paper title footer: `１莫良元：行政诉讼撤销重作判决的司法适用研究`
- English abstract marker: `(\n` (opening paren of a citation)
- `（责任编辑：林鸿潮）`

**Fix**: Strip these with targeted regex:

```python
text = re.sub(r'\n[０-９\d]+[^\n]*：[^\n]*(研究|可诉性)\s*$', '', text)
text = re.sub(r'（责任编辑[^\n]*）', '', text)
text = re.sub(r'\(\s*$', '', text)
```

## Reusable `clean_conclusion()` Function

The complete cleaning pipeline for PDF-extracted conclusion text:

```python
def clean_conclusion(text):
    """Thorough cleaning of PDF-extracted conclusion text."""
    # 1. Remove special unicode chars from PDF rendering
    text = text.replace('\ue5d2', '').replace('\ue5cf', '')
    text = text.replace('\x0f', '').replace('\x0e', '')
    # 2. Remove hyphenation at line breaks
    text = re.sub(r'-\n', '', text)
    # 3. Remove embedded page headers/journal names (BEFORE joining lines)
    text = re.sub(r'\d+\n\d+\n[^\n]*学刊[^\n]*期\n', '', text)
    text = re.sub(r'\d+\n\d+[^\n]*学刊[^\n]*期', '', text)
    text = re.sub(r'\d+\n[^\n]*法学[^\n]*期\n', '', text)
    text = re.sub(r'\d+\n[^\n]*研究[^\n]*\n', '', text)
    text = re.sub(r'\n\d+\n', '\n', text)
    # 4. Remove footnote reference numbers ①②③
    text = re.sub(r'[①②③④⑤⑥⑦⑧⑨⑩]', '', text)
    # 5. Remove section headers if present
    text = re.sub(r'^（[三四五六七八九]）\s*', '', text)
    # 6. Join broken lines (lines ending without sentence-ending punctuation)
    text = re.sub(r'([^\n。！？；：\n）」』\)\]])\n([^\n])', r'\1\2', text)
    # 7. Remove trailing paper/journal footers
    text = re.sub(r'\n[０-９\d]+[^\n]*：[^\n]*(研究|可诉性)\s*$', '', text)
    text = re.sub(r'（责任编辑[^\n]*）', '', text)
    # 8. Normalize whitespace
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r' +', ' ', text)
    # 9. Remove fullwidth-English-dominant lines (abstracts)
    lines = text.split('\n')
    cleaned_lines = []
    for line in lines:
        fw_count = sum(1 for c in line if '\uff01' <= c <= '\uff5e')
        cn_count = sum(1 for c in line if '\u4e00' <= c <= '\u9fff')
        total_chars = len(line.strip())
        if total_chars > 10 and fw_count > cn_count * 2 and fw_count > 10:
            continue
        cleaned_lines.append(line)
    text = '\n'.join(cleaned_lines)
    return text.strip()
```

## Updated Conclusion Header Heterogeneity Table

Papers seen across both batches:

| Header pattern | Example papers |
|---------------|----------------|
| `六、结语` | 杜强强 |
| `四、结语` | 谭金可 |
| `五、结语` | 战东升, 李满奎 |
| `五、结论与政策建议` | 马孟琛 |
| `五、结论` | 梁琼芳 |
| `结　语` (fullwidth space) | 莫良元 |
| `结\n语` (split across newline) | 王敏 |
| No explicit section — last paragraph | 葛翔, 艾琳 |
| No explicit section — last theoretical section | 黄辉 |
| No explicit section — entire final section | 李超 |
| `提要` at top serves as conclusion | 郑尚元 |

## Verification Checklist

After writing conclusions, verify ALL of:
1. ✅ Char count ≥ 200
2. ✅ No English text (no `[A-Za-z]{15,}` matches)
3. ✅ No page numbers (`\n\d+\n` pattern)
4. ✅ No fullwidth English blocks
5. ✅ All section headers intact (count `## ` headers — should be 11)
6. ✅ No leaked section headers at start of conclusion text
7. ✅ No trailing paper footers or `责任编辑` markers
