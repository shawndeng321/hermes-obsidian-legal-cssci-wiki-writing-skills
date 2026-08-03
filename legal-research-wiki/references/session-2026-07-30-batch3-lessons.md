# Session Lessons: 2026-07-30 Batch 3 (25-paper ingestion)

## Overview

Full 25-paper ingestion into `~/Desktop/法学wiki/工伤认定群案研究Wiki/`.
Wiki grew from 9 pages (research design + methodology + journal templates + seed paper)
to 40 pages (1 research design + 10 concepts + 29 entities).

## delegate_task Subagent JSON Failure

Dispatched 3 parallel subagents (8+8+9 papers). Two completed and wrote JSON
to `/tmp/batch2_papers.json` and `/tmp/batch3_papers.json`. The third
(batch1, 8 papers) reported "completed" but **no JSON file was produced**.

- `ls -la /tmp/batch1_papers.json` → "No such file or directory"
- `process(action='poll', session_id='deleg_b7c70055')` → "not_found"
- `process(action='list')` → empty (subagent had already exited)

**Fix**: Wrote a standalone extraction script to `/tmp/extract_batch1.py` using
pymupdf + regex, ran it with `terminal()`, and got results in one shot. This
was faster than re-dispatching a subagent.

Lesson: always verify subagent output files exist before proceeding. If missing,
fall back to direct script execution — do NOT waste time re-dispatching.

## pymupdf Metadata Quality Issues

Auto-extracted metadata from PDFs was unreliable for batch 1:

| Paper (from filename) | Auto-extracted title | Actual title |
|---|---|---|
| 王东伟_举证责任 | "Evidence Science Vol.24 No.1 2016" | 论工伤认定行政诉讼案件中的举证责任 |
| 杨曙光_举证责任 | "法学杂志·2017年第12期" | 论工伤行政诉讼的举证责任 |
| 谭秋勤_不确定法律概念 | "【法学与法制建设】" | 工伤认定行政案件中不确定法律概念... |
| 王东伟_司法审查 | "第29卷第4期" | 工伤认定行为的司法审查研究 |

**Fix**: Created a manual `corrections` list with ground-truth title/author/
affiliation/journal/year for each paper, derived from the filename pattern
`标题_作者.pdf`. Used auto-extracted data only for abstract, keywords,
section headings, and statutes.

## Inline Python Quote Nesting Failure

Attempts to run pymupdf extraction via `execute_code` with inline `python3 -c`
commands failed repeatedly due to quote nesting (Chinese filenames + f-strings
+ shell quoting).

**Fix**: Write the script to a file (`write_file("/tmp/extract_batch1.py")`),
then run with `terminal("python3 /tmp/extract_batch1.py")`. This is already
documented in the skill but was bypassed — reinforce: **always use script
files, never inline `python3 -c` for complex extraction**.

## Concept Page Generation from Paper Themes

After creating 25 paper entity pages, identified 6 new concept pages that
emerged from the literature:

1. 新就业形态劳动者职业伤害保障 — from 5 papers on platform worker injury
2. 工作时间的功能主义解构 — from 沈建峰's functionalist analysis
3. 上下班途中合理时间的认定边界 — from 艾琳's empirical study
4. 工伤认定中的不确定法律概念 — from 谭秋勤 + 王东伟
5. 工伤认定一般条款与列举模式 — from 郑晓珊 + 侯玲玲 + 胡京 + 葛翔
6. 工伤认定中的程序性问题 — from 谭金可 + 李超 + 莫良元 + 王敏

Pattern: each cluster of 3-5 papers on a related theme → 1 concept page
synthesizing their contributions, debates, and cross-references.

## User's Seed Paper as Concept Source

The user's own paper (检例205号案例分析) was ingested first and produced
2 concept pages (举证责任三层规范体系, 检察跟进监督制度) that became anchor
concepts for the entire wiki. When other papers were ingested, they were
cross-linked to these concepts. This "seed paper first" approach worked well
for establishing the conceptual framework before literature review.

## Wiki Page Size Targets

Observed page sizes that produced good content:
- Entity pages (papers): 2,000-7,000 bytes (sweet spot ~5,000)
- Entity pages (seed paper): 10,000+ bytes (detailed case analysis)
- Concept pages: 2,700-5,500 bytes (sweet spot ~3,500)
- Pages under 1,500 bytes were too thin and required enrichment

## Overlap Note

The research category has significant skill overlap:
- `legal-research-wiki` (most comprehensive umbrella)
- `chinese-law-llm-wiki`
- `legal-case-research-wiki`
- `gongshang-qunan-yanjiu`
- `group-case-enrichment`
- `wiki-content-completeness`
- `cssci-paper-writing`

Recommend consolidating into 2-3 class-level skills. `legal-research-wiki`
is the natural umbrella; `cssci-paper-writing` and `wiki-content-completeness`
serve distinct functions and could remain standalone. The others should be
merged into `legal-research-wiki` as reference files.
