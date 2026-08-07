# 本地 PDF 提取（pymupdf 流程）

> **来源**：multimodal-wiki v1.0.0（kigner/multimodal-wiki）`references/pdf-extraction.md`，2026-08 融合。
> 法学库用法：与既有 PDF 提取纪律互补——法学库要求提取后做格式清洗（去方括号、合并断行），
> 此文档补充 sha256 前页与 raw/papers 双文件保存的规范。

# Local PDF Extraction for Wiki Ingestion

When ingesting local PDF files (not URLs), `web_extract` won't work because it
expects HTTP(S) URLs. Use this workflow instead.

## Step 1: Copy PDFs to raw/papers/

```powershell
$wikiPath = 'D:\wiki'
Copy-Item -Path 'C:\source-dir\*.pdf' -Destination (Join-Path $wikiPath 'raw\papers')
```

## Step 2: Install pymupdf (if needed)

```bash
uv pip install pymupdf
# or: pip install pymupdf
```

## Step 3: Extract text with the host's code-execution facility

```python
import fitz  # pymupdf
import os, hashlib, re
from datetime import datetime

papers_dir = os.path.join(os.environ["WIKI_PATH"], "raw", "papers")  # your wiki root (e.g. D:\wiki)

for fname in sorted(os.listdir(papers_dir)):
    if not fname.endswith('.pdf'):
        continue

    pdf_path = os.path.join(papers_dir, fname)
    doc = fitz.open(pdf_path)
    text_parts = [page.get_text() for page in doc]
    doc.close()

    full_text = '\n\n'.join(text_parts)
    sha = hashlib.sha256(full_text.encode('utf-8')).hexdigest()

    # Raw frontmatter
    frontmatter = f"""---
source_path: raw/papers/{fname}
ingested: {datetime.now().strftime('%Y-%m-%d')}
sha256: {sha}
---

"""
    md_name = fname.replace('.pdf', '.md')
    md_path = os.path.join(papers_dir, md_name)
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(frontmatter + full_text)

    title = re.sub(r'\s*\[[a-f0-9]+\]\s*', '', fname.replace('.pdf', ''))
    print(f"[OK] {title[:80]} ({len(full_text)} chars)")
```

## Step 4: Categorize papers (for bulk ingest)

Use another code-execution pass to classify by keyword matching on titles, then
group into categories to plan which entity/concept pages to create.

## Key points

- **Always save both** the original `.pdf` AND the extracted `.md` in `raw/papers/`
- **The `.md` is the working copy** — read this for content extraction, but never modify it
- **SHA256 in frontmatter** covers the extracted text body only (not the frontmatter itself)
- **Use native Windows paths** (`<WIKI_PATH>\...`, your wiki root) in the current host's file tools, not bash paths
