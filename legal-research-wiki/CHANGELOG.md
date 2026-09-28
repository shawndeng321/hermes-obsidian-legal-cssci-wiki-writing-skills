# 更新记录

新增能力或规则递增次版本号，措辞与格式修订递增修订号，面向所有使用者的结构性调整递增主版本号；变更同时更新 `SKILL.md` 的 `metadata.version`、技能包根目录的 `bundle-release.json` 与 README。

## 5.0.1（2026-09-28）

- 仓库更名为 `shawndeng321/legal-academic-research-skills`：更新器的清单地址与 README 中的安装命令随之更新。旧地址由 GitHub 自动跳转，已安装的用户不受影响。

## 5.0.0（2026-09-25）

从单一研究项目中积累的经验，改写为适用于任何法学领域的通用建库技能。

- `SKILL.md` 重写（约 107 KB → 约 16 KB）：保留范围优先、材料边界（闭世界查询）、研究思路先行、来源与分析分开、模块化验收等纪律；细节移入按主题组织的参考文件。
- 20 份会话记录（`session-*.md`）合并为 5 份主题参考文件：`pdf-paper-ingestion.md`、`case-ingestion.md`、`linking-and-cross-references.md`、`research-design-pages.md`、`literature-audit-and-repair.md`；删除其中的具体作者、案例编号、样本数量、本机路径和个人信息。
- 移除项目专属规则：固定的三层案例分类、三维分析框架、特定标签词表与论文主题分类、特定期刊的格式实测值；改为“先问用途，再按项目设计”，并给出可选的常见方案。
- `legal-norm-hierarchy-and-reply-ingestion.md` 重写为通用的法源、规范层级与法规范摄入流程；对司法解释与规章的关系改用审慎表述。
- `pitfalls-and-lessons.md`、`statistics-landing-and-case-matching.md`、`docx-case-parsing-lessons.md` 通用化；多模态与模型编排参考文件改为宿主中立，增加 Hermes / Claude Code / Codex 的能力对照。
- 新增“技能包更新预检”中的 Claude Code 插件通道与“运行环境”说明：相对路径以技能目录为基准，不绑定宿主工具名，不写死 `/tmp`。
- 修复（发布前审查）：`clean_pdf_artifacts.py` 原先删除全页的 `【】`，会损坏案例页的 `【裁判要旨】` 等标签，并把 `［1］` 注码变成紧贴正文的数字；现只处理论文页的摘要、关键词、核心论点、主要结论四个章节，注码整体删除。
- 修复（发布前审查）：`check_wikilinks.py` 在 Python 3.9 上无法运行，且把 `[[目标\|别名]]`、`[[目标.md]]` 误报为死链；现按 Obsidian 规则解析别名、锚点、`.md` 后缀与附件嵌入，跳过隐藏目录和备份，单列畸形链接，新增 `--strict`。
- 预检与示例命令改为 `python3`（Windows 用 `py`）；macOS 默认没有 `python` 命令。
- 兼容性：`description` 改为“英文开头句 + 中文触发词”（约 200—240 字符，Codex 与 Hermes 上限均为 1024）。开头一句不超过 57 字符，因为 Hermes 在系统提示的技能目录中只显示前 57 个字符；后半部分的中文触发词供 Claude Code、Codex 自动选用；Claude Code 插件安装时跳过更新预检，不再每次加载都弹出命令权限确认。
- 新增 `assets/templates/`：20 个页面模板（SCHEMA、index、log，以及案例、论文、概念、比较、法规范、规范实体/版本/条款版本、研究设计、论点证据引注矩阵、期刊风格观察卡、范文、底稿、争点导航、会话交接、行文思路页），以一个实际运行的法学研究库为蓝本通用化，不含原库内容。
- 找回并通用化本机旧版中从未上传的内容：“知识库与论文写作双轨隔离”（写入 SKILL.md）、`references/draft-version-sync.md`（论文草稿新版本同步）、`references/norm-versioning.md`（规范时序版本、七类研究对象、历史案件两层评价、试点方法）、`docx-footnote-extraction.md` 中引用位自带方括号时的 `[[脚注N]]` 形态。
- `check_wikilinks.py` 把 `drafts/` 中的链接列为容忍类（`[[脚注N]]` 汇总报告），把根目录台账与轮转日志 `log-YYYY.md` 视为维护文档。
- 新增建库访谈：`references/wiki-design-interview.md`（十组问题：目的、研究问题、将来怎么用、材料、深度、组织、关联、时间维度、质量与边界、维护与协作；新建与加深两种模式；提问规则）与 `assets/templates/wiki-design-brief.md`（Wiki 设计书），接入建库流程第 2 步。
- 新增 `evals/pressure-tests.md`：15 个行为评估场景。
- 新增“配套技能”一节：写明用到其他两个技能的哪些内容，以及未安装时如何处理；跨技能引用改为按技能名查找，不再使用 `../../其他技能/` 相对链接（Hermes 等宿主可能把技能分放在不同子目录，相对链接会失效）。
- 技能包更新器支持分目录安装：按技能名在技能根目录或一层分类子目录（如 Hermes 的 `research/`）中定位各技能，原地备份、更新与回滚；同一技能装了两份时停止并报告。
- 按“模型原生支持多模态”调整：删除图片摄入的“宿主能力检查”与视觉工具路由（模型直接读图，文字存档保留以便检索与溯源）；扫描版 PDF 改为模型直接读页面并逐页转写，专门 OCR 工具仅作数百页以上大批量的省钱选项；模型编排删除“多模态角色先整理、再交给写作模型”的分工，保留“先登记来源、后写作”。音频转录保留（Claude、Codex 等模型不能直接读音频）。

## 4.2.0（2026-08）

技能包按需更新预检；多模态摄入（图片、音频、本地 PDF、批量参考文献、Obsidian headless 同步）。
