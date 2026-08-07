# 批量下载参考文献（arXiv 等来源）

> **来源**：multimodal-wiki v1.0.0（kigner/multimodal-wiki）`references/bulk-arxiv-refs.md`，2026-08 融合。
> 用途：把论文引用的参考文献批量下载入库。原文档以 arXiv 为例（理工科预印本），
> 方法通用——知网/北大法宝等法学来源可套用同一"批量抓取→存 stub→后续补全"流程。

# Bulk arXiv Reference Download

When the user asks to download all papers that a wiki-ingested paper references,
or to populate `raw/papers/` with the bibliography of a key source, follow this workflow.

## Workflow

### 1. Locate arXiv IDs from the source paper's bibliography

The source paper's raw extract is in `raw/papers/<source>.md`. Read its references
section (usually the last ~300 lines). Each entry gives: author, title, venue, and
often an arXiv ID in the form `arXiv:YYMM.NNNNN`.

For any reference without an explicit arXiv ID, use the host's available scholarly-search or browser capability:
```
search_query=all:"<paper title keywords>"+<first author last name>
```

### 2. Batch-acquire with the available web/research capability

If the current host exposes `web_extract`, it can process arXiv PDF URLs in small batches; otherwise use the available browser/download workflow:
```
https://arxiv.org/pdf/<id>
```

If the tool returns summarized Markdown rather than the full text, treat it only as a discovery/index stub. It cannot support legal propositions, quotations, page references, or a `VERIFIED` source status; acquire and verify the primary document before using it as evidence.

### 3. Save stubs to raw/papers/

Each downloaded paper gets a stub `.md` file with:
```yaml
---
source_url: https://arxiv.org/abs/<id>
ingested: YYYY-MM-DD
arxiv_id: <id>
ref_label: <Paper Name> [<ref number from source>]
---
```

File naming convention:
```
<RefLabel> - <ShortTitle> [<arxiv_id>].md
```
For example: `Stable Diffusion [62] - High-Resolution Image Synthesis with Latent Diffusion [2112.10752].md`

**Note on content:** `web_extract` on arXiv PDFs returns LLM-summarized markdown
(since papers are typically >5000 chars). This is acceptable for reference indexing.
The full text is always available at the `source_url`. These stubs are NOT the same
as full paper extracts from local PDFs (which use pymupdf via [multimodal-pdf-extraction.md](multimodal-pdf-extraction.md)).

For CNKI, PKULaw and other licensed legal databases, use only the user's authorized access and preserve the official export/original file. Do not attempt to bypass authentication or paywalls.

### 4. Log the batch

Single log entry covering all downloaded papers, grouped by category:
```markdown
## [YYYY-MM-DD] ingest | <Source Paper> 引用论文 (arXiv 批量下载)
- 来源: <source paper> 论文参考文献列表
- 入库: raw/papers/ (N 篇 arXiv 论文)
- 论文清单:
  架构基座: ...
  方法前提: ...
  对比基线: ...
```

### 5. Not found handling

Some papers (conference-only, non-arXiv venues like SIGGRAPH) won't be on arXiv.
Note them explicitly in the log entry.

## When This is Triggered
- "把这篇论文引用的论文下载下来"
- "download all papers referenced by X"
- User points to a paper in the wiki and wants its bibliography ingested
