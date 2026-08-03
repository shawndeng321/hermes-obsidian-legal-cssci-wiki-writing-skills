# Session 2026-07-31 — Research-Design Page Upgrade (研究设计页升级)

Context: after merging cssci-paper-writing (五问框架) into chinese-law-paper-writing
v3.0.0, the user asked to audit the wiki's 写作思路 pages (research-design + methodology
concept pages) against the merged skill, report whether improvements were needed,
then execute them step by step.

## What the audit found (report-first, then execute)

Overall: skeleton was good — 五问框架 fully applied, cross-reference network healthy
(15 concept pages + 25 papers link back to the research-design page), 0 dead links.
Gaps were execution-tool and freshness issues, not structural.

### Priority findings (4 executed)

1. **Q4 素材清单 stale** — status column contradicted log.md/raw/:
   - "最高法参考10个文件 ⬜ 待摄入" was wrong: 53-case compilation ingested 07-30,
     4 reference DOCX archives used for case-page updates 07-31
   - "53个权威案例 ✅ raw/cases/（目录已建）" — wrong location; case pages live in
     entities/案例/ (53 pages); raw/cases/ holds the source DOCX
   - Missing entry: 最高检指导性案例 (检例205/236/237, partially used; 检例237 irrelevant)
   - Fix: rewrite table with real statuses + ingestion dates + exact file names
     (verified via `ls raw/cases/` first — 5 DOCX total)
2. **论点—证据—引注矩阵 missing** — created `research-design/工伤认定群案论点证据引注矩阵.md`:
   - Per-dimension matrix: 子主张 | 证据类型 | 具体证据 | 支持范围 | 反方材料 | 核验状态
   - 13 sub-claims across 3 dimensions; statistics rows marked `待核`/`缺证据`
     until 121案 compilation is ingested; literature positions marked VERIFIED
   - 6-item 统计口径清单 (待定稿): 年代切片认定率 (2003-2010/2011-2016/2017-2024),
     改判率定义 (撤销+变更? 含发回重审?), 行政机关问题类型分布, 法条引用频率变迁,
     撤诉/放弃比例, 裁判理由分化度
3. **样本选取标准 missing** — added 三层样本结构 table: 权威样本 (53 最高法案例,
   官方汇编收录即入选), 统计样本 (121案编译集, criteria 待核 until ingestion),
   补充样本 (裁判文书网按需). Plus 双样本结构 rationale answering 样本偏斜 criticism.
4. **资料截止日期 + 五项硬门禁状态表 missing** — added: 案例数据截止 [待定],
   《工伤保险条例》2010修订版 (国务院令第586号) + 法释〔2014〕9号 verified as current,
   25 papers verified via log; gate table with ✅/⚠️ per gate + next step.

### Optional findings (deferred, user decides)

5. 学术史争议地图 page (three controversies: 举证责任三说/不确定概念解释/立法模式选择)
6. Methodology concept page sync with skill v3.0.0 (task modes, 待核标记体系)

## Key techniques

### Verify Q4/material status against ground truth before editing

`ls raw/cases/` + log.md entries + `grep -o "维度[一二三]" entities/案例/*.md` for
dimension distribution. Never rewrite a status table from memory of past sessions.

### Case-page dimension tags are boilerplate

All 53 case pages contain generic 维度一/二/三 sections (template-like text). They
cannot be used as precise claim→case evidence mapping without reading each 裁判要旨.
The matrix therefore cites papers (verified positions) + landmark cases (何文良案,
王明德案/指导案例69号) with 待核 status on the specific statistical claim.

### Log append ordering

log.md had entries appended by a parallel session ("引用文献Wiki第一批修复").
My entry was inserted before it; fixed by removing and re-appending at true EOF.
Always `read_file` the log tail before appending.

### Verification after upgrade

- Dead-link check on both modified/new pages: 23 links + 24 links, 0 dead
- index.md page count updated (98→99), frontmatter `updated:` bumped to 2026-07-31
- log.md entry at true end with verification results included

## Follow-up state

- 121案编译集 remains the top pending ingestion; after it: fill matrix statistics
  rows per 统计口径清单, flip 待核 → VERIFIED, finalize 样本选取标准 待核 fields,
  set 案例数据截止 date, and (optionally) build the 学术史争议地图 page.
