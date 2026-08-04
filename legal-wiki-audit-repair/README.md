# 法学 Wiki 审计与修复 Skill

对法学研究 Obsidian/LLM Wiki 做全库体检、问题分级、分批整改和复核。它把“发现问题”和“修改页面”分成不同阶段，适合需要保留证据、备份和回滚边界的研究库。

> 运行时入口是 [`SKILL.md`](SKILL.md)。本页提供模式选择、安装和安全使用方式；批量操作细则见 `references/`。

## 什么时候使用

- Wiki 出现死链、YAML 错误、字段缺失、标签漂移或图谱断裂。
- 需要批量重命名、编号、链接迁移、反向链接补齐或论文—案例链接同步。
- 需要定期检查页面总数、字段覆盖率和统计口径，但不希望审计过程直接改库。
- 需要对模型提出的修复规则保留 OPT 编号、证据和用户确认记录。

## 四种工作模式

| 模式 | 默认行为 | 适合场景 |
|---|---|---|
| `AUDIT_ONLY` | 只读扫描，不修改页面 | 第一次体检、风险盘点、每日检修 |
| `AUDIT_PLAN` | 输出问题、范围、顺序和验收条件 | 需要先给出整改方案 |
| `REPAIR` | 用户确认后按小批执行修改 | 处理已冻结范围的问题 |
| `VERIFY` | 对修复结果做全量复核 | 关闭 OPT、确认没有新增回归 |

## 核心纪律

- **双轨审计**：技术健康（YAML/来源/死链/图谱/标签）与学术可用性（模板化、假说/事实、论证充分性）分开报告。
- **P0—P3 分级**：P0 代表可能造成原始材料丢失、全库损坏或正式内容大规模错误的问题。
- **小批修复**：默认每批 5—8 页，超过 10 页先征得用户确认；每批完成后再全量验收。
- **备份优先**：批量脚本先 `--dry-run`，写入前由调用方指定备份目录；禁止把旧备份静默覆盖。
- **统计复核**：机器重算与人工口径清单交叉核对，差异逐项归因，不直接改定稿数字。
- **三日迭代**：连续三天执行每日检修后，根据 `log.md` 的重复错误更新检修方法。

## 推荐工作流

```text
AUDIT_ONLY → AUDIT_PLAN → 用户确认范围 → 备份 + DRY_RUN → REPAIR → VERIFY → 追加台账与 log
```

任务提示应明确 Wiki 根目录、只读/写入权限、备份目录和本批页数。例如：

```text
使用 legal-wiki-audit-repair 的 AUDIT_ONLY 模式。只检查指定 Wiki 根目录，输出 YAML、死链、字段覆盖率、
链接对称和统计口径问题；不要修改文件。将问题按 P0—P3 编号，给出证据、范围和验收条件。
```

## 快速安装

### 当前优化分支

分支尚未合并到 `main` 时，请按[根 README 的当前分支安装](../README.md#current-branch-install)，复制完整技能目录。

### 合并到 `main` 后的 Hermes Skills Hub

```bash
hermes skills install shawndeng321/hermes-obsidian-legal-cssci-wiki-writing-skills/legal-wiki-audit-repair
```

无交互终端加 `--yes`：

```bash
hermes skills install shawndeng321/hermes-obsidian-legal-cssci-wiki-writing-skills/legal-wiki-audit-repair --yes
```

## 配套脚本

- `scripts/sync_paper_case_links.py`：同步论文与案例之间的链接。
- `scripts/insert_norm_sections.py`：按确认范围插入规范段落。
- `references/batch-operations.md`：批量重命名、编号、链接迁移和反链补齐的安全流程。
- `references/daily-maintenance.md`：每日检修与三日迭代规则。

所有会写入 Wiki 的脚本都应先用 `--dry-run` 查看计划；不要直接把整个 Vault 作为目标，也不要使用未经确认的备份路径。

## 与其他技能配合

- 建库与摄入：[legal-research-wiki](../legal-research-wiki/)
- 论文写作：[chinese-law-paper-writing](../chinese-law-paper-writing/)

## 适用范围与边界

适用于法学研究 Wiki 的审计、维护和批量修复。不替代法律意见或客户法律服务；对于原始材料、正式稿件和跨库批量修改，始终保留人工确认和可回滚备份。

## 许可证

MIT © 2026 Shawn Deng
