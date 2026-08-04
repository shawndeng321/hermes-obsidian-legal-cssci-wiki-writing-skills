# 法学 Wiki 排查修复 Skill

对法学研究 Obsidian/LLM Wiki 进行全库体检、问题分级（P0—P3）、分批整改和复核的核心技能。

**v3.1.0**（2026-08）新增：每日检修制度与三日迭代（DAILY-MAINTENANCE：约10分钟全库回归，连续检修3天必须迭代检修方法，易错点速查）＋统计复核纪律（STATS-REVIEW：类型专属字段机器重算与人工口径交叉核对，差异逐项归因，不直接改定稿数字）。

**v3.0.0** 已吸收原 `wiki-batch-operations`（批量重命名/重编号/wikilink 迁移/反向链接补齐/批量填充/论文—案例链接同步）。

## 功能

- 四种工作模式：`AUDIT_ONLY`（只排查）/ `AUDIT_PLAN`（排查+整改方案）/ `REPAIR`（分批修复）/ `VERIFY`（复核）
- **每日检修制度**：用户说「今天检修」即触发约10分钟全库回归（页面总数、YAML、死链、标签词表、字段覆盖率、链接对称）；连续3天检修后必须依据 log.md 记录迭代检修方法（三日迭代规则）
- 双轨审计：技术健康轨（YAML/来源/死链/图谱/标签）+ 学术可用性轨（模板化检测/假说 vs 事实/论证充分性）
- 问题分级 P0—P3 + OPT 编号整改台账协议（含规则回写区，AI 规则候选须两批验证 + 用户确认）
- 分批修复纪律：默认 5—8 页/批，超过 10 页须用户确认；外科式修改、全量验收
- 批量操作安全流程：备份先行、old==new 防误删、中文文件名正则解析、DRY_RUN 试跑
- 统计复核纪律：类型专属字段（outcome 等）落地后机器重算须与人工口径清单交叉核对，差异逐项归因，不直接改定稿数字
- 四文件定向：`SCHEMA.md` → `index.md` → `log.md` → `知识库排查修复流程与整改台账.md`

## 安装

```bash
hermes skills install shawndeng321/hermes-obsidian-legal-cssci-wiki-writing-skills/legal-wiki-audit-repair
```

Codex 用户请按[仓库根目录的安装说明](../README.md#openai-codex)，将本技能目录复制到 `$HOME\.codex\skills\legal-wiki-audit-repair`。

## 使用

- "全面排查知识库" → 默认 `AUDIT_ONLY`（只读，不改页面）
- "修复/按 OPT 执行" → `REPAIR` 模式，先冻结范围再小批执行
- "案例文件按编号重命名" → 批量操作流程（见 `references/batch-operations.md`）
- 每次修复后：台账追加详细记录 + `log.md` 追加简记 + 全量验收

## 配套

- 建库/摄入：[legal-research-wiki](../legal-research-wiki)
- 论文写作：[chinese-law-paper-writing](../chinese-law-paper-writing)

## License

MIT © 2026 Shawn Deng
