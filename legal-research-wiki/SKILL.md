---
name: legal-research-wiki
description: Use when building a Chinese legal research wiki.
license: MIT
metadata:
  version: "3.0.0"
---

# Legal Research Wiki

Build and maintain an LLM Wiki for legal academic research, especially administrative law
group case studies and paper writing. Extends the general `llm-wiki` skill with
legal-domain conventions, scope-first ingest discipline, and batch processing patterns.

## Model-Orchestrated Legal Research

For multi-model Wiki-to-paper workflows, keep the process model-agnostic:

- **Skills own sequence and quality gates; models occupy replaceable capability slots.**
- Use single models for high-volume extraction, formatting, graph maintenance, Chinese drafting, and tool-heavy data work.
- Use MoA only at high-value decision gates: research planning, difficult sections, substantive audit, and journal adaptation.
- Enforce a **single-writer rule** per artifact. Reviewers produce issue lists or constraints; they do not silently rewrite the same file.
- Normalize multimodal sources into page-cited source packets before handing them to a Chinese legal-writing model.
- Store current provider/model mappings in a separate role registry and benchmark replacements before promotion; never hard-code today's model names as permanent workflow rules.

See `references/model-orchestrated-legal-research-workflow.md` for role slots, Wiki and paper-writing stage maps, Hermes MoA boundaries, handoff contracts, update benchmarks, and a dated example mapping.

## When to Use

Use this skill alongside `llm-wiki` when:
- Building a legal knowledge base for academic paper writing
- Ingesting judgment documents (.docx), PDF papers, or court materials
- Working with Chinese legal sources
- Group case study methodology integrated into the wiki
- 20+ source files and need controlled, scoped ingestion

## Core Principle: Scope Before Speed

The #1 pitfall for legal wiki work is ingesting too much at once without user visibility.

Legal users curate sources carefully. When the user provides a directory with many files:

1. Survey first: list what's there, count files, identify sub-groupings
2. Discuss 1-2 representative sources: extract and show takeaways before proceeding
3. Ask for scope: let the user steer
4. Process in batches: even when user says "all", break into thematic batches

Never silently process 25+ files without the user knowing what's happening.

## Batch PDF Extraction

Don't run inline Python in terminal(). Write the extraction script to /tmp/ first:

1. write_file the script to /tmp/extract_papers.py
2. terminal("python3 /tmp/extract_papers.py '/path/to/papers'")
3. Script uses pymupdf, saves companion .txt files

See scripts/batch_extract_papers.py for the reusable template.

marker-pdf is needed only for scanned/image-based PDFs (OCR). Most academic PDFs
from CNKI are text-based and work with pymupdf alone.

## Duplicate Detection

Source directories often contain (1).pdf copies. Before treating as separate sources:

```bash
diff file.pdf "file(1).pdf"
shasum -a 256 file.pdf "file(1).pdf"
```

Report duplicates to the user instead of silently filtering.

## Chinese Legal Materials

### Legacy .doc extraction (macOS textutil)

User-supplied statute files are often legacy `.doc` (Composite Document File V2), which `python-docx` CANNOT read. On macOS, extract with textutil (no install needed):

```bash
textutil -convert txt -stdout "工伤保险条例（2010修订）....doc" > /tmp/tiaoli.txt
```

Then parse the .txt with grep/regex (`^第.*条` finds article boundaries; `grep -n` locates chapter sections like 第四章工伤保险). Aspose-generated .doc files contain `HYPERLINK "https://..."` noise lines — strip or ignore them. Save the original .doc to `raw/法规范/` for traceability alongside the wiki page.

### Document types and wiki mapping

Judgment docs (.docx) go to raw/cases/ and become entities/ pages.
Academic papers (.pdf) go to raw/papers/ and become entities/ pages.
Judicial interpretations go to raw/supreme-court/ and become concepts/.
Analysis reports go to raw/reports/ and become comparisons/.

## Norm Layer Ingestion (法规范层摄入：批复/答复/会议纪要/审判答疑)

When the user supplies 最高法批复答复汇编/司法解释/会议纪要/审判答疑 materials, do NOT bulk-ingest. **User-mandated order: 先排查相关性 → 专门摄入 → 分类由AI设计（用户确认后执行）**. Reuse the same scan-first discipline as case compilations:

1. **Scan first**: parse the DOCX, extract the full TOC (目录), then scan ALL body paragraphs for keyword hits (工伤/劳动/保险/职工) — TOC alone misses Q&A-style items embedded mid-document (e.g. 在家加班48小时问答藏在正文后部). Record 文号/日期 per hit.
2. **Classify by relevance to the research design**: 直接相关 (maps to an analysis dimension / comparison page / 底稿 claim), 次相关, 背景性 (old-law regime, tangential). Report the tiered list to the user before building pages.
3. **Design classification by 争点主题, not by document chronology**: group replies into themed pages (e.g. 劳动关系与工伤认定主体 / 超龄劳动者 / 上下班途中与排除规则 / 因工外出与工作原因 / 视同工伤与救助行为 / 时间效力与新旧法衔接).
4. **Page format** (user-approved): 文号/日期/性质 → 批复原文（全文引文）→ 请示背景摘要 → 规范要点 → 与群案研究的关联（wikilinks to 案例/比较页/概念页/底稿）→ 相关页面. YAML gets a **`规范层级`** field (法律/行政法规/司法解释/批复答复/规章).
5. **Directory structure** (user-approved, **7 tiers ordered by 法的效力层级, NOT 5 — user corrected 2026-08: 法律与行政法规必须分开，法律是上位法；司法解释在部门规章之上**): `entities/法规范/1. 法律/`, `2. 行政法规/`, `3. 司法解释/`, `4. 部门规章/`, `5. 批复答复/`, `6. 会议纪要/`, `7. 审判答疑/` — keep empty tiers as placeholders so future materials slot in. **The tier number IS the authority rank** (upper law first); when citing, look from the top down — same issue with an upper-law provision beats a lower one. **司法解释 vs 部门规章位阶 (user asked "哪个上位", 2026-08): 司法解释上位** — 司法解释是最高法对法律的解释（如法释〔2014〕9号解释《社会保险法》《工伤保险条例》），是**裁判依据**，法院判案必须遵循；部门规章（如《工伤认定办法》）在行政诉讼中仅"参照"（《行政诉讼法》第63条），法院可不用。SCHEMA type adds `norm`; renumber existing subdirectories when a new tier splits an old one (e.g. old `1. 行政法规与法律/` → `1. 法律/`+`2. 行政法规/`+`3. 部门规章/`, shifting 司法解释→3, 部门规章→4, 批复答复→5, 会议纪要→6, 审判答疑→7; wikilinks are filename-based so moves don't break links).
6. **Background items**: do NOT build pages — copy the source DOCX to `raw/法规范/` for traceability and say so explicitly.
7. **Every page links its normative basis back into the corpus** — e.g. 行他10号 → [[超龄劳动者工伤认定案例比较]]; 行他236号 (死因不明→认定工伤) is direct statutory support for 底稿's 三层规范体系; 行他2号 (非工作原因救助不视同) is the boundary counterpart of 案例62 救助工友案.
8. **Authority tiers differ — encode them in the page**: 批复 = formal 司法解释 form (citable as normative basis); 答复 = 司法文件/准司法解释; **会议纪要 and 审判答疑 = 审判业务指导文件, NOT formal sources — page must carry a top 性质说明 block stating they cannot be cited as 裁判依据, only as 裁判倾向佐证** (user explicitly asked "会议纪要应该算什么呢"). 论文引用铁律: 有正式司法解释不引批复；会议纪要/答疑只作"最高法亦持此立场"式佐证。

For the authority hierarchy, 批复 vs 答复 distinction, 会议纪要/审判答疑 citation rules, and the 会议纪要(6条)/审判答疑(10问→3页) ingest records, see `references/legal-norm-hierarchy-and-reply-ingestion.md`.

## Draft Ingestion (论文初稿摄入 — user rule 2026-08-03)

When the user provides their own paper draft (初稿) — e.g. 《3.0初稿》21874字 docx — the ingest rule is **reference-only, not a research target** (user: "只是让你知道我写了啥，但是还不能作为研究的标靶，因为肯定还要根据这扩展的知识库做修改"):

1. **Store in `drafts/` (草稿文件夹)**, NOT `entities/`: keep both the original .docx AND a readable .md conversion (`textutil`/python-docx → `/drafts/N.0初稿-标题.md`). The folder is excluded from formal page counts, index lists it under a `## Drafts` section explicitly marked 非正式页面、不入正式计数.
2. **CRITICAL: extract footnotes too — python-docx `paragraphs` DOES NOT include footnotes.** A draft's citation apparatus (案例脚注带案号/文献脚注带页码) lives in `word/footnotes.xml` inside the docx zip. Reading only `d.paragraphs` silently drops all 42 footnotes (observed: 3.0初稿 22055 chars body + 42 footnotes, 26 of them case citations with full 案号). Extraction recipe + body-position marking: `references/docx-footnote-extraction.md`. After converting any 初稿/论文 docx, ALWAYS verify `zipfile` contains `word/footnotes.xml` and extract it — footnote info is exactly what the user will ask about ("你能正常读到我的脚注吗").
2. **No YAML type=entity, no tags, no wikilink expansion, no footnote/引注 marking** on the draft itself — it is a read-only historical artifact. (Never annotate cases/footnotes from a draft without the user handing over the final text.)
3. **Also ingest the user's 论文思路/research-outline file** (e.g. 论文思路.docx) into drafts/ — it is the 行文思路源文件 (e.g. 发现问题—解释转型—构造标准—保障适用) and drives outline writing later.
4. **Record the draft's core thesis in research-design/** (e.g. 3.0初稿核心命题="从'三工要素'形式符合判断转向职业风险归属实质判断", 三阶判断) plus the relationship note: 初稿是写作历史参考不是标靶; 大纲阶段流程="AI读库→从头写大纲→与初稿对比修改".
5. **Case-usage configuration (案例用量) belongs in research-design**, derived from journal style + word count (e.g. 《政治与法律》风格=案例分组归纳/实证数据切入 → 正文详析10 + 脚注25 + 统计121全部; 类型化覆盖每争点2-3案, 权威优先), with the final 详析 list deferred to outline stage after AI reads the vault.
6. **初稿脚注↔知识库案号匹配（2026-08-03，11/11成功）**: build a `queries/` 对照页 mapping draft footnote numbers → 案号 → case wikilinks (供改稿追溯; 用户提醒: 初稿案例≠最终必用, 最终以大纲阶段类型化覆盖为准). **案号匹配纪律**: match on the FULL case number (年份+行政区划代码+字号, e.g. `（2019）苏0903行初209号`), NEVER year-only — a bare year like "2019" matches multiple cases and produces massive false positives. Handle BOTH 全角`（）` and 半角`()` parentheses (one case page stored half-width brackets, causing a miss until both were tried). Extraction regex: `re.findall(r'（(20\d{2})）([^，。；]*?号)', t)` then compare `full in c or c in full` against the case page's `案号**：` field; normalize spaces before comparing.

## Statute/法规 Ingestion (法条摄入：法律/行政法规/部门规章)

When the user supplies statute texts (《工伤保险条例》《社会保险法》《工伤认定办法》 etc.), ingest into the matching tier of `entities/法规范/` — **tier is determined by 制定机关/效力位阶, never by content convenience**:

1. **Tier assignment** (user-corrected 2026-08, 引用时权威性排序):
   - `1. 法律/` — 全国人大及其常委会制定（《社会保险法》《劳动法》《行政诉讼法》）
   - `2. 行政法规/` — 国务院制定（《工伤保险条例》）
   - `3. 司法解释/` — 最高法/最高检（法释〔2014〕9号）
   - `4. 部门规章/` — 国务院部门制定（《工伤认定办法》人社部令；人社部发〔2013〕34号意见属"其他规范性文件"，如无独立层级可归入本层并标注）
   - `5. 批复答复/` `6. 会议纪要/` `7. 审判答疑/` — 见上
   - **位阶理由必须写进页面**：司法解释=裁判依据（法院必须遵循）；部门规章仅"参照"（行政诉讼法第63条）。论文引用铁律：同一问题有上位法不引下位法。
2. **Page granularity**: 一部法规=一页（如《工伤保险条例》一页、条文分节）；**只摄入与研究设计相关的条文节**（如《条例》第14/15/16/19/64条），不全文照搬无关章节 — 页面聚焦"与群案研究的关联"。
3. **Page format** (per statute): 规范层级/制定机关/现行版本(修订时间) → 条文节选（逐条原文，blockquote）→ 每条规范要点 → 与群案研究的关联（wikilinks到案例/比较页/概念页/底稿）→ 相关页面。
4. **条文级链接纪律**: 页面间引用法条用 `[[页面名#第14条]]` 锚点形式（如比较页引用《工伤保险条例》第14条）；SCHEMA 引用规范字段保持"第X条"级别（用户2026-08确认：条文号到"第xx条"级别即可，不写项/款）。
5. **现行版本标注**: YAML 加 `现行版本` 字段（如"2010年修订"），防止未来引用失效版本（如《条例》2011.1.1施行的修订版）。
6. **来源说明**: 法条原文来自用户提供的法规文本/官方发布，非网络转述——sources 记录文件路径；如来自汇编（如司法解释汇编DOCX）标注原文出处。
7. **相关性过滤（user decision 2026-08-03）**: when a batch of laws is supplied (e.g. 5 administrative laws), propose a 关联强/关联弱 tiering BEFORE ingesting — strong-relevance laws get pages, **weak-relevance laws are SKIPPED entirely, not ingested as thin pages** (工伤认定 project: 行诉法/复议法/强制法 ingested; 行政处罚法/行政许可法 skipped because 工伤认定 is neither a penalty nor a license act). The 底稿三层体系's first layer (行诉法第34条) is a strong relevance anchor.
8. **官方原文核验（2026-08-03）**: when the user later supplies the OFFICIAL full text of a regulation already ingested from a compilation, VERIFY article completeness against the official text — the compilation-derived 法释〔2014〕9号 page was missing 第10条 (新旧司法解释衔接条款). Add missing articles + record the official source; the official .doc goes to `raw/法规范/`.
9. **条文号数字统一（2026-08-03, user-flagged defect）**: mixing 中文数字 (第四条) and 阿拉伯数字 (第4条) for the same statute across pages is a defect the user flags ("第四条和第4条就是一个"). Normalize formal pages (entities/concepts/comparisons/queries/research-design) to **中文数字** (`第四条`); do NOT rewrite log.md/台账 historical records. Direction confirmed; 项/款 digit style and table quick-reference style pending user decision — when normalizing, only touch `第N条` patterns, keep 项/款 structure intact.

### Tag taxonomy

Customize SCHEMA.md with tags for: 行政行为类型, 审查要点, 裁判结果, 法院层级, and meta tags
like comparison, controversy, 通说, 少数意见.

### 引用文献主题分类（paper pages, user-approved 2026-08）

25篇引用文献按研究主题分6类，tags第二项为主题标签（Graph View按主题分组）：
`举证责任与司法审查`（王东伟×2/杨曙光/梁琼芳）、`认定要件解释`（郑晓珊/胡京/沈建峰/艾琳-上下班/谭秋勤/黄辉/葛翔/杜强强）、`排除规则与立法构想`（侯玲玲/郑尚元/黎建飞）、`新就业形态`（战东升/李满奎/杨思斌/马孟琛/艾琳-平台）、`程序问题`（谭金可/王敏/李超/莫良元）、`检察监督`（张相军）。分类依据=论文核心论点主题（对应研究设计维度），批量用regex替换 `tags:\n- 工伤认定` → `tags:\n- 工伤认定\n- <主题>`。

### Concept-page-first approach

Prioritize concept pages over entity pages for academic legal wikis.
Each paper typically triggers 2-3 concept page updates.
Group case research benefits most from comparisons/ pages.

## Case Classification by Citation Usability (案例三层分类 — 项目特定约定，非通用规则)

> **适用性警示（用户2026-08确认）**：三层分类（核心/辅助/参考）是**工伤认定项目约定示例**，因该论文的引注规范（有无案号决定能否进脚注）而设计。**新项目不得默认套用**——摄入案例前必须先问用户：这些案例用于什么研究/写什么文章（如"实证统计型"vs"类型化分析型"vs"个案释评型"），再按研究需要重新设计分类。

When a case corpus mixes authoritative cases (公报/指导案例, full judgment texts) with brief typical-case summaries (典型案例 without 案号), classify by **citation usability** — this is what the user actually needs for paper writing (工伤认定项目示例):

- **核心案例/**: complete authoritative cases + material-rich cases (even without 案号 — material depth supports research; 无案号 only affects footnote format, not research value). Priority for citation.
- **辅助案例/**: cases WITH complete 案号 but medium/light material. Citable as supplements.
- **参考案例/**: typical cases without 案号. Reference only — cannot be formally cited in a law paper footnote; treat as 裁判观点参考.

Classification rule of thumb: 材料丰富度 determines research value; 有无案号 determines citation ability. Ask the user whether material-rich-but-no-案号 cases go 核心 or 参考 — they usually go 核心.

**摄入前询问流程（MANDATORY for new projects）**: before designing case classification for any NEW research project, ask the user (in plain language): ①这批案例要支撑什么研究问题/什么类型的文章（实证统计/类型化分析/个案释评）？②案例数量规模？③有无引注约束（是否要求案号）？Then propose a classification design for user confirmation — never reuse the 三层分类 silently.

**编号纪律（用户2026-08确认）**: numbering goes in **FILE NAMES** (`案例N-标题.md`, N global continuous across tiers: 核心1-62, 辅助63-79, 参考80-121), NOT in page titles. The user wants to flip through files sorted by number in Obsidian's file browser. Page titles stay title-only; the numeric ID lives in YAML `case_id` (kept consistent with filename number AND source-compilation sequence for traceability). Global continuous numbering avoids three "案例1" collisions breaking Obsidian filename-based wikilinks. Moving files between subfolders does NOT break links (Obsidian resolves by filename); renaming requires vault-wide link replacement.

**年份入文件名（CASE-YEAR-RENAME 2026-08）**: filename format is `案例N-YYYY-标题.md` (year after the number: `案例1-2003-何文良…`), so the file browser shows time span at a glance and number order ≈ time order. Year source hierarchy (never fabricate): ① compilation sort date (最后生效裁判日期 — matches the global numbering order; NOT the page's 裁判日期 field which is the first-instance year and can disagree with ordering) ② same-series inference (e.g. 典型案例 siblings share the release year — 案例120/121 inferred 2023 from 案例102's same 昌平 series) ③ no evidence → `案例N-年份不详-标题.md` (4/121 cases had zero clues; mark honestly, do not guess). **Batch link replacement after rename MUST cover ALL FOUR link forms**: `[[旧]]`, `[[旧|别名]]`, `[[旧.md]]`, and **`[[旧&#124;别名]]` (table-alias form)** — missing the `&#124;` form produced 19 real dead links in comparisons/ tables in one pass. Verify with a recursive dead-link scan after every rename, excluding maintenance/log/SCHEMA false positives. Also archive any 0-byte `&`-suffix ghost files (Obsidian creates `案例N-…&.md` when a link with `&` is clicked) to `.maintenance/ghosts/`.

### Case Ingestion Batch Strategy（案例摄入批量策略）

**摄入与关联的时序纪律（2026-08更新，AUDIT-BATCH5教训）**：

- **模块化批次**：以"主题完整"为模块边界（如121案例=1模块、25篇论文=1模块）。**一个模块摄入必须全部完成，才做该模块的关联**——半途关联必然返工（早期129条"相关论文"链接因案例库未补全，核验后70%不真实被删除）。
- **关联后立即核验**：每完成一次关联操作（论文↔案例/案例↔法规范/任何双向链接），必须立即跑全库验收：未解析链接0、双向对称、无纯链接残留（所有链接须带印证理由）、理由字数达标。**不核验不进入下一模块**。
- **增量关联**：新模块摄入后，只做"新页面↔已有页面"的增量关联，然后**再核验一次**。
- **旧链接程序化核验**：任何早期/批量生成的"相关"链接，使用前必须逐条核验（案例裁判要旨↔论文核心论点的真实印证/支撑/反衬关系，同主题泛泛相关不算）——**不得假定旧链接真实**。

**批量法条/法规名→wikilink替换（AUDIT-BATCH6教训）**：把正文`《工伤保险条例》`批量替换为`[[工伤保险条例（2010修订）|工伤保险条例]]`时，**已链接页面会被二次替换产生嵌套**（`|[[...]]]]`——别名部分被再次替换）。防嵌套规则：①替换正则必须排除链接内文本（`(?<!\[\[)`只排一个`[[`不够，别名在`|`后也会被匹配）；②**先试点→批量前检查试点页是否被二次替换**；③替换后全库扫描`[[[[`/`]]]]`嵌套=0；④长名先替换短名后替换（`中华人民共和国行政诉讼法`在`行政诉讼法`之前），避免短名吃掉长名前缀。
- **研究设计同步**：每个大模块摄入完成后，检查 `research-design/` 是否需同步更新（新增素材的支撑/修正作用；素材清单、门禁状态、样本标准等）——**研究设计与知识库必须同步演进**。

**research-design 全文件同步纪律（user-confirmed 2026-08-03）**：模块化知识库更新完成后，必须同步更新 `research-design/` 下**所有**文件（不止五问研究设计——本项目还有 [[工伤认定群案论点证据引注矩阵]]），并核验论证，作为一个固定纪律。每文件检查项：
- **五问研究设计**：素材清单状态列（勿信旧状态——曾出现"121案待摄入"而实际已全部摄入的过期状态）、样本选取标准（草案→定稿）、五项硬门禁状态表、资料截止日期、`updated` 字段。
- **论点证据引注矩阵**：`analysis_status`（preliminary→in_progress→verified）、使用纪律中的过期前提（"121案摄入前…保持待核"）、**统计口径清单随数据集摄入从"待定稿"翻转"可执行"**（121案有年份→年代切片可统计；有裁判结果→改判率可统计等）、矩阵内 `待核/缺证据` 状态按新证据逐行复核。

**统计落地纪律（user confirmed 2026-08，STATS-LANDING教训）**："可执行"≠"已计算"。引注矩阵写"统计口径可执行"不代表统计完成——数据落地前研究设计相关假说必须保持"待验证"，论文开篇不得出现数字（用户写作铁律：禁止编造数据）。统计完成后必须同步更新三处：①引注矩阵（口径→结果数据）②研究设计（"研究假说，待XX摄入后验证"→"已验证+数据"）③写作交接文件（"可执行"→"已完成"）。大样本统计（100+案）用3个子代理并行逐案读裁判结果文本归类，**严格基于文本**：文本未明说最终结果标"无法判定"，不猜测不推断；统计后附**样本代表性警示**（精选案例库非随机样本，论文表述必须说明样本性质）。详见 `references/statistics-landing-and-case-matching.md`。
- 更新后核验：状态标记与口径可执行性是否自洽（写进MODULE-END CHECK第7项）。

**知识分层（user confirmed 2026-08）**：`methodology/`（方法论层：CSSCI法学论文写作方法论、政治与法律期刊行文风格分析）=**跨项目稳定层**，底层行文方式，**不随知识库扩展变化**，无需每次同步；`research-design/`=**项目演进层**，随知识库同步更新；`entities/`+`concepts/`=项目知识实体层。方法论文件曾混在concepts/，已独立为methodology/（2026-08-03，index已分区）。**方法论文件frontmatter纪律**：`type: methodology`（不是 concept），tags 用 `方法论`+`论文写作`/`期刊风格` 等跨项目标签，**绝不挂项目标签**（曾把CSSCI方法论标成`工伤认定`——跨项目基础方法论不应有项目归属）；`analysis_status: verified`（已定稿的方法论内容，非 preliminary）。

**模块化检修结构（MODULE-END CHECK，每个模块完成后固定执行）**：

| # | 检修项 | 验收标准 |
|---|---|---|
| 1 | 摄入完整性 | 该模块页面数=预期数，无0字节/幽灵页，文件名规范（案例N-年份-标题） |
| 2 | 死链扫描 | 全库未解析链接0（按Obsidian真实解析：`\|`和`|`都是别名分隔符，`&#124;`=死链） |
| 3 | YAML | 全库YAML异常0，type符合SCHEMA |
| 4 | 关联核验 | 新页面的双向链接（与论文/与案例/与法规范）每条带印证理由，无纯链接残留 |
| 5 | 双向对称 | 新模块的 出链数 ≈ 入链数（如论文→案例 与 案例→论文 一致） |
| 6 | 旧链接抽检 | 涉及旧页面时，抽检关联真实性（默认不可信，发现1条不实→全批核验） |
| 7 | research-design全文件同步+核验 | research-design/下**所有文件**（五问研究设计+论点证据引注矩阵+其他）逐一同步：素材清单状态/门禁状态/样本标准/统计口径/analysis_status/updated；更新后核验状态自洽（见"research-design 全文件同步纪律"） |
| 8 | 台账+log | 模块摄入、关联、核验三件事各记一条，含教训 |

**log.md自引用陷阱（强制机制，2026-08已犯4次）**：每次追加log.md/台账后**必须立即重跑全库死链扫描**，发现新增死链当场清理，不得留到下次检修。陷阱成因：描述旧bug时把旧链接形式（`[[目标&#124;别名]]`、`[[...]]`、`|[[...]]]]`）当示例写回log，Obsidian Graph把反引号内/标注"（示例）"的方括号链接仍解析为节点。**示例必须彻底去掉`[[`和`]]`只留纯文本**——"（示例）"标注不防解析，去方括号才防。

**不通过不进下一模块**——模块化批次=摄入→关联→MODULE-END CHECK→下一模块。

**模块边界（user confirmed 2026-08-03）**：一个**文件夹**就是一个模块（concepts/、comparisons/、entities/案例/、entities/引用文献/ 各为一个模块）——检修时按文件夹逐个过 MODULE-END CHECK，而不是把整个库当一个模块。用户原话："把一个文件夹作为一个模块"。

Scale decides method (from merged case-ingestion-workflow):

| Scale | Method |
|---|---|
| ≤10 | Foreground Python |
| 10-30 | execute_code batch |
| 30+ | Delegate subagent — provide FULL list of existing concept pages and paper entity filenames for [[wikilinks]] |

**Two-phase ingestion (user-confirmed for the 121-case compilation)**: for large compilations, Phase 1 ingest brief pages from the summary docx (`analysis_status: preliminary`, `source_confidence: medium`, facts/result/holding/basis only, NO analysis layer and NO wikilinks yet — empty analysis layer is INTENTIONAL at this stage, not a shell violation); Phase 2 fill the full analysis layer from the complete-text docx by mirroring matured case pages, then flip to `verified`. The user explicitly asked for this order ("先摄入剩下的68个简要版本，然后再看另一个完整的文档…做系统的完整填充").

**Schema-before-ingest (decided with this user)**: when the user asks "先修复还是先加案例", finish structural-norm tasks FIRST (SCHEMA v2 type taxonomy, tag taxonomy, sources/source_note split, confidence split) before ingesting a large batch — otherwise all new pages are built on the old schema and must be re-migrated (60+ pages × double work). Content-layer repairs of already-ingested pages are independent and don't block ingestion; structure-layer norms gate it. Network-layer work (comparisons, cross-case review) comes AFTER all cases are in.

**Prefix matching false-positives**: matching new titles against already-ingested pages by first-N chars can mis-match (e.g. "某劳务公司诉某区人社局案" matched existing "天津某劳务公司案" — different cases). When deduplicating a compilation against existing pages, print ALL match pairs for manual review or require full main-title equality; never trust prefix-only matches silently.

**Parallel subagents editing the SAME files (2026-08-03 lesson)**: when delegating parallel batches that append to shared pages (e.g. 3 subagents each adding 论文↔案例 entries to the same 25 paper pages), each subagent MUST: (1) skip entries whose target already exists (check by 案例 complete stem in the target section — skip-if-exists is what prevents duplicate/overwritten entries); (2) number new entries continuing from the CURRENT max at write time (read the file fresh, not from a stale cache); (3) after completion, main agent re-verifies numbering continuity and zero duplication across ALL batches. Subagent reports of "MISSING (0)" are self-reports — re-scan from the main context. Also: subagents writing to log.md concurrently can interleave — have only ONE batch write the log record, or verify the true tail before appending.

## Group-Case Three-Dimensional Analysis Framework (群案研究三维分析框架)

The user's core research methodology for 群案研究 (merged from gongshang-qunan-yanjiu). Case pages' `## 群案研究定位` section maps each case to one of three dimensions:

**⚠️ 项目特定性（user confirmed 2026-08，重要）**：三维度框架**仅适用于工伤认定群案研究项目**，是该项目独有的行文思路，**不是通用研究/行文模板**。新项目不得默认套用；用户没主动说研究思路时，AI必须主动询问（见 `five-questions-framework` skill）。

**定位区分（user confirmed 2026-08，重要）**：
- **三维度 = 用户的行文思路**：论文正文的论证结构（维度一裁判方法变迁→维度二法律适用演变→维度三行政与司法张力），用于**写作**时组织文章、以及案例页"群案研究定位"的归类。
- **五问（Q1-Q5） = AI的拆解工具**：当用户提出模糊需求（如"帮我写这个"），AI用五问框架帮用户把模糊需求拆解为清晰的研究设计（见 `five-questions-framework` skill）。
- 两者用途不同：**行文用项目特定思路（本项目=三维），拆解用五问**。不要混用。
- **思路后置路径**：用户自己也不知道研究思路时，允许先建立知识库，每个大模块完成后（MODULE-END CHECK）主动帮用户归纳可行思路、给建议（基于已摄入素材）。

- **维度一（裁判方法变迁）**: extract cases spanning 20+ years; slice by 5-year intervals, track recognition/denial ratios; observe interpretation width of "三工要素" (time/place/cause) across eras; flag turning points (2014 8 typical cases, 2016 Guiding Case No.69).
- **维度二（法律适用演变）**: extract cited legal provisions from each case, sort by time; track shifts (试行办法 → 工伤保险条例 → 司法解释); analyze the "enumeration model → dynamic interpretation" transition. **Historical/abolished regulations ARE part of this dimension** (user confirmed 2026-08): the abolished 《企业职工工伤保险试行办法》(1996) is the chain's start point and should be ingested even though it's no longer in force — historical evolution is EVIDENCE for the single research question (裁判偏差的规范根源), not a second question, so it does NOT violate 一文一问. Only the chain-start regulation is needed; later abolished versions (e.g. 2003 条例原文) are unnecessary because the current 修订版's 衔接条款 (第64/67条) already document the transition.
- **维度三（行政与司法张力）**: calculate consistency/reversal rates; categorize administrative agency errors (burden of proof, vague concepts, procedural violations, circular litigation); note procuratorial supervision role.

## Comparison Pages (comparisons/ 跨案比较层)

Group-case research value concentrates in `comparisons/` pages — typed cross-case results directly usable in the paper. User-approved format (2026-08):

1. `## 样本纳入标准` — inclusion criteria + counts per tier
2. `## 案例表` — table: 案例wikilink | 案情 | 争点 | 裁判结果
3. `## 相同点` — numbered points
4. `## 差异点` — table: 维度 | 差异
5. `## 反例与边界` — negative samples and limiting boundaries (MUST include; makes the analysis defensible)
6. `## 可支持的论文主张` — each item is a claim the paper can adopt, tied to 底稿/学理
7. `## 与其他比较页的关联` — cross-links

**Every case mention in narrative text must be a display-text wikilink** `[[案例N-标题|韩老汉案]]` (user mandate). **Table cells use `\|` for the alias pipe — `[[目标\|别名]]` — NOT `&#124;` and NOT bare `|`** (PIPE-FIX 2026-08, user-verified in Obsidian): Obsidian's wikilink parser does NOT recognize `&#124;` as an alias separator — it treats the whole `目标&#124;别名` as one filename → dead link → Graph View shows a `&`-bearing ghost node. Bare `|` splits the table column. `\|` (escaped pipe) is the ONLY correct form in tables: Obsidian neither splits the column nor misparses the link. This REVERSES the earlier FORMAT-AUDIT-2 guidance that recommended `&#124;`. Batch link replacements must cover `[[旧]]`, `[[旧|别名]]`, `[[旧.md]]` AND the legacy `[[旧&#124;别名]]` form. **Dead-link/未解析链接 check scripts MUST parse aliases with BOTH separators**: target = split on `\\|` first, then `|` (i.e. `re.split(r'\\\||(?<!\\)\|', raw)[0]`) — a naive single `split('|')` mis-reports `[[目标\|别名]]` as unresolved. Also verify table column consistency with the escaped pipe STRIPPED (`re.sub(r'\\\|','',line)` before counting `|`) — otherwise `\|` inflates column counts and looks like broken tables. The `## 可支持的论文主张` section is the direct bridge to the paper — this is what the user checks first.

## Concept Page Refinement (概念页细化)

Thin concept pages (1200-1800 chars, theory-only) fail the user's standard once a case corpus exists. Refine each concept page with:

- **`## 案例证据` layer per concept point**: link typical cases (positive / negative / boundary — at least 1 each) with a one-line holding per case, then a "关键归纳" paragraph mapping cases to the scholarly positions
- **`## 与比较页的关联` section**: 概念→comparisons/ pages
- **`## 规范依据` section (AUDIT-BATCH7 2026-08-03)**: concept pages that discuss legal standards MUST link the supporting norm pages — a 举证责任 concept page with zero links to 行诉法第34条/条例第19条 is a weak signal. Add 2-4 entries `- [[法规范页完整文件名]]——说明（30-80字，写明哪些条文支撑本概念）`, inserted before `## 与比较页的关联` (or before `## 相关概念` if absent). Scan signal: count concept→norm links per page; 0 = weak.
- Target ≥2000 chars; methodology/writing-guide pages (CSSCI方法论, 期刊风格分析) do NOT need the case layer

## Reference Files

- `references/content-completeness.md` — **内容完整性强制纪律**（原 wiki-content-completeness v1.0.0，v3.0.0 合并）：每页必须写满实质内容，不允许空壳/占位符；案例/论文/概念页必备字段清单；反模式；500字符底线
- `references/docx-footnote-extraction.md` — DOCX 脚注提取（python-docx paragraphs 不含脚注；zip 读 footnotes.xml + footnoteReference 位置标记；脚注自带 `[]` 前缀陷阱）
- `references/legal-norm-hierarchy-and-reply-ingestion.md` — 法的渊源/规范层级（宪法→法律→行政法规→司法解释→部门规章→批复答复→会议纪要→审判答疑）、批复vs答复区分、司法解释vs部门规章位阶（司法解释上位=裁判依据，规章仅参照）、论文引用铁律、entities/法规范/7层结构、15批复→6争点页映射表、法条摄入工作流
- `references/session-2026-08-01-case-tiers-and-filling.md` — 121案三层分类+全局连续编号+68页完整填充：分类判定逻辑（含旧53案识别陷阱）、编号纪律（文件名编号≠页面标题）、8节填充格式、批量写入要点
- `references/model-orchestrated-legal-research-workflow.md` — Class-level model routing: replaceable role slots, Wiki→paper stage ownership, MoA decision gates, handoff contracts, and benchmarked model updates
- `references/session-2026-07-24-lessons.md` — First session: empty-page crisis, tag conversion, read_file caching, compilation parsing
- `references/session-2026-07-30-lessons.md` — Second session: wiki rebuild, papers-before-cases order, parallel delegate_task extraction, journal style templates
- `references/session-2026-07-30-batch2-lessons.md` — Batch 2 extraction: curly-quote filename pitfall, single-agent execute_code approach for small batches, stdout truncation mitigation
- `references/session-2026-07-30-batch3-lessons.md` — Batch 3 (25-paper full ingestion): subagent JSON failure + fallback, pymupdf metadata unreliability + manual corrections, concept-page generation patterns, page size targets, skill overlap note
- `references/session-2026-07-30-deadlinks-lessons.md` — Dead link crisis (133 dead links), re-extraction of missing abstracts/conclusions, themed concept page strategy
- `references/session-2026-07-30-crossref-lessons.md` — Cross-reference network crisis (25 papers as isolated islands), three-layer completeness model, anchor-first cross-reference building
- `references/session-2026-07-30-format-lessons.md` — PDF format artifact cleanup (］［ brackets, broken lines, keyword corruption), three-dimension quality model
- `references/session-2026-07-30-yaml-format-lessons.md` — YAML frontmatter quote escaping (Obsidian red pages), fragmented conclusion detection, five-dimension quality check workflow
- `references/session-2026-07-30-quality-verification-lessons.md` — Phase 2: unified 6-dimension quality verification, English-in-abstract fix, section heading empty line, subagent reliability, user patience lesson
- `references/session-2026-07-31-literature-wiki-audit.md` — Literature-Wiki audit: provenance mapping, metadata verification, semantic conclusion checks, bidirectional links, statute precision, and staged repair
- `references/session-2026-07-31-paper-case-links.md` — paper–case mapping: confidence rules, anonymized aliases, reverse-edge updates, and recursive verification
- `references/session-2026-08-02-paper-case-pilot.md` — 25论文↔121案例库链接试点：语料重合度仅~10%（正常非缺陷）、权威标识（指导案例/检例）优先匹配、先审计现有链接再新增（张相军篇刘自荣案曾错链案例31）
- `references/session-2026-08-03-paper-case-dualtrack.md` — 论文↔案例**双轨链接**（引用轨+主旨轨）全量执行：用户纠正链原话、121/121覆盖步骤、镜像陷阱（行内多案例/观点观点重复/行内第二案例漏配）、并行子代理写log问题、验收清单
- `references/session-2026-07-30-conclusion-reextraction.md` — Batch 1 conclusion re-extraction: PDF-to-/tmp/ extraction, Chinese-punctuation Python escaping pitfall, surgical regex section replacement, heterogeneous conclusion headers
- `references/session-2026-07-30-conclusion-reextraction-batch2.md` — Batch 2 conclusion re-extraction (7 papers): fullwidth-English contamination fix, embedded page headers, split-char section headers (结\n语), no-explicit-conclusion strategy, leaked section header cleanup, reusable `clean_conclusion()` function
- `references/session-2026-07-30-threesection-repair.md` — Three-section batch quality repair (摘要+核心论点+主要结论): English Abstract contamination defect type, PDF-residue in 核心论点 requiring full rewrite, benchmark-driven quality repair pattern
- `references/session-2026-07-30-phase3-lessons.md` — Phase 3 polish: vault-root ghost files, sources/filename sync, 引用规范 statute-article completion, 引用案例 extraction, subagent lazy markers and format drift
- `references/systematic-vault-audit-and-optimization-ledger.md` — Whole-vault structural and semantic audit, template-risk detection, graph-shape analysis, and append-only optimization ledger protocol
- `scripts/batch_extract_papers.py` — Reusable PDF batch extraction script
- `scripts/clean_pdf_artifacts.py` — Reusable PDF artifact cleanup script (run after batch ingestion)
- `scripts/check_wikilinks.py` — Vault-wide recursive dead-link/backlink checker (handles nested entity dirs, known false positives, optional target-page backlink count)

## Dead Link Prevention (MANDATORY after every ingestion batch)

Dead links — `[[wikilinks]]` pointing to non-existent pages — are as bad as empty
pages. The user clicks a link in Obsidian and sees a blank page. In one session,
133 dead links were created because every keyword in "涉及概念" sections was
wrapped in `[[]]` without a corresponding page.

### Post-ingestion dead-link check

```python
import os, re
from collections import Counter
wiki = "/path/to/wiki"
existing_pages = set()
for d in ["entities", "concepts", "research-design"]:
    for f in os.listdir(f"{wiki}/{d}"):
        if f.endswith('.md'): existing_pages.add(f[:-3])
all_links = Counter()
for d in ["entities", "concepts", "research-design"]:
    for f in os.listdir(f"{wiki}/{d}"):
        if f.endswith('.md'):
            with open(f"{wiki}/{d}/{f}") as fh:
                links = re.findall(r'\[\[([^\]]+)\]\]', fh.read())
            for link in links:
                if link not in existing_pages:
                    all_links[link] += 1
dead = all_links.most_common()
print(f"Dead links: {len(dead)}")
for link, count in dead: print(f"  [[{link}]] ← {count} refs")
```

### Dead link resolution

1. **High-frequency (3+ refs)**: Create themed concept pages absorbing multiple
   related dead links (e.g., one "工伤认定的核心要件" page absorbs 工作时间,
   工作场所, 工作原因, 上下班途中, 因工外出, etc.)
2. **Low-frequency (1-2 refs)**: Convert `[[term]]` to plain text `term`.
3. **Target: zero dead links** before finishing any ingestion session.

### When generating "涉及概念" sections

Do NOT wrap every keyword in `[[]]`. Only link to concepts that already have a
page OR are important enough (3+ papers reference them) to warrant creating one.
For all other keywords, use plain text.

## Missing Abstract/Conclusion Re-extraction

When auto-extraction produces empty abstracts or conclusions (replaced with
"详见原文"), re-extract with a dedicated script that reads ALL pages (not just
first 10) and tries multiple regex patterns:

```python
import pymupdf, re
doc = pymupdf.open(path)
text = "".join(page.get_text() for page in doc)
# Abstract: try multiple patterns
for pattern in [
    r'摘\s*要[：:（(【]?\s*(.*?)(?=关键词|Key\s*word|【关键词|一、|$)',
    r'Abstract[：:（(]?\s*(.*?)(?=Key\s*word|一、|引言|$)',
]:
    m = re.search(pattern, text, re.DOTALL)
    if m and len(m.group(1).strip()) > 30:
        abstract = m.group(1).strip(); break
# Conclusion: search last 6000 chars
for pattern in [r'(?:结语|结论|结\s*语)[：:。\s]*(.*?)(?=参考文献|$)']:
    m = re.search(pattern, text[-6000:], re.DOTALL)
    if m and len(m.group(1).strip()) > 50:
        conclusion = m.group(1).strip(); break
```

Key: read ALL pages for conclusion extraction. Different journals format differently.

### Conclusion header heterogeneity

PDF conclusion sections use varied headers — don't assume `结语` or `结论`:

| Header pattern | Example papers |
|---------------|----------------|
| `六、结语` / `五、结语` / `四、结语` | Most 法学 papers (numbered section) |
| `五、结论与政策建议` | Some 社会保障 papers |
| `五、结论` | Shorter papers |
| `结　语` (fullwidth space U+3000 between chars) | 莫良元 |
| `结\n语` (chars split across newline in extraction) | 王敏 — search for `"结\n语"` not `"结语"` |
| No explicit section — last paragraph before 责任编辑 | 葛翔, 艾琳 |
| No explicit section — last theoretical section | 黄辉 (类型化 section IS the conclusion) |
| No explicit section — entire final numbered section | 李超 (section 四 standards discussion) |
| `提要` / `摘要` at the TOP of the paper serves as conclusion | 郑尚元 |
| `余论` — "remaining remarks" after last numbered section, before 参考文献 | 王东伟 (举证责任) |

When re-extracting conclusions, first `read_file` the full PDF text from `/tmp/`
and manually identify the correct section before extracting. If no explicit
`结语`/`结论`/`结　语`/`总结`/`余论` marker is found, search for the last
substantive paragraph before `责任编辑` or `（责任编辑`.

### Surgical section replacement (batch conclusion re-extraction)

When replacing conclusions (or any single section) across multiple wiki pages:

1. **Extract** full PDF text to `/tmp/pdf_<name>.txt` via pymupdf
2. **Identify** the conclusion section by reading the /tmp/ text
3. **Write** each conclusion to `/tmp/conclusions/NN_name.txt` via `write_file`
   (NEVER inline Chinese text in Python string literals — see pitfalls)
4. **Replace** only the target section using regex:
   ```python
   pattern = r'(## 主要结论\n)([\s\S]*?)(\n## |\Z)'
   match = re.search(pattern, content)
   new_content = content[:match.start(2)] + conclusion_text + content[match.end(2):]
   ```
5. **Verify**: char count ≥ 200 AND all expected section headers still present

See `references/session-2026-07-30-conclusion-reextraction.md` for full workflow
and the 6-paper batch that brought all conclusions from <150 to 200+ chars.

## Cross-Reference Network Construction (MANDATORY after ingestion)

Content + no dead links is necessary but NOT sufficient. A wiki where 25 papers
each link only to "CSSCI法学论文写作方法论" is a pile of isolated islands —
the user clicks around and finds no intellectual connections. This is as useless
as empty pages.

### The problem

After batch ingestion, papers typically link only to:
- The methodology concept page (e.g., [[CSSCI法学论文写作方法论]])
- 1-2 concept pages

They do NOT link to:
- The anchor/draft paper (底稿) — the user's own work that is the reason the wiki exists
- Other papers in the same domain — peer literature that shares theoretical ground

### Post-ingestion cross-reference check

After ALL pages are created and dead links are resolved, run this check:

```python
import os, re
from collections import defaultdict

wiki = "/path/to/wiki"
all_pages = {}
for d in ["entities", "concepts", "research-design"]:
    for f in os.listdir(f"{wiki}/{d}"):
        if f.endswith('.md'):
            all_pages[f[:-3]] = d

# Check: do entity pages link to other entity pages?
for page_name, dir_name in sorted(all_pages.items()):
    if dir_name != "entities": continue
    with open(f"{wiki}/{dir_name}/{page_name}.md") as fh:
        content = fh.read()
    links = re.findall(r'\[\[([^\]]+)\]\]', content)
    entity_links = [l for l in links if l in all_pages and all_pages[l] == "entities"]
    if len(entity_links) < 2:
        print(f"⚠️ {page_name}: only {len(entity_links)} entity cross-refs")
```

### Cross-reference building workflow

When the check shows papers with <2 entity cross-references:

1. **Identify the anchor document** — the user's own draft/底稿. This is the central
   node that ALL papers must link to.

2. **Extract the anchor's key theoretical contributions** — read the draft and list
   5-10 specific theoretical points (e.g., "三层规范体系", "认定路径遮蔽",
   "裁判偏差惯例化").

3. **For the anchor document itself**: Add a "与引用文献的关联" section that
   links to ALL papers, grouped by theme. Each link must specify the theoretical
   connection (呼应/补充/分歧 + reason).

4. **For each paper**: Add two sections before "## 相关概念":
   - "## 与底稿的关联" — which specific theoretical point in the anchor does this
     paper echo, supplement, or contradict? Why?
   - "## 与其他论文的关联" — which other papers share theoretical ground?

5. **Use parallel delegate_task** for large sets (15+ papers):
   - Split into groups of 8-9 papers
   - Each subagent reads the paper, identifies connections to the anchor's
     theoretical points and to peer papers, writes the sections via Python
   - Main agent adds the anchor's own section manually (it requires understanding
     all papers at once)

### Quality requirements for cross-references

- **Specific, not generic**: "本文提出的XXX观点与底稿中XXX论点形成呼应/补充/分歧，因为..."
  NOT "本文与底稿有关"
- **Bidirectional**: If paper A links to paper B, paper B should link back to paper A
- **Thematic grouping**: Group cross-references by theme (举证责任, 认定路径, 程序问题, etc.)
- **Target**: Each paper has 3-6 entity cross-references; the anchor has links to all papers

### Verification

```python
# After cross-reference building, verify
for page_name, dir_name in sorted(all_pages.items()):
    if dir_name != "entities": continue
    with open(f"{wiki}/{dir_name}/{page_name}.md") as fh:
        content = fh.read()
    has_draft_link = "与底稿的关联" in content or "与引用文献的关联" in content
    links = re.findall(r'\[\[([^\]]+)\]\]', content)
    entity_links = [l for l in links if l in all_pages and all_pages[l] == "entities"]
    status = "✅" if has_draft_link and len(entity_links) >= 2 else "⚠️"
    print(f"{status} {page_name}: draft={has_draft_link}, entity_links={len(entity_links)}")
```

## PDF Format Artifact Cleanup (MANDATORY after batch ingestion)

pymupdf text extraction from Chinese academic PDFs produces **format artifacts** that
survive into wiki pages and are visible to the user in Obsidian:

1. **Full-width bracket residue**: `］` and `［` characters from PDF layout boxes
   appear in abstract, keywords, and body text. Also `】` and `【`.
2. **Broken lines mid-sentence**: PDF page-width line breaks are preserved as `\n`,
   splitting sentences across lines (e.g., "不确定法律概念\n如何将这些").
3. **Keyword section corruption**: Newlines within keyword lists, bracket residue
   wrapping keywords (e.g., "］工伤认定; 不确定法律概念; 司法审查\n［").
4. **OCR errors**: `Vo1.` instead of `Vol.`, footnote markers merged into body text.

### Post-ingestion format check

After ALL pages are created (but before cross-reference building), scan every
entity page for these artifacts:

```python
import os, re

wiki_entities = "/path/to/wiki/entities"
issues = []

for f in sorted(os.listdir(wiki_entities)):
    if not f.endswith('.md'): continue
    path = os.path.join(wiki_entities, f)
    with open(path) as fh:
        content = fh.read()
    page_issues = []
    if '］' in content or '［' in content: page_issues.append("PDF方括号残留")
    # Check keywords for newlines or brackets
    kw_match = re.search(r'## 关键词\n\n(.*?)\n\n##', content, re.DOTALL)
    if kw_match:
        kw = kw_match.group(1).strip()
        if '\n' in kw or '］' in kw or '【' in kw: page_issues.append("关键词格式异常")
    # Check abstract for broken lines
    abs_match = re.search(r'## 摘要\n\n(.*?)\n\n##', content, re.DOTALL)
    if abs_match:
        if re.search(r'[，；。]\n[^\n]', abs_match.group(1)): page_issues.append("摘要PDF换行残留")
    if page_issues:
        issues.append((f, page_issues))

print(f"Files with format issues: {len(issues)}")
for f, pi in issues: print(f"  {f}: {pi}")
```

### Cleanup script

For each affected file, run a cleanup pass that:
1. Strips `］［】【` characters
2. Joins broken lines in abstract/conclusion sections (`re.sub(r'([^\n])\n([^\n])', r'\1\2', text)`)
3. Normalizes keyword sections (remove newlines, strip bracket residue)
4. Preserves paragraph breaks (double newlines) and frontmatter

See `scripts/clean_pdf_artifacts.py` for the reusable cleanup script.

**This check is separate from content completeness and dead-link checks.** All three
must pass before declaring ingestion complete. The user WILL spot format artifacts
in Obsidian and lose trust in the wiki quality.

## YAML Frontmatter Quote Escaping (MANDATORY post-ingestion check)

Chinese academic PDF filenames frequently contain curly quotes (e.g.,
`"两高"共同发挥监督作用...pdf`, `"循环诉讼"...pdf`, `"合理时间"...pdf`).
When these filenames are used in YAML `title:` and `sources:` fields,
the curly quotes conflict with YAML string delimiters, causing
**Obsidian to mark the page red and fail to parse frontmatter**.

### Post-ingestion YAML check

After ALL pages are created, scan every `.md` file's frontmatter for
quote issues:

```python
import os, re

wiki = "/path/to/wiki"
issues = []
for d in ["entities", "concepts", "research-design"]:
    for f in os.listdir(f"{wiki}/{d}"):
        if not f.endswith('.md'): continue
        path = f"{wiki}/{d}/{f}"
        with open(path) as fh:
            content = fh.read()
        fm = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
        if not fm: continue
        fm_text = fm.group(1)
        # Check for Chinese curly quotes in frontmatter
        if '\u201c' in fm_text or '\u201d' in fm_text:
            issues.append((f, "Chinese curly quotes in frontmatter"))
        # Check for title with nested quotes
        title_match = re.search(r'^title:\s*"?(.*?)"?\s*$', fm_text, re.MULTILINE)
        if title_match:
            val = title_match.group(1)
            if '"' in val:  # nested ASCII double quotes
                issues.append((f, f"Nested quotes in title: {val[:50]}"))

print(f"YAML issues: {len(issues)}")
for f, issue in issues:
    print(f"  ⚠️ {f}: {issue}")
```

### Fix

For every affected file, strip ALL quotes from frontmatter fields:

```python
import re

# For each file with issues:
fm_match = re.match(r'^(---\n)(.*?)(\n---)', content, re.DOTALL)
fm = fm_match.group(2)
# Remove Chinese curly quotes
fm = fm.replace('\u201c', '').replace('\u201d', '')
# Fix title: remove all quotes, use bare value
fm = re.sub(r'title:\s*"(.*?)"', lambda m: f'title: {m.group(1).replace(chr(34), "")}', fm)
fm = re.sub(r'title:\s*"(.*?)"', lambda m: f'title: {m.group(1)}', fm)
# Write back
content = content[:fm_match.start(2)] + fm + content[fm_match.end(2):]
```

**Rule: YAML `title:` fields should be bare values (no quotes) for Chinese
academic wikis.** Chinese titles don't need YAML string quoting — only
strings containing `:`, `#`, or starting with special chars need quoting,
and even then use single quotes, never double quotes with nested quotes.

## Fragmented Conclusion Detection

pymupdf sometimes extracts text fragments from the **middle** of a paper
as "conclusions" because the regex for `结语/结论` matches section
references or mid-text occurrences. The resulting conclusion field starts
with punctuation (`，`, `；`) and is an unusable fragment.

### Detection

```python
import re
concl_match = re.search(r'## 主要结论\n\n(.*?)\n\n##', content, re.DOTALL)
if concl_match:
    concl = concl_match.group(1).strip()
    # Fragment indicators:
    starts_with_punct = len(concl) > 0 and concl[0] in '，。；、的而'
    too_short = len(concl) < 100
    if starts_with_punct or too_short:
        print(f"⚠️ Fragmented conclusion detected: starts with '{concl[:20]}'")
```

### Fix

When a fragmented conclusion is detected:
1. Read the **last 2000 chars** of the full PDF text to find the real
   concluding section
2. If no explicit `结语/结论` section exists (common in shorter papers),
   **manually synthesize** a 200-400 character conclusion from the paper's
   section headings and key arguments
3. Never leave a fragmented conclusion — it is worse than no conclusion
   because it misleads the reader

## Three-Section Batch Quality Repair (摘要 + 核心论点 + 主要结论)

When wiki entity pages have quality defects in multiple sections simultaneously
(English abstracts, PDF-residue in 核心论点, fragmented/short conclusions),
repair all three sections in a single batch pass using the benchmark-driven
approach.

### Defect types to scan for

1. **English Abstract contamination**: CNKI PDFs contain both Chinese
   内容提要/摘要 AND English Abstract. Auto-extraction may grab the English
   version. Detect: `[a-zA-Z]{10,}` in the 摘要 section.
2. **核心论点 PDF residue**: page numbers (`· 9 1 1 ·`), footnote markers
   (`瑏瑠`, `瑔瑦`), citation brackets (`〔1〕`), broken lines, **PDF section
   headers leaked as argument text** (`**一、问题的提出**`, `**二、溯因**`,
   `**三、再造**`). These are too pervasive for find-replace —
   **rewrite the section entirely** as clean numbered arguments (3-4 items,
   each 200+ chars) based on the PDF's actual section structure.
3. **主要结论 defects**: fragment start (`;` or `，`), English Abstract
   appended at end, or too short (<200 chars). See "Fragmented Conclusion
   Detection" and "Missing Abstract/Conclusion Re-extraction" sections above.

### Workflow

1. **Extract** all PDFs to `/tmp/pdf_<author>.txt` via pymupdf in `execute_code`
2. **Read** first 3000 chars (摘要) and last 2000-3000 chars (结语/结论) of
   each /tmp/ file; also read middle sections for 核心论点 source material
3. **Rewrite** each defective section using a `replace_section()` helper for
   surgical regex replacement (preserves all other sections):
   ```python
   def replace_section(content, section_name, new_content):
       pattern = r'(## ' + re.escape(section_name) + r'\n\n).*?(\n\n## )'
       return re.sub(pattern, r'\g<1>' + new_content + r'\g<2>', content, count=1, flags=re.DOTALL)
   ```
4. **Verify** all pages against benchmark metrics (see below)

### Benchmark-driven quality repair

Use a known-good page as the quality standard. For the 工伤认定 wiki, the
benchmark is 梁琼芳 (摘要 176 chars, 核心论点 3 items avg 259 chars/item,
主要结论 403 chars). All repaired pages must meet:
- 摘要: ≥100 chars, zero English words ≥10 chars
- 核心论点: ≥3 numbered items, avg ≥100 chars/item, zero PDF residue
- 主要结论: ≥200 chars, no fragment start, no English text

See `references/session-2026-07-30-threesection-repair.md` for the full
7-paper batch repair session with defect catalog and results table.

## 引用规范与引用案例章节补全（深度优化阶段）

After content quality passes, two more sections need depth work:

**引用规范**: (1) strip non-statute contamination — journal names, book titles
(释义/注释/逐条/探索与实践), paper titles — via keyword blocklist; (2) add article
numbers extracted from PDF full text (`《X》第N条` regex, 条 level only, no 项/款);
(3) normalize mixed Arabic/Chinese numerals (`第14、十五、15条` → `第14、15条`).
**引用案例**: extract real cases only — case-number regex, 指导案例N号, named cases,
 judicial replies (批复/答复/复函). Genuinely case-free papers get an honest
`- 本文未引用具体案例` line, never a blank section. Details and regexes:
`references/session-2026-07-30-phase3-lessons.md`.

## Unified Post-Ingestion Quality Verification (MANDATORY — run ALL checks before declaring complete)

After ALL ingestion, cross-reference building, dead-link resolution, and format cleanup
are complete, run ONE comprehensive quality check covering ALL 6 dimensions. Do NOT
declare "all done" after fixing one dimension — the user WILL find the next issue and
lose trust in the wiki.

### The 6-dimension quality bar

Every entity page (论文实体页) must pass ALL of these:

| Dimension | Standard | Common Failure |
|---|---|---|
| 1. 摘要 | 50+ chars, **pure Chinese** (no English) | Bilingual PDFs leak English Abstract |
| 2. 主要结论 | **200+ chars**, starts with proper char (not `，。；`) | pymupdf regex matches mid-text fragments |
| 3. PDF artifacts | No `］［】【` symbols, no broken lines | pymupdf extraction residue |
| 4. 关键词 | Clean, semicolon-separated, no newlines/brackets | PDF keyword formatting corrupts |
| 5. YAML frontmatter | No curly quotes (""), no nested quotes | PDF filenames with curly quotes |
| 6. Section formatting | `## Heading\n\nText` (empty line after heading) | Subagents write `## Heading\nText` |

### Verification script

See `references/session-2026-07-30-quality-verification-lessons.md` for the complete
unified quality check script that scans all 6 dimensions in one pass.

### Post-subagent verification

When using parallel `delegate_task` subagents for batch extraction or fixes:
- Subagent "completed" status does NOT guarantee quality
- Subagents commonly fail on: English in abstracts, short conclusions, section formatting
- ALWAYS run the 6-dimension check after ALL subagents complete
- Manually fix any remaining failures

### Key lesson: user patience is finite

In one session, the user found 8 separate quality issues across 8 turns, each requiring
a separate fix cycle. Each time the agent declared "done," the user found the next issue.
**Rule**: Run ALL checks proactively and present a single quality report showing all
dimensions passing, rather than declaring "done" and waiting for the user to find problems.

## Whole-Vault Structural and Semantic Audit

Use this workflow when the user asks for a systematic review of the entire legal wiki, its categories, architecture, representative pages, or a future-agent optimization plan. The default is **read-only diagnosis**. If the user requests a root audit/optimization file, treat that file as the only allowed write and do not silently repair existing pages during the audit.

Audit in two independent tracks:

1. **Technical health** — recursive YAML validation, actual raw-path existence, live dead links, index coverage, empty/thin pages, root-level zero-byte notes, tag/schema drift, update dates, raw coverage, duplicate hashes, scripts, and Obsidian configuration.
2. **Academic usefulness** — traceability of claims, hypothesis-versus-fact status, separation of source facts from agent analysis, concept/literature/case examples, comparison-layer coverage, confidence semantics, and the specificity of cross-page relations.

Do not let good technical counts conceal poor scholarship. A case page may be long, sourced, indexed, and dead-link-free while its dispute focus, adjudication method, group-case position, or related-case section is generic or wrong. Detect this by fingerprinting normalized section bodies, counting repeated long paragraphs and repeated link bundles, comparing facts against procedural-history duplication, and then reading one benchmark plus one suspicious outlier per category. Corpus counts locate risk; source-backed page reading proves it.

For graph analysis, build substantive inbound edges from formal content pages only. Index links prove navigation but do not make a page intellectually connected; documentation examples and historical log links must be reported separately. Measure category-to-category edges and inspect graph shape. A star where dozens of cases all point to the same few anchors is false density, not a useful group-case network. Never add links merely to reduce orphan counts.

Also audit the machinery that created the wiki. A generator with hard-coded paths, stale output folders, direct overwrite, no dry-run/no-clobber, or fixed analytical templates is a P1 safety risk. Generators should extract source facts and structure, not invent dispute focuses, comparative relations, or research conclusions.

Report findings as P0–P3 and give another model an executable order: safety boundary → 5–8 page pilot → schema pilot → evidence-backed relationship rebuild → comparison/navigation layer → tags/format/Graph → deferred statute library. The optimization ledger must carry numbered findings, evidence, scope, acceptance checks, a small first batch, and an append-only execution template. Keep the global `log.md` concise while the optimization ledger stores detailed evidence and verification.

### Maintenance ledger division (three files, not two duplicate logs)

When the user asks to reorganize the vault's audit/optimization records, use three roles instead of letting two files both record execution history:

1. **排查修复流程与整改台账** (process manual + issue ledger): how to inspect, what problems remain (OPT-001-style numbered findings with acceptance criteria), and a rule write-back zone. Renaming a bare `优化log.md` to this name makes the dual role explicit.
2. **`log.md`** (timeline): one-line-per-action global record pointing to the ledger and `.maintenance/`; never duplicate the full execution narrative.
3. **`.maintenance/OPT-编号/`** (evidence): backups, diffs, hashes, manifests per batch.

Detailed narratives live in exactly one place. Historical log entries that mention the old filename are intentional false positives — keep them, only update live references (skills, protocol sections, header notes).

### Rule write-back discipline (AI "self-learning" within bounds)

AI can register rule candidates (RULE-CANDIDATE-XXX) but never self-confirm them. Promotion to confirmed rules requires ALL of: (1) recurrence in ≥2 independent batches; (2) page + raw-source evidence; (3) full-vault regression passed; (4) no change to research question, core classification, source credibility, legal validity, or statistical definitions; (5) user confirmation or membership in already-written quality rules. This delivers auditable project-level learning without letting the model silently change the research contract.

See `references/systematic-vault-audit-and-optimization-ledger.md` for the full pass order, template-homogeneity method, graph rules, schema/provenance distinctions, Obsidian checks, severity model, and ledger template.

## Literature-Wiki Audit and Staged Repair

Use this section when the user asks to inspect an existing `entities/引用文献/` corpus before deciding what to do next. The default first pass is **read-only diagnosis**, not bulk rewriting.

### Audit sequence

1. **Inventory the corpus**: count literature pages, raw PDFs, style-template pages, and index entries independently. Build a page-to-source map from each `sources:` value and verify every path exists. Do not call intentionally separated `entities/范文/` PDFs missing literature sources.
2. **Check semantic sections**: validate YAML and headings, then inspect the meaning of `摘要`, `核心论点`, `研究方法`, and `主要结论`. Length thresholds are necessary but insufficient. A long numbered body section is still a wrong conclusion; a sentence fragment is still defective even if it has 200+ characters.
3. **Verify metadata against the PDF**: manually read the first page/DOI when author affiliation, co-authors, journal, issue, pages, or DOI are absent or uncertain. PDF text extraction is not a reliable bibliographic authority. Do not leave every page at `confidence: high` when source-level uncertainty remains.
4. **Audit the graph in both directions**: scan the complete vault (including root files) for dead links, then measure paper → anchor draft, anchor → paper, paper ↔ paper, paper → case, and case → paper coverage. A readable phrase such as `标题|底稿` outside `[[...]]` is not a graph edge. A case name in `引用案例` is not a case link until it is mapped to an existing file stem.
5. **Audit legal citations by evidence**: list every `引用规范` item lacking an article marker, then classify it as exact statutory support, whole-instrument background, policy document, judicial reply, or uncertain. Add `第X条` only when the source supports it; never fill missing provisions by inference.
6. **Separate repairs by risk**: report must-fix correctness defects (wrong metadata, wrong conclusion, false link), recommended structural improvements (method sections, article-level citations, bibliography fields), and deferred enrichment (new case pages, broad crosslink expansion). Ask for scope before changing more than a small verified batch.

### Required acceptance output

The final audit must state: page/source counts; extra template sources; substantive and section results; verified metadata defects; conclusion/method defects; dead links with documentation/history false positives separated; bidirectional graph coverage; citation-precision counts; and the three repair priority classes. Re-run the entire report after repairs rather than declaring completion after one dimension passes.

See `references/session-2026-07-31-literature-wiki-audit.md` for the reusable defect catalog, audit passes, and report template.

### Staged repair and concise user-facing reporting

After the read-only audit, obtain explicit scope confirmation before editing. For the first repair batch, default to no more than five pages and only source-verified, unambiguous defects. Separate metadata corrections from semantic rewrites and deferred enrichment; do not silently fix all 25 pages at once.

Before editing each target page:
1. Re-read the current page and the relevant first-page or concluding PDF passage.
2. Record the exact old field/section and the source-supported replacement.
3. For a conclusion rewrite, write the replacement text to a temporary file, then surgically replace only `## 主要结论`; preserve every other section.
4. Update `updated` only on pages actually changed, and append a short audit-log entry.

After the batch, re-read every changed page and verify YAML parsing, source paths, required headings, conclusion length/semantic start, PDF-artifact absence, and links. Because this wiki uses nested entity directories, collect pages and link targets recursively (`Path.rglob('*.md')`), not only with a top-level `glob`.

For this user's legal-Wiki work, the report must be action-first and short: start with the batch size and exact page names, give one concrete change per page, list only the key verification counts, and state the next batch in one sentence. Do not repeat the entire audit when the user asks "第一步是什么" or says the response is too long.

**Hard style rule for proposal answers**: when the user asks 要不要改 / 有什么好处 / 具体怎么弄 (before approving a change), answer in plain language with a few sentences plus at most one small table. The user has explicitly rejected long structured essays for such questions ("太长了，我根本读不懂") and will ask for a re-explanation — never pre-empt with a multi-part proposal document. Save the full detail for after approval, in the artifact itself.

See `references/session-2026-07-31-batch1-repair.md` for the five-page repair checklist, recursive-link verification, and patch pitfalls.

## Staged Deep Repair (bibliography, paper–case links, and statute precision)

When a literature corpus has passed basic completeness checks but still needs deep repair, split the work into independently verifiable sub-batches rather than rewriting all 25 pages at once: (A) bibliography metadata, preferably five pages; (B) paper–case graph mapping and bidirectional links; (C) article-level statute verification. Before any 10+ page edit, record the affected pages and field/link mapping.

For bibliography fields, verify the PDF first page, printed page footers, and printed DOI/article number. Treat external search results and PyMuPDF metadata as secondary only. If an article-number suffix conflicts with printed page numbers, record the printed page range and article number separately; never infer or silently overwrite one with the other. In this vault, extend the existing body metadata block with issue/volume, pages, DOI, or article number instead of inventing new YAML keys unless `SCHEMA.md` is updated.

Use temporary files plus surgical patches for replacement blocks, update `updated` only on changed pages, and preserve unrelated sections. After each sub-batch, run target-level and recursive-vault checks: YAML, source paths, required headings, substantive conclusions, PDF artifacts, dead links, and nested-link corruption. Read the true tail of `log.md` before appending the sub-batch record. Keep user-facing reporting action-first and short: scope, concrete changes, verification counts, and the next sub-batch not yet started.

See `references/staged-deep-repair.md` for the evidence hierarchy, page-range conflict rule, metadata format, acceptance checks, and logging procedure.

## Paper–Case Thematic Linking (论文—案例主题链接, user-corrected 2026-08-02)

**用户纠正了链接逻辑（最高优先）**：论文与案例的关联**不在于"论文引用了哪个案例"的一一对应**（学者论文引用的是裁判文书网随机案例，与精选案例库重合度仅~10%，逐条匹配≈0收益），而在于**案例主旨（裁判要旨）能否对应论文的主要观点**——"这些公报案例经典案例的主旨或者说一些要以能不能和论文里面的主要观点去对应"。链接标准 = 观点↔要旨的印证/支撑/反衬关系，不是引用关系。

**双轨制（user clarified 2026-08-03 — BOTH tracks must be built）**：链接关系有且只有两类，都要建立：
1. **引用轨**：论文直接引用的案例（论文页 `## 引用案例` 或 `## 与案例的关联` 提到）→ 建立关联。
2. **主旨轨**：论文**没有引用**、但案例裁判主旨与论文核心论点存在印证/支撑/反衬关系的案例 → 也要建立关联。用户原话："一种是论文直接引用 那肯定有关系 一种是论文没引用这些案例 但是论文的观点和案例的裁判主旨有关 也可以联系"。
- **无关联不硬加（user rule）**：案例与任何论文观点都无实质对应时，**保持无"与论文的关联"章节**，绝不凑链接——"如果没联系的话你弄链接上去我都不知道是什么意思"。关联建立后全库验收：有章节的案例数 + 无章节的案例数 == 案例总数，且无章节案例需经匹配确认（不是漏配）。
- **全量执行法（2026-08-03 实测，121/121 全覆盖）**：第1步按引用轨处理（论文页有明确引用的案例）；第2步把剩余无关联案例按主旨轨匹配——建 `/tmp/no_assoc_cases.json`（无关联案例要旨索引）+ `/tmp/papers_full_points.json`（25篇论文核心论点全文），3×delegate_task 并行（每批约18案，每案匹配2-4篇论文），严格基于要旨文本判断。执行结果：66案引用轨 + 55案主旨轨 = 121/121 全部有"与论文的关联"；论文→案例 284 ≈ 案例→论文 282 双向对称。
- **双轨镜像的"行内多案例"陷阱（实测）**：论文页一条目可含2个案例链接（如"观点4 ↔ [[案例81]]；[[案例34]]——理由"）。镜像到案例页时**必须只把该条目的理由复制给"行首案例"**，行内第二个案例会在第一个案例页里留下 `；[[案例34…]]` 尾巴（本次产生7处混入，全部清理）。镜像后**专项扫描案例页"与论文的关联"章节内是否混入 `[[案例…` 链接**（该章节只应含论文链接），发现即删尾巴。

**正确工作流**：
1. 读取论文 `## 核心论点`（拆成观点1、观点2…）；读取案例库全部 `裁判要旨` 建索引（/tmp/case_yaozhi_index.json：stem→yaozhi，先验证覆盖率为100%）。
2. 按观点↔要旨语义匹配（严格基于要旨文本，不臆造；制度构建/立法构想类论文如无案例对应，如实写"与个案要旨直接对应较少"）。
3. 论文页在 `## 与其他论文的关联` **之前**插入 `## 与案例的关联` 章节：说明行 `> 按"观点↔案例主旨"对应建立（2026-08）：论文核心论点与库内案例裁判要旨的印证关系，非引用关系。`，每条 `1. **观点N（简要）** ↔ [[案例N-YYYY-标题]]——对应理由（要旨如何印证观点，60-150字）`。
4. 链接必须用案例文件完整stem（含年份，如 `[[案例3-2005-孙立兴诉天津新技术产业园区劳动人事局工伤认定案]]`）。
5. **批量前先全库审计现有论文→案例链接**——旧链接有错误实例（张相军篇把"刘自荣抗诉案"错链到案例31李某案，应为案例64刘自荣案；"检例205号"错链到案例31，应链底稿页）。逐条核对标题/当事人/案号后再新增。
6. 批量（24篇）可用 3×delegate_task 并行（每批8篇：子代理读核心论点+要旨索引+参照已验收试点页格式写入），完成后主代理统一做案例页反向"与论文的关联"小节。
7. **案例页反向小节必须带印证说明，禁止裸链接列表**（user correction 2026-08-03: "案例页面感觉反过来和论文只有链接 没有具体内容 看不出啥联系"）。`## 与论文的关联` 每条 = `[[论文页|短名]]——印证说明`（与论文侧"与案例的关联"的对应理由互相镜像），不能只有 `- [[论文页]]` 一行。生成方式：从论文侧章节的 `观点N ↔ 案例` 条目反向推导每条理由。
8. **镜像正则的两大陷阱（AUDIT-BATCH2 2026-08-03 实测）**：① **一行可含2个案例链接**——论文页条目如 `观点4 ↔ [[案例81]]；[[案例34]]——理由`，行首正则 `^\d+\.\s*\*\*(.+?)\*\*\s*↔\s*\[\[(案例\d+-[^\]\n]+?)\]\]——(.+)$` 只捕获第一个案例（案例81），行内第二个（案例34）被漏，导致案例页反向缺失、需手动补（本批2例：案例34/19）。**必须用 `findall` 捕获行内所有 `[[案例…]]`，或按 `；` 拆分后再逐段解析**。② **"观点观点"重复词**——镜像模板若写"本文观点{观点文本}"而来源条目已含"观点N"字样，会产生"本文观点观点1"；镜像前先检查来源格式，模板只用观点编号或只用观点简述，不要重复前缀。

试点格式与验收见 `references/session-2026-08-02-paper-case-pilot.md`。2026-08-03 全量批次（24篇并行3子代理）结果：25篇共**119处**论文→案例链接，66个案例被引用（孙立兴被7篇引用最多）；案例页反向 `## 与论文的关联` 66页，**双向对称119↔119**（论文→案例数 == 案例→论文数），全库197页、未解析链接0。验收必须同时检查双向对称，单向链接多寡不是目标。

### 引用关系匹配（旧逻辑，仅作引用场景补充，非主链接逻辑）

**CRITICAL scope rule (user correction 2026-08): NEVER annotate case pages with paper footnote numbers based on a compilation file alone.** A draft-case compilation docx (e.g. 《论文初稿引用的20个工伤认定案例原文完整版.docx》) may carry "对应论文脚注：[N]" markers, but those footnote numbers are UNVERIFIABLE without the actual paper. Adding a `## 论文初稿引用` section (脚注号+原脚注引文) to case pages was rejected by the user ("你现在做论文脚注没有意义啊 我都没给你论文"). Correct behavior when the paper is not provided: at most create a case LIST page (case wikilink + 争点 + 层级) WITHOUT footnote columns, explicitly noting 脚注以初稿实际编号为准. Only add footnote-level annotations when the actual paper text is in hand. The 20-case list page from this session (`queries/论文初稿引用的20个核心案例.md`) is the correct model — no footnote numbers.

Use this workflow when a literature corpus already has `## 引用案例` sections and the vault contains case entity pages. The goal is a traceable graph, not maximum link count: link only cases that can be matched to an existing, substantive case page with high confidence.

### Corpus-overlap reality check (pilot-verified 2026-08)

**Expect LOW overlap between paper-cited cases and a curated case library — this is normal, not a defect.** In the 工伤认定 vault: 25 papers cited ~103 cases, but only ~5-10 (≈10%) exist in the 121-case library. Reason: scholars cite random 裁判文书网 cases (e.g. 2014 璧山/承德/江阴 local cases), while the library holds curated 公报/指导/检例/典型案例. Consequences:

1. **Do NOT attempt exhaustive per-entry matching** — ~90% of entries will legitimately stay as plain text. Report the unmatched majority as expected, not as failure.
2. **Case-number matching returns ~0 hits across corpora** — papers and library cite different cases; format drift (第0034号 vs 第34号, 全角/半角括号) also breaks naive matching even when the same case is cited. Normalize (strip leading zeros, unify brackets) before any number matching, but do not expect it to be the workhorse.
3. **The ONLY reliable bridge is authoritative identifiers**: scan papers' 引用案例 for `指导案例N号`, `检例N号`, `公报案例`, 最高法典型案例 — these are the cases the curated library actually contains (指导案例40号→孙立兴=案例3, 指导案例69号→王明德=案例11, 检例205号→底稿, 刘自荣=案例64). Build the link set from THESE first; everything else is best-effort 当事人+法院+年份 triple-match.
4. **Verify authoritative IDs against the library before linking** — a bare `grep "91号"` can false-positive on unrelated pages that merely mention the number; 指导案例91号 (沙明保案, 房屋强拆) is NOT a 工伤 case and correctly stays unlinked in a 工伤 library.

### Audit existing links FIRST (pilot-verified 2026-08)

Existing paper→case links may be WRONG and must be verified before adding new ones. Found in this vault: 张相军篇 linked 刘自荣工伤认定纠纷抗诉案 to 案例31 (李某案) — a completely different case — because an earlier matcher paired by loose keyword. 检例205号 was also mislinked to 案例31 instead of the 底稿 page. **Audit rule**: for every existing `[[案例N-…]]` in a paper's 引用案例 section, re-verify that the case page's title/facts actually match the cited case (当事人+案号+案情). Fix wrong links BEFORE adding new ones — the user will spot them in Obsidian and lose trust.

### Scope and mapping before editing

1. Inventory recursively: literature pages, case pages, and all existing wikilinks. Never rely on filenames alone; read each case page's YAML title and identifying facts.
2. Extract each paper's `## 引用案例` section and build an explicit mapping table: paper page → cited display name → target case stem → evidence/rationale → confidence.
3. Before editing more than 10 pages, freeze the affected-page list and mapping list. Separate exact title matches, exact guiding-case/检例 identifiers, case-number matches, and anonymized/short-name matches.
4. Do not link generic statistics, foreign cases, cases mentioned only in passing, or citations for which no existing case page can be verified. Leave those entries as plain text and report them as unmatched.

### Matching rules

- Prefer exact title or official identifier matches (指导案例号、检例号、公报案例 title).
- For anonymized paper citations such as `何某某`, `孙某某`, or `王某某`, link only when the court/administrative agency, procedural result, distinctive facts, and the case page's source support the correspondence. Preserve the paper's original display name with an alias: `[[实名案例页|论文中的匿名称谓]]`.
- Do not use loose substring or common-word matching. Generic terms such as `工伤认定案`, `北京`, or a shared year produce false candidates.
- If a citation's case number is absent from the case page and the facts are not distinctive enough, do not infer the match.

### Editing and reverse edges

1. In the paper, replace only the relevant case name/identifier inside `## 引用案例`; preserve the explanatory holding and all other sections.
2. Use the existing case page's `## 相关论文` section for the reverse edge when appropriate. Add only missing direct citing-paper links; do not duplicate an existing link or replace thematic links with a false claim of direct citation.
3. Use full-line context for a targeted patch when a short substring does not match. After every failed patch, reread the actual section before retrying; never assume a false return means the file changed.
4. Do not create new case pages during a link-only batch. New case ingestion is a separate, user-approved scope.

### Acceptance checks

- Count paper → case links and unique paper–case edges separately because one paper may display two names for the same case.
- For every edge, verify the target case stem exists and the case page links back to the paper page.
- Scan the complete vault recursively for dead links. Classify documentation examples in `SCHEMA.md` and historical references in `log.md` separately from live entity-page dead links; do not silently report them as newly created defects.
- Re-parse YAML and verify source paths, required headings, and unchanged substantive sections on all edited pages.

Keep the user-facing report action-first and short: affected paper/case counts, notable anonymized mappings, unmatched-citation policy, verification counts, and the next deferred sub-batch. See `references/session-2026-07-31-paper-case-links.md` for the detailed recipe and verification skeleton.

## 三角互联（案例↔论文↔法规范, AUDIT-BATCH6 2026-08-03）

After paper↔case linking is done, complete the third edge: **statute references in case/paper body text → norm pages**. 案例页正文大量引用 `《工伤保险条例》第十四条` 等法条但最初全是纯文本（0链接）；法规范页→案例已有（115处）。批量链接化实测：

- **映射表**（按法规范页存在性过滤，库内无对应页的不链接——如《广东省工伤保险条例》《职业病防治法》留纯文本）：
  `工伤保险条例`→`[[工伤保险条例（2010修订）|工伤保险条例]]`、`中华人民共和国行政诉讼法`→`[[行政诉讼法（2017修正）相关条款|行政诉讼法]]`、`社会保险法`→`[[社会保险法（2018修正）工伤保险章节|社会保险法]]`、`工伤认定办法`→`[[工伤认定办法（2011）|工伤认定办法]]`、`行政复议法`/`行政强制法`同理。
- **替换顺序**：先长后短（`中华人民共和国行政诉讼法` 必须在 `行政诉讼法` 之前），否则短名先替换会吃掉长名前缀。
- **结果**：案例→法规范629处（60页）、论文→法规范169处（23页）、法规范→案例115处——三角三边全通后跑 MODULE-END CHECK（死链0/嵌套0/YAML 0）。
- **反向边不必机械对称**：法规范页已按规范要点组织案例链接（115处），正文引用链接是单向的（案例/论文→法规范），不需要每个正文引用都回链——三角互联的"对称"指三边都存在，不是逐条对称。

### 批量替换的嵌套陷阱（CRITICAL）

`re.sub(r'(?<!\[\[)' + name, link, s)` 只排除了链接**开头**的 `[[`——已链接页面（试点页/原本就有 `[[工伤保险条例（2010修订）]]` 的页面）的**别名部分**（`|工伤保险条例]]` 里的明文"工伤保险条例"）会被二次替换，产生 `|[[工伤保险条例（2010修订）|工伤保险条例]]]]` 嵌套（本次11页）。检测：扫描 `'[[[[' in s` 或 `re.search(r'\[\[[^\]\n]*\[\[', s)`。修复：`re.sub(r'\|\[\[(法规名)\|([^\]]+?)\]\]\]\]', r'|\2]]', s)` 还原嵌套。**预防**：批量前先排除"目标页面已含该链接"的情况（试点页单独跳过，或替换前检查目标名是否已在 `[[` 之后）。

## Research-Design Page Upgrade (研究设计页升级)


When the user asks whether the 写作思路/research-design pages need improvement, audit them against the five-question writing methodology (五问框架) — not just wiki mechanics. **Report first** (要不要完善 / 怎么完善 / 完善后的效果), edit only after explicit user confirmation.

### Audit dimensions (read-only pass)

1. **五问框架完整性**: Q1 (一文一问 + 四件套结构), Q2 (四层读者), Q3 (问题意识两要件+三来源), Q4 (资料), Q5 (验收清单) — each must be project-specific, not a copy of the methodology page.
2. **素材状态核实纪律**: NEVER trust the Q4 素材清单 status column — cross-check against log.md entries and actual `ls raw/` contents. Stale statuses (e.g., "最高法参考10个文件待摄入" when already ingested) mislead future sessions into duplicate or omitted ingestion.
3. **样本选取标准**: 三层样本结构 — 权威样本 (官方汇编案例), 统计样本 (编译集), 补充样本 (裁判文书网按需) — each with 选取标准/时间范围/用途. The 双样本结构 argument (权威保证覆盖面 + 统计提供量化验证) answers the "样本偏斜" reviewer attack.
4. **资料截止日期与核验状态**: 案例数据截止日期, 法律规范现行版本 (e.g., 《工伤保险条例》2010修订版, 法释〔2014〕9号), 文献核验状态.
5. **五项硬门禁状态表**: 来源真实性/法律有效性/引注完整性/论证充分性/期刊适配 mapped to project status (✅/⚠️) + next step per gate.
6. **反向链接**: research-design pages must be linked FROM concept and paper pages, not just link out. Verify with `grep -rln "<研究设计页名>" --include="*.md" .` in terminal.

### 论点—证据—引注矩阵 (claim-evidence matrix page)

Create a `research-design/` matrix page as the writing-execution tool: per analysis dimension, each 子主张 row = 主张 | 证据类型 | 具体证据（案号/文献/页码）| 支持范围 | 反方材料 | 核验状态.

- Only `VERIFIED` claims enter the final draft; statistics stay `待核`/`缺证据` until the dataset (e.g., 121案编译集) is actually ingested. NEVER fabricate percentages.
- **统计口径清单 must be predefined**: 年代切片认定率, 改判率定义 (撤销+变更? 含发回重审?), 法条引用频率变迁, 撤诉/放弃比例, 裁判理由分化度. Undefined 口径 makes statistics unreproducible and fails reviewer scrutiny.
- 反方材料 column must never be empty — a claim without a counter-position is advocacy, not argumentation.

### 学术史争议地图 (literature controversy map page)

When the 论文实体页 corpus is healthy (positions verified), build a `concepts/` controversy-map page as the 文献综述素材 for "问题的提出" (学界研究到哪了) and as Q3 理论空白 evidence.

- **Extract positions first, never from memory**: survey ALL paper pages in one pass by pulling `## 核心论点` + `## 主要结论` sections (regex `r'## 核心论点(.*?)(?=## |\Z)'`), print filename + truncated sections, then organize by stance. Quote the pages; positions must trace to the (recently repaired) entity pages.
- **Page structure per controversy**: 争议问题 → 阵营表（立场 / 代表文献 wikilinks / 核心主张）→ 分歧点 → 实务映射（实证锚点：检例号、643案/141件/100案类统计）→ 未决问题（研究缺口，mapped to a paper dimension）. The 未决问题 row IS the group-case study's entry point — each controversy should map to one analysis dimension.
- **Cover the three core controversies** (举证责任分配 / 不确定法律概念解释 / 立法模式) + 延伸集群 (程序与监督, 新就业形态). 阵营对立 = pre-stocked 反方材料.
- **Backlink discipline for new center-node pages**: immediately after creating, add `- [[页面名]]` to 相关概念 of stable pages (研究设计页 + related concept pages) via a small script that inserts into each `## 相关概念` section. Do NOT bulk-edit entity pages in the same pass — if a parallel session is actively editing them (check log.md tail for recent entries), defer entity-page backlinks and record the deferral in log.md.
- **Known dead-link false positives**: SCHEMA.md's `[[wikilinks]]` doc example and log.md historical references to renamed pages are NOT defects — exclude or report separately, don't "fix" them.

See `references/session-2026-07-31-controversy-map.md` for the full session (extraction snippet, page skeleton, backlink insertion script, verification numbers).

### Log ordering

log.md is append-only and may be written by parallel sessions. Before appending, read the file tail and insert at the TRUE end (chronological order) — inserting at the last line you remember can land your entry in the middle of the log.

See `references/session-2026-07-31-research-design-upgrade.md` for the full session: audit findings, the 4+2 upgrade list, Q4 stale-status corrections, matrix structure, and verification results.

## Pitfalls

- **CRITICAL: Recursive vault scans.** This wiki stores pages below nested directories such as `entities/引用文献/`, `entities/案例/`, and `entities/底稿/`. A top-level `os.listdir()` or `Path.glob('*.md')` scan falsely reports valid literature links as dead. Build the page-stem set with recursive traversal (`Path.rglob('*.md')`) before judging links.
- **CRITICAL: Validate YAML after every frontmatter patch.** When replacing a frontmatter block with surrounding context, an accidental leading space before a top-level key (for example ` type: entity`) can change YAML structure. Re-parse the edited page immediately and inspect the diff; never assume a successful patch means valid frontmatter.
- **CRITICAL: User-facing audit reports must be action-first.** For this user's legal-Wiki work, do not lead with a long inventory. State the first batch, exact pages, one change per page, and a short verification result. Keep later batches deferred until the user can see and accept the first result.
- **CRITICAL: Vault-root ghost files.** Obsidian auto-creates 0-byte `.md` files at the vault ROOT when the user clicks an unresolved wikilink. Subdirectory-only scans (entities/concepts/research-design) miss them — run `find "$WIKI" -maxdepth 1 -name '*.md' -size 0` in every health check, grep for inbound links, then delete or retarget.
- **CRITICAL: `&`-suffix ghost files resurrect via workspace.json (GHOST-AMP-CLEANUP 2026-08).** Obsidian auto-creates 0-byte `案例N-…&.md` files (or any `&`-bearing variant) when a link with `&` is clicked, AND `.obsidian/workspace.json` → `lastOpenFiles` stores their paths — so Obsidian **recreates deleted ghost files on every launch**. Deleting the files alone never fixes it. Fix: (1) archive ghosts to `.maintenance/ghosts/`; (2) strip ALL `entities/案例` paths containing `&` from workspace.json (re-check with `grep -c '&\.md' .obsidian/workspace.json` — first pass can miss entries); (3) add `"userIgnoreFilters": [".maintenance","ghosts"]` to `.obsidian/app.json` so backup dirs don't display; (4) tell user to Cmd+Q fully quit Obsidian (in-memory workspace overwrites cleanup on window-close).
- **CRITICAL: Graph View ghost nodes ≠ missing files — example wikilinks in maintenance docs get parsed even inside backticks (GRAPH-CLEANUP 2026-08).** When Graph View shows blank/unresolved nodes but the file system is clean, the culprit is example `[[wikilinks]]` in SCHEMA.md / log.md / 台账 (e.g. `[[wikilinks]]`, `[[目标|显示]]`, `[[案例N-标题|X案]]`, `[[A|[[B|C]]]]`). **Obsidian's link graph parses wikilinks inside backticks too** — backticks only affect rendering, not link resolution. Fix: write example links as plain text (strip the `[[ ]]` entirely, add `（示例）` note) in ALL maintenance docs — including new log entries you append yourself (self-referential trap: a log entry describing this very bug reintroduced 4 ghost nodes). Verify with a vault-wide unresolved-link scan: parse every `[[...]]`, split alias on `\|` or `|`, check target stem exists. A clean file list does NOT mean a clean graph.
- **CRITICAL: 核心论点 section header leak.** PDF structural headers (`**一、...**`, `**二、...**`) can be dumped verbatim into `## 核心论点` sections, making them unreadable. Scan for `\*\*[一二三四五六]、...\*\*` patterns in core argument sections and rewrite as proper thesis statements. See `references/session-2026-07-30-wangdongwei-repair.md`.
- **CRITICAL: Wrong section as conclusion.** pymupdf may grab a mid-body numbered section (e.g., `三、再造`) as the conclusion instead of the actual `余论`/`结语` at the paper's end. Check that conclusion text doesn't start with a numbered section header. Search for `余论` as an additional conclusion marker. Same reference file.
- **CRITICAL: Three-section triage.** When one of `## 摘要` / `## 核心论点` / `## 主要结论` has a defect, check ALL THREE — they often fail together. Wang Dongwei's article had abstract typo + core-argument header leak + mid-body-as-conclusion simultaneously.
- **CRITICAL: Keep `sources:` in sync with PDF filenames.** After renaming PDFs (e.g., stripping curly quotes), verify every frontmatter `sources:` path with `os.path.exists`. Prefer renaming the file to the clean name.
- **CRITICAL: Subagent lazy markers and format drift.** Subagents may write `*提取受限*` disclaimers instead of extracting, and `## Header\nText` without the blank line — both pass batch-level "completed" status while failing content. Verify per-file content after every delegation batch; re-extract manually when found.
- Don't mass-ingest without user buy-in. Survey, discuss, ask scope.
- Don't silently filter duplicate files. Tell the user.
- Batch PDF extraction goes through a temp file, not inline.
- **CRITICAL: PDF format artifacts survive into wiki pages.** Always run the
  format check above after batch ingestion. Common artifacts: ］［ brackets,
  broken lines, corrupted keywords. See "PDF Format Artifact Cleanup" section.
- **CRITICAL: Cross-reference network is mandatory.** Content + no dead links is NOT
  enough. If 25 papers each link only to the methodology page and 1-2 concepts, the
  wiki is a pile of isolated islands. Every paper MUST link to the anchor/draft (底稿)
  AND to at least 2 other papers, with specific theoretical connections. Run the
  cross-reference check after every ingestion batch. See "Cross-Reference Network
  Construction" section above.
- **CRITICAL: Dead links after ingestion.** Always run the dead-link check above
  after creating pages. Zero dead links is the target. The user WILL find dead
  links in Obsidian and lose trust in the wiki.
- **CRITICAL: "详见原文" is NOT acceptable content.** If auto-extraction fails,
  re-extract with a dedicated script reading all pages with multiple regex patterns.
- **CRITICAL: Curly-quote filename mismatch.** Chinese PDF filenames from CNKI
  frequently contain Unicode punctuation (curly quotes ""、——、：) that differs
  from ASCII equivalents in user-provided lists. A file listed as
  `论工伤认定"循环诉讼"...pdf` with straight quotes will appear MISSING.
  Always verify filenames against the filesystem with `ls` or
  `search_files(target='files')` before assuming absence.
- **CRITICAL: search_files false negatives for Chinese patterns.** Content search via
  `search_files` can return 0 matches for Chinese regex patterns that `grep` finds
  dozens of (observed: pattern `五问研究设计|群案研究：五问` → 0 results, while
  `grep -rn` found 38 matches across 38 files). NEVER conclude "no backlinks /
  isolated page / missing term" from a search_files zero result alone — cross-validate
  suspicious zeroes with terminal `grep -rn` before reporting a negative finding or
  starting remediation work. This almost caused a wrong "研究设计页是孤岛" report.
- **CRITICAL: read_file dedup + write_file corruption.** Never use `read_file()` → string replace → `write_file()` in a loop for bulk edits. The `read_file` dedup system returns cached content with line-number prefixes (`6|tags: [...]`), which get written back as actual content, corrupting files to zero-byte. Use `sed` on the filesystem for bulk tag/string replacements instead.
- **CRITICAL: Each page must be in index.md.** After batch-creating entity pages from compilations, rebuild `index.md` to list every single page with `- [[slug]]`. Section headers without individual links will look empty to the user.
- **CRITICAL: YAML frontmatter quote escaping.** Chinese PDF filenames with curly quotes
  (""") carried into `title:` and `sources:` fields cause Obsidian to mark pages red
  (frontmatter parse failure). Always run the YAML quote check after batch ingestion
  and strip ALL quotes from frontmatter fields. See "YAML Frontmatter Quote Escaping" section.
- **CRITICAL: Fragmented conclusions.** pymupdf regex may extract mid-text fragments
  as conclusions (starting with `，` or `；`). Always check conclusion quality — if it
  starts with punctuation or is <100 chars, manually rewrite from the PDF's actual
  concluding section. See "Fragmented Conclusion Detection" section.
- **Chinese punctuation in execute_code string literals.** In older Hermes
  runtimes, full-width punctuation like `、` (U+3001) and `""` (U+201C/U+201D)
  could cause `SyntaxError: invalid character` when inline in Python source
  inside `execute_code`. As of 2026-07-30, the current runtime handles Chinese
  Unicode text in string literals correctly. The `write_file` to `/tmp/` →
  `open().read()` approach remains a safe fallback if any encoding issue
  arises, but is no longer strictly required.
  See `references/session-2026-07-30-conclusion-reextraction.md` and
  `references/session-2026-07-30-threesection-repair.md` for details.
- **CRITICAL: Fullwidth English abstract contamination.** CNKI PDFs contain
  English abstracts in fullwidth characters (`ＯｎｔｈｅＪｕｄｉｃｉａｌ...`)
  after the Chinese conclusion. The naive regex `[Ａ-Ｚａ-ｚ０-９...]+` to strip
  them is too aggressive — it nukes Chinese text that has scattered fullwidth
  chars. Instead, remove fullwidth-English-dominant LINES:
  `if fw_count > cn_count * 2 and fw_count > 10: continue`. See the reusable
  `clean_conclusion()` function in
  `references/session-2026-07-30-conclusion-reextraction-batch2.md`.
- **CRITICAL: Embedded page headers in mid-sentence text.** PDF page headers
  (`0\n6\n中州学刊2020 年第12 期\n`) get embedded mid-sentence during extraction.
  Strip them with targeted regex BEFORE running the line-join regex, otherwise
  they merge into the text and create garbage like "在06中州学刊2020年第12期效果上是存疑的".
- **CRITICAL: Section headers split across newlines.** 王敏's `结语` header
  appears as `结\n语` (two chars on separate lines) in extraction. A simple
  `find("结语")` fails. Always try both `"结语"` and `"结\n语"` patterns.
  Also check for `结　语` (fullwidth space U+3000 between chars).
- **CRITICAL: Surgical section replacement with regex.** When replacing a single
  section (e.g., `## 主要结论`) in a wiki page, use the pattern
  `r'(## 主要结论\n)([\s\S]*?)(\n## |\Z)'` to replace ONLY that section's content
  while preserving all other sections. Do NOT reconstruct the full file manually —
  this risks dropping or corrupting other sections.
- **Don't create compilation summary pages INSTEAD of individual pages.** Users expect to click each individual case/interpretation/Q&A, not just a page describing the compilation. Summary pages are supplementary, not a substitute.
- **One vault per research project.** When the user has multiple distinct research domains (e.g., 工伤认定 and 长三角治理), create separate wiki vaults. Mixing unrelated domains clutters Graph View, dilutes search, and makes tag taxonomies unmanageable. Cross-project methodology reuse happens via Skills, not shared wiki pages.
- **CRITICAL: DOCX separator vs subtitle clash.** When parsing Chinese case compilations (.docx), separators are long dash lines (`————————————————————————————`, ~28 em dashes). Some case titles contain `——` (2 dashes) as subtitle delimiters. Using `'——' in line` for separator detection silently drops all subtitle-bearing cases. Use `line.count('—') > 5` instead. See `references/docx-case-parsing-lessons.md`.
- **CRITICAL: Duplicate filenames in batch creation.** When two cases generate the same slug (e.g., "李某" in two different years), the second `write_file` overwrites the first. Use a counter dict to append `-2`, `-3` suffixes. See `references/docx-case-parsing-lessons.md`.
- **CRITICAL: Batch reverse-link insertion must exclude self-links and dedupe.** When programmatically inserting "与其他案例的关联" reverse entries across many case pages, a page must never link to itself — the batch script inserted `- [[案例74-韩某…]]` (target == the page being edited) with a misattributed description into 26 pages in one pass. Also check for duplicate entries of the same target (one correct entry + one prefixed `与[[...]]的关联` variant). Post-insertion audit: regex per page for `\[\[<own-stem>` (self-link) and Counter over link targets (duplicates); delete the malformed lines. The same bug family can occur when reverse-linking any entity type (papers, norms).
- **CRITICAL: Truncated wikilinks that swallow the next section heading (CASE83-LINK 2026-08).** A malformed link like `[[案例62-某劳务公司…案## 相关概念` (missing closing `]]`; the following `## 相关概念` heading gets absorbed INTO the link target) breaks the page structure AND the link. It survives dead-link scans because the target string contains `##` and no closing bracket pair — a plain `[[…]]` regex never sees it. Detection: scan for `\[\[[^]]*##` (link containing `##`) and compare per-file `[[` vs `]]` counts (unbalanced = truncated link). This is the only surviving malformed link after the year-rename batch — batch renames must include a truncated-link sweep, not just the four normal link forms.
- **CRITICAL: OPT execution-record numbering drift.** Execution-record OPT numbers can drift from the task ledger (observed: the second batch of OPT-001 was logged as `OPT-002` while ledger OPT-002 is a *different* task — the case-generator script). Before appending an execution record, check its number against the ledger's task status table; when a conflict is found, keep historical entries verbatim and add a clarification note in the ledger instead of rewriting history.
## Entities Subdirectory Organization

When entities/ exceeds ~30 files, subdivide by type for navigability:

```
entities/
├── 引用文献/    # Academic papers (25 papers)
├── 范文/         # Journal style-reference papers; NOT academic citations
├── 底稿/         # User's own draft/anchor paper
└── 案例/         # Court cases (53+ cases)
```

**Rules:**
- 范文 are for style learning only — clearly separate from 引用文献 and annotated in index.md
- Obsidian resolves `[[wikilinks]]` by filename across the vault, so NO path prefixes needed
- After moving/reorganizing, verify 0 dead links vault-wide
- Update index.md categories + SCHEMA.md to reflect the subdirectory layout

## Ingestion Order: Papers Before Cases

When both papers and cases need ingesting, **always recommend papers first**:

- Papers build the concept skeleton; cases fill in empirical flesh
- Without concept pages, case entity pages have nothing to link to → become orphan islands
- Papers reveal which dimensions matter for tagging → prevents tag rework
- Academic history dimension needs literature base before cases are analyzed

State this recommendation to the user proactively when they ask "papers or cases first?"

## Journal Style Template Step

When the user has a specific target journal (e.g., 《政治与法律》), add a step
**after** research design but **before** reference paper ingestion:

1. Ask user for 2-3 sample papers from the target journal
2. Ingest them as entity pages
3. Create a concept page analyzing: format specs, writing style, argumentation patterns,
   and relevance to the group case research
4. This becomes the "style template" the agent follows when drafting the paper

## Updated Wiki Initialization Sequence (MANDATORY)

When user asks to create a new research wiki:
  1. Ingest the CSSCI paper-writing methodology as a concept page
  2. Ask the user for their research design/problem consciousness
  3. Write the research design to `research-design/`
  4. (Optional) Ingest journal style templates if target journal is known
  5. Ingest reference papers → entity pages + concept pages
  6. Ingest cases → entity pages (linked to concepts from steps 4-5)
  7. Only then begin paper drafting

  Never skip steps 1-3 and jump straight to material ingestion.

## Parallel PDF Extraction with delegate_task

For 15+ papers, use parallel `delegate_task` subagents (8-9 papers each):
- Each subagent uses pymupdf to extract text and output structured JSON
- JSON schema MUST include: title, author, affiliation, journal, year, abstract,
  keywords, key_arguments (3-5 detailed), methodology, conclusions, cases_cited,
  statutes_cited, concepts (for wiki cross-linking)
- After subagents complete, main agent reads JSON and writes wiki pages
- Keeps main context clean and is 3x faster than serial extraction
- marker-pdf requires ~5GB disk. Warn the user.
- Store wiki path in memory so it persists across sessions.

### Subagent output reliability

- A subagent may report "completed" but **fail to write its JSON output file** to the
  specified `/tmp/` path. Always verify with `ls -la /tmp/batch*_papers.json` after
  all subagents report done.
- If a subagent's JSON is missing, do NOT re-dispatch. Instead, write a standalone
  extraction script to `/tmp/` and run it directly with `terminal()`. This is faster
  and more reliable than retrying the subagent.
- Pattern: `write_file("/tmp/extract_batchN.py", script)` → `terminal("python3 /tmp/extract_batchN.py")`

### pymupdf metadata unreliability

pymupdf text extraction from academic PDFs produces **unreliable metadata**:

- PDF first pages often contain journal headers (e.g., "Evidence Science Vol.24 No.1
  2016") instead of the paper title.
- Author names get misidentified — the second line after title is often an abstract
  or funding note, not the author.
- Abstract extraction fails when PDFs use non-standard "摘要" formatting (brackets,
  full-width colons, etc.).

**Fix**: Always pair auto-extraction with a **manual metadata correction table**:

```python
corrections = [
    {"title": "正确标题", "author": "正确作者", "affiliation": "正确单位",
     "journal": "正确期刊", "year": "正确年份", "filename": "wiki-page-slug"},
    # ... one per paper
]
```

Use the filename (which the user named as `标题_作者.pdf`) as the ground truth for
title and author. The auto-extracted text is only reliable for abstract, keywords,
section headings, and statutes.

## Compilation File Handling

When a source `.docx` contains multiple entities (e.g., 133 cases, 29 guiding cases, 84 Q&A entries, dozens of judicial interpretations), **extract every individual item as its own entity page.** Do NOT create just one summary page.

### Index Must List Every Page

After batch-creating pages from a compilation, **every single entity page must appear as a `- [[page-slug]]` wikilink in `index.md`**. Section headers alone (e.g. "公报案例（49个）") are NOT sufficient — the user sees nothing clickable in Obsidian.

When building/rebuilding the index after batch ingestion:
```python
# Rebuild index with ALL individual pages listed
for g in sorted(gazette_cases):
    index += f"- [[{g}]]\n"  # every single case
```

### Scope verification and mapping

Before updating existing case pages from a compilation, follow `references/docx-scope-and-mapping.md`: resolve the actual path, inspect the DOCX body, count real case entries, map source cases to existing pages, separate irrelevant entries, report the affected-page scope before large batches, and verify the final page/link inventory. Do not trust a case count stated only in the filename.

For multi-source case-page revalidation, also follow `references/docx-case-compilation-revalidation.md`. It covers DOCX XML fallback parsing, directory-versus-body detection, inline and bracketed section markers, revision deduplication, source-level mapping, statute extraction, file-stem wikilinks, and acceptance checks that must run again after parser corrections.

### Workflow

1. Write a parser to `/tmp/parse_<type>.py` using `python-docx`
2. Parse and save structured JSON to `/tmp/<type>_out.json`
3. Use `execute_code` to batch-create entity pages from the JSON
4. Each page must have proper YAML frontmatter with detailed tags

### Parsing pattern

```python
import docx, json, re
doc = docx.Document(path)
for p in doc.paragraphs:
    t = p.text.strip()
    m = re.match(r'pattern', t)
    # extract fields: title, date, keywords, yaozhi, etc.
```

**CRITICAL: Separator vs subtitle detection.** Chinese case compilations separate cases with long dash lines (`————————————————————————————`, ~28 dashes). Case titles may also contain `——` (2 dashes) as subtitle delimiters. Never use `'——' in line` for separator detection — use `line.count('—') > 5` to distinguish real separators from subtitles. Full parser walkthrough, duplicate-filename avoidance, field extraction regexes, legal basis normalization, and auto-classification patterns: `references/docx-case-parsing-lessons.md`.

## Chinese Tag Preference

Users working with Chinese legal materials **strongly prefer Chinese tags** over pinyin in Obsidian's Graph View. SCHEMA.md tag taxonomy should use Chinese labels: `工伤认定` not `gongshang-renting`.

When converting pinyin to Chinese tags across many files, use `sed`:

```bash
sed -i '' \
  -e 's/gongshang-renting/工伤认定/g' \
  -e 's/falu-shiyong/法律适用/g' \
  entities/*.md concepts/*.md research-design/*.md
```

## Tagging Protocol

Every entity page must have **detailed, multi-tag annotations**, not just a single generic tag. When batch-creating pages from parsed JSON, assign tags based on content keywords:

- Contains "工伤/工伤保险" → add `工伤认定`
- Contains "举证/证据" → add `证据问题`
- Contains "程序/受理/中止/时效" → add `程序违法`
- From 最高人民法院 → add `最高人民法院`
- Discusses 新业态/平台/骑手 → add `新业态`

## Directory Extensions

The wiki supports a `research-design/` directory for research methodology pages (type: `research-design`). This is valid alongside the standard `entities/`, `concepts/`, `comparisons/`, and `queries/` directories.
