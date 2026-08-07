# Stub 重摄入（空壳源文件补全）— 多模态扩展

> **来源**：multimodal-wiki v1.0.0（kigner/multimodal-wiki）`references/reingest-stubs.md`，2026-08 融合。
> 法学库用法：批量抓取参考文献生成的空壳（只有 frontmatter 或占位符）按此流程补全。
> 与法学纪律一致：补全是 Ingest 动作，查询（Query）阶段不得补全；sha256 只算正文。

# Re-ingesting Stub Files

When a lint reveals placeholder stubs in `raw/papers/` (frontmatter only, no body text, or
`*Content extracted via web_extract — full text available at the source URL.*`), convert them
to real content with this workflow.

## 1. Identify stubs

Stubs are born from:
- **Bulk arXiv bibliography downloads** ([multimodal-bulk-refs.md](../../legal-research-wiki/references/multimodal-bulk-refs.md)): a web/research tool on
  `/pdf/` URLs returns LLM-summarized content that's often truncated. The raw note gets
  frontmatter + `sha256` but an empty or placeholder body.
- **Failed extractions**: `/abs/` returns metadata only; `/html/` often 404s.

Lint detection: `search_files` for files with `sha256` but fewer than ~5 non-frontmatter
body lines, plus the `*Content extracted via*` placeholder string.

## 2. Extract arXiv IDs from filenames

Stubs follow the naming convention:
```
<Author> [<refnum>] - <ShortTitle> [<arxiv_id>].md
```
Parse the `[<arxiv_id>]` suffix (e.g., `[2112.10752]`) from the filename.

## 3. Fetch real content

**URL priority order:**

| Priority | URL | Behaviour | When to use |
|----------|-----|-----------|-------------|
| 1st | `https://arxiv.org/pdf/<id>` | LLM-summarized markdown (~3-5K chars) | **Default — works for most papers** |
| 2nd | CVF open-access page | Full abstract + metadata | CVPR/ICCV/ECCV papers that fail `/pdf/` |
| 3rd | Available web search on blog/article | Third-party summaries | Discovery only; never legal evidence |

If the host exposes batch extraction, pass only a small set of `/pdf/` URLs per call; otherwise process them through the available browser/download workflow.

Example: 21 stubs → 5 batches of 5+5+5+4+2.

### CVF fallback pattern

For CVPR papers: `https://openaccess.thecvf.com/content_CVPR_<YEAR>/html/<Author>_<Title>_CVPR_<YEAR>_paper.html`

For ICCV: same pattern with `ICCV`.

This returns the abstract and metadata, sufficient for a reference-level summary.

### web_search fallback

When both URL formats fail, search for the paper title + "summary" or "explained":
```
web_search("<paper title> <first author> summary key contributions")
```
Record the top blog/article result only as a discovery lead. Do not replace a legal primary source with a third-party summary or mark the item fully ingested.

## 4. Write body content

Each stub gets a condensed summary covering:
- **Title, Authors, Venue/Year**
- **Abstract** (1-2 sentences)
- **Key Contributions** (bullet list)
- **Method** (core technical approach, 3-5 bullets)
- **Significance/Impact** (why it matters in the wiki's domain context)

Keep each summary scannable (~15-25 lines). The raw note is a reference index, not a replacement for reading the source. For legal propositions, quotations, case numbers, statutory text, dates and page references, the official or authorized primary document must be acquired and verified first.

## 5. Update sha256 and write

Use the current host's code-execution facility to batch-process:
```python
import hashlib, re, os

# For each stub file:
# 1. Read current content, extract frontmatter
# 2. Replace body with new content
# 3. Recompute sha256 over body only
# 4. Update sha256 in frontmatter: sha256: <new_hash>
# 5. Write file

sha = hashlib.sha256(new_body.encode('utf-8')).hexdigest()
new_content = re.sub(r'sha256:.*', f'sha256: {sha}', new_content)
```

**Do NOT recompute sha256 over frontmatter + body** — only the body. This matches the
original ingest convention and prevents false drift detection.

## 6. Log the re-ingest

Single log entry covering the batch, grouped by category:

```markdown
## [YYYY-MM-DD] ingest | 重新摄入 N 篇 arXiv 引用论文存根
- 来源: [date] <original batch> 的 N 个存根
- 方法: web_extract /pdf/ + CVF 补充
- 类别分组:
  基础架构 (M): paper1, paper2, ...
  方法前提 (M): paper3, ...
- 更新: raw/papers/ 中 N 个 .md 文件（正文替换 + sha256 重算）
- 验证: N/N 全部通过（body 行数 M-N，sha256 已重算）
```

## Pitfalls

- **`/abs/` is useless for content** — it only returns the arXiv landing page (navigation,
  submission history, bibtex). Never use it for re-ingest; go straight to `/pdf/`.
- **`/html/` often 404s** — arXiv HTML rendering is inconsistent. Don't spend time
  debugging 404s; fall through to web_search.
- **sha256 must be body-only** — recomputing over frontmatter + body creates a different
  hash than the original ingest, triggering false drift in future lints.
- **Batch writes** — for many files, use the current host's code-execution facility with an explicit Wiki root, a backup, and a dry-run/preview before changing the batch.
- **Do NOT create new Layer-2 pages during re-ingest** — these papers already have
  entity/concept pages. Re-ingest only updates the raw source, not the wiki layer.
