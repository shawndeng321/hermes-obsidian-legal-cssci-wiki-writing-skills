# Literature Wiki Audit and Repair (2026-07-31)

This reference records a reusable audit pattern discovered while reviewing a 25-paper Chinese legal-research wiki. It is not a completion log; use it as a defect catalog and acceptance checklist.

## Audit in four passes

1. **Inventory and provenance**
   - Enumerate `entities/引用文献/*.md`, `raw/papers/*.pdf`, `entities/范文/*.md`, and `index.md` independently.
   - Map every `sources:` value to an existing raw PDF.
   - Explain extra raw PDFs before calling them missing sources; style-template PDFs may intentionally live in `entities/范文/` rather than `entities/引用文献/`.
   - Treat the PDF as immutable evidence. Do not infer metadata from the wiki filename alone.

2. **Structure and substance**
   - Check YAML, title/filename, author list, journal, year, issue, pages, DOI, tags, confidence, and section headings.
   - Check section *meaning*, not only character count. A 1,900-character “主要结论” can still be wrong if it is a numbered body section; a 500-character conclusion can still be defective if it starts mid-sentence.
   - Require a source-grounded audit of `摘要`, `核心论点`, `研究方法`, and `主要结论`. If the source has no explicit method or conclusion, state that status rather than inventing one.

3. **Links and graph integrity**
   - Scan all wikilinks against the complete vault, including the vault root; distinguish real dead links from documentation examples and historical log references.
   - Check both directions: paper → anchor draft, anchor draft → paper, paper ↔ paper, paper → existing case, and case → paper.
   - A plain case name in `引用案例` is not a wikilink. Map only to an existing, correctly identified case page; keep foreign, unbuilt, or merely mentioned cases as plain text until an explicit mapping/new-page decision exists.
   - Require the anchor draft to link back to every paper it actually uses. Report coverage counts, not just a binary “links exist”.

4. **Citation precision and presentation**
   - In `引用规范`, distinguish exact statutory support from a background mention of an entire instrument. Add article numbers only when the PDF/page explicitly supports them; never fill them by inference.
   - Normalize article notation (`第14条、第15条` rather than mixed shorthand) while preserving款/项 when the source provides them.
   - Check blank lines after every `##` heading, clean keywords, and remove PDF residues.
   - Run the full quality report once after all repairs; do not announce completion after fixing only links, only metadata, or only conclusions.

## High-risk defect patterns

- **Metadata false confidence:** all pages may say `confidence: high` while affiliation, co-authors, journal name, or issue/page data are wrong. Read the first page/DOI and maintain a manual correction table.
- **Wrong conclusion section:** extraction may select a numbered body section such as `四、……` instead of the author’s conclusion, `余论`, or final substantive paragraph.
- **Fragmented conclusion:** a conclusion beginning with `是……`, `，……`, or another sentence continuation is not acceptable even when it exceeds the length threshold.
- **Inline section markers:** source layouts may place `裁判理由：` or `裁判要旨：` in the middle of a paragraph. The parser must split inline markers before assigning facts/reason/gist.
- **False “missing source”:** raw directories can contain style templates or other intentionally separated source classes. Resolve the page-to-source map before reporting omissions.
- **One-way graph illusion:** paper pages may contain rich prose about the draft while using malformed text such as `标题|底稿` outside `[[...]]`; visually readable prose is not a navigable graph edge.

## Acceptance report template

Report these separately:

- page count, source count, extra/template source count;
- substantive-page and section-completeness results;
- exact metadata defects verified against source PDFs;
- conclusion/method extraction defects;
- dead links, with documentation/history false positives separated;
- paper↔draft, paper↔paper, paper↔case, and case↔paper coverage;
- statute bullets needing article-level review;
- format-only issues;
- “must fix / should improve / defer” recommendations.

Do not silently rewrite a whole literature corpus after this audit. First produce a scope and mapping list, then repair a small, source-verifiable batch; re-run the complete acceptance report before expanding the batch.
