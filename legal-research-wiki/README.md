# 法学研究 Wiki 建库 Skill

把论文、案例、法条和研究方法整理成可追溯、可审计、可继续维护的法学研究 Wiki。适合在研究项目开始时建立底层资料结构，也适合已有 Wiki 的分批扩充。

> 运行时入口是 [`SKILL.md`](SKILL.md)。本页解决“什么时候用、怎么开始、如何验收”；详细规则按需阅读 `references/`。
>
> **当前版本：v4.1.0（2026-08）**。新增图片、音频、本地 PDF 和批量参考文献摄入，以及闭世界查询纪律与 Obsidian headless 同步说明。

## 适合解决什么问题

- 研究材料散落在 PDF、DOCX、网页和 Obsidian 笔记中，缺少统一来源登记。
- 论文、底稿、案例和法条之间没有稳定的双向链接。
- 批量摄入后出现 PDF 残留、空壳页面、YAML 错误或标题格式问题。
- 需要在写作前确认材料范围、证据状态和 Wiki 质量，而不是直接让模型“补全”。

## 核心能力

| 能力 | 结果 |
|---|---|
| 范围优先摄入 | 先勘察目录和授权范围，再确认批次，避免无边界扫描整个 Vault |
| 多格式提取 | 支持 PDF/DOCX/图片/音频进入可复核的 Markdown 工作层；OCR、视觉与转录能力按宿主实际配置启用 |
| 关系网络 | 建立论文↔底稿↔案例↔法条的可追溯链接，而不是只堆标签 |
| 六维质量门禁 | 检查摘要、结论、PDF 残留、关键词、YAML 和标题空行 |
| 学术可用性 | 区分假说与事实、来源线索与已核验材料，保留证据缺口 |

## 典型工作流

```text
勘察范围 → 确认批次 → 读 SCHEMA/index/log → 摄入 → 六维检查 → 链接复核 → 记录台账
```

建议每批只处理有限页数，并在进入下一批前完成：死链检查、YAML 检查、六维质量检查和交叉引用检查。

## 快速安装

### 当前优化分支

分支尚未合并到 `main` 时，请按[根 README 的当前分支安装](../README.md#current-branch-install)，把完整技能目录复制到 Hermes 或 Codex。

### 合并到 `main` 后的 Hermes Skills Hub

```bash
hermes skills install shawndeng321/hermes-obsidian-legal-cssci-wiki-writing-skills/legal-research-wiki
```

无交互终端加 `--yes`：

```bash
hermes skills install shawndeng321/hermes-obsidian-legal-cssci-wiki-writing-skills/legal-research-wiki --yes
```

## 第一次使用

给 Hermes 或 Codex 的任务应明确范围、资料入口和写回权限，例如：

```text
使用 legal-research-wiki。只读取指定的 research/2026 行政法项目目录，先检查 SCHEMA.md、index.md 和 log.md，
提出本批 5—8 页的摄入计划。不要扫描其他目录，不要写回任何文件，先列出待确认的范围和质量门禁。
```

摄入前先固定：

1. 允许读取的目录和原始文件范围；
2. 本批处理的页数、类型和命名规则；
3. 来源登记、版本日期和精确定位要求；
4. 允许写回的具体文件，以及备份位置。

## 配套技能与脚本

- 维护与修复：[legal-wiki-audit-repair](../legal-wiki-audit-repair/)
- 论文写作：[chinese-law-paper-writing](../chinese-law-paper-writing/)
- 批量 PDF 提取：`scripts/batch_extract_papers.py`
- 多模态摄入：`references/multimodal-image-ingest.md`、`references/multimodal-audio-ingest.md`、`references/multimodal-pdf-extraction.md`
- 批量参考文献：`references/multimodal-bulk-refs.md`
- PDF 文本残留清洗：`scripts/clean_pdf_artifacts.py`

脚本默认偏保守：先 `--dry-run`，写入时提供调用方指定的备份目录；不要把作者本机路径、整库路径或未经确认的批量范围写进命令。

## 适用范围与边界

适用于法学论文、案例研究、法条和研究方法材料的知识库整理。不替代法律意见、诉状、合同审查或客户法律建议；不把来源线索自动升级为已核验事实。

## 许可证

MIT © 2026 Shawn Deng
