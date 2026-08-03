# Session Lessons: 2026-07-30

## New Wiki Initialization (Second Build)

User wiped the old wiki (`~/Desktop/法学研究wiki/`) and rebuilt from scratch at
`~/Desktop/法学wiki/工伤认定群案研究Wiki/`. The rebuild followed the correct sequence:

1. CSSCI methodology → concept page ✅
2. Research design asked → written to research-design/ ✅
3. Paper ingestion (pending)
4. Case ingestion (pending)

The cssci-paper-writing skill's mandatory init sequence worked correctly.

## Paper-Before-Case Ingestion Order

User asked whether to ingest papers or cases first. Recommendation: **papers first**.

Rationale:
- Papers build the concept skeleton; cases fill in empirical flesh
- Without concept pages, case entity pages have nothing to link to → become orphan islands
- Papers reveal which dimensions matter for tagging → prevents tag rework
- Academic history (维度二) needs literature base before cases are analyzed

User agreed. This should be the default recommendation for future group case research wikis.

## Parallel PDF Extraction with delegate_task

For 25 papers, used 3 parallel `delegate_task` subagents (8+8+9 papers each).
Each subagent:
1. Uses pymupdf to extract text from PDFs (first 10 pages usually sufficient)
2. Outputs structured JSON to /tmp/batchN_papers.json
3. Fields: filename, title, author, affiliation, journal, year, abstract, keywords,
   key_arguments (3-5 detailed points), methodology, conclusions, cases_cited,
   statutes_cited, concepts

This is faster than serial extraction and keeps the main context clean.
After subagents complete, main agent reads JSON files and writes wiki pages.

**Key**: subagent JSON schema for papers should include `cases_cited`, `statutes_cited`,
and `concepts` fields — these are essential for cross-linking wiki pages.

## Journal Style Template Ingestion

Before ingesting reference papers, user wanted to ingest 3 sample papers from the
target journal (《政治与法律》) to learn house style.

Created a concept page analyzing:
- Format specs (字数, 摘要, 关键词, 脚注, 中图分类号)
- Writing style (实证数据切入, 类型化分析, 案例分组引用)
- Relevance to the group case research

This "style template" step should be added to the workflow when the user has a
specific target journal. It goes AFTER research design but BEFORE paper ingestion.

## Updated Ingestion Sequence

For group case research wiki with target journal:

1. CSSCI methodology → concept page
2. Ask research design → research-design page
3. Journal style templates (3 sample papers from target journal) → concept page + entity pages
4. Reference papers (literature review) → entity pages + concept pages
5. Cases → entity pages (linked to concepts from steps 3-4)
6. Paper draft

## User Persona Details

- User.s name: Shawn Deng (author of the 检例205号 paper)
- Target journal: 《政治与法律》(CSSCI)
- The 检例205号 paper is the "seed" — to be expanded into a group case research article
- Three-dimension framework: 裁判方法变迁 → 法律适用演变 → 行政与司法张力
