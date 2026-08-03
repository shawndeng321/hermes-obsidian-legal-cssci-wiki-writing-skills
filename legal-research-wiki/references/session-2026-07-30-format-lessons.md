# Session 2026-07-30 Format Cleanup Lessons

## Problem: PDF extraction artifacts visible in Obsidian

After batch-ingesting 25 papers via parallel subagent extraction, 8 of 29 entity pages
contained visible PDF format artifacts that the user spotted in Obsidian:

### Artifact types found

1. **Full-width brackets**: `］` and `［` from PDF layout boxes appeared in abstract,
   keywords, and body text. Caused by pymupdf preserving CJK punctuation from
   the original PDF typesetting.
   
2. **Broken lines mid-sentence**: PDF page-width line breaks preserved as `\n`,
   splitting sentences like "不确定法律概念\n如何将这些". The `re.sub(r'([^\n])\n([^\n])', r'\1\2')`
   pattern joins these while preserving paragraph breaks (double `\n`).

3. **Keyword corruption**: Keywords section had embedded newlines and bracket residue:
   ```
   ］工伤认定; 不确定法律概念; 司法审查
   ［
   ```
   Fix: strip brackets, join newlines, normalize separators.

4. **OCR errors**: `Vo1.` instead of `Vol.` — minor but visible.

### Root cause

pymupdf extracts text faithfully from the PDF, including CJK layout artifacts.
The batch extraction scripts focused on content (abstract, arguments, conclusions)
but did not clean formatting. When this text was pasted into wiki page templates,
the artifacts survived.

### Detection pattern

Scan each entity page after ingestion:
- Check for `］`, `［`, `】`, `【` characters
- Check keywords section for `\n` or bracket residue
- Check abstract/conclusion for `re.search(r'[，；。]\n[^\n]')` (Chinese punctuation
  followed by single newline = broken line)

### Fix pattern

```python
def clean_pdf_artifacts(text):
    # Strip brackets
    text = text.replace('］', '').replace('［', '').replace('】', '').replace('【', '')
    # Fix keywords (remove newlines)
    # Fix abstract/conclusion (join broken lines, preserve paragraph breaks)
    # Fix key arguments (join lines within paragraphs)
```

See `scripts/clean_pdf_artifacts.py` for the full reusable script.

### Lesson

Format cleanliness is a **third dimension** of wiki quality, alongside:
1. Content completeness (no empty pages, no "详见原文")
2. Link integrity (no dead links)
3. **Format cleanliness** (no PDF artifacts, no broken lines)

All three must pass before declaring ingestion complete. The user sees everything
in Obsidian and will spot formatting issues immediately.
