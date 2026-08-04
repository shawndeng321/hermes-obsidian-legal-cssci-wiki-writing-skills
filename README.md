# Hermes 法学研究技能包

面向中国法学研究的三项 AI Skill：先把论文、案例和法条整理成可追溯的 Wiki，再做全库审计与安全修复，最后把研究证据转化为可核验的论文工作稿。

> 本仓库同时提供 Hermes Agent 与 OpenAI Codex 的技能目录。正文只保留一份，运行时元数据分别放在 `SKILL.md` 与 `agents/openai.yaml` 中。

<p align="center">
  <img src="chinese-law-paper-writing/assets/readme/paper-banner.png" alt="中国法学研究、知识库审计与论文写作技能包" width="100%">
</p>

## 先从这里开始

| 你的目标 | 先使用 | 你会得到 |
|---|---|---|
| 建立或扩充法学研究 Wiki | [`legal-research-wiki`](legal-research-wiki/) | 有范围、有来源、有质量门禁的论文/案例/法条知识库 |
| 检查并修复已有 Wiki | [`legal-wiki-audit-repair`](legal-wiki-audit-repair/) | 只读审计、P0—P3 台账、小批修复与全量复核 |
| 从选题写到投稿工作稿 | [`chinese-law-paper-writing`](chinese-law-paper-writing/) | 主问题—证据—引注链、期刊适配与 DOCX 工作稿 |

推荐顺序：`chinese-law-paper-writing` 先收窄研究问题 → `legal-research-wiki` 组织材料 → `legal-wiki-audit-repair` 定期体检与修复。只做其中一项时，可以直接进入对应技能。

## 技能一览

| 技能 | 版本 | 适合什么时候用 | 核心能力 |
|---|---:|---|---|
| [`legal-research-wiki`](legal-research-wiki/) | v3.0.0 | 新建、扩充或重新整理研究库 | 范围优先摄入、PDF/DOCX 提取、交叉引用、六维质量门禁 |
| [`legal-wiki-audit-repair`](legal-wiki-audit-repair/) | v3.1.0 | 已有 Wiki 出现死链、字段缺失或批量操作需求 | AUDIT_ONLY、P0—P3 分级、备份/DRY_RUN、小批修复、统计复核 |
| [`chinese-law-paper-writing`](chinese-law-paper-writing/) | v4.0.0 | 选题、研究、起草、修订、审核或期刊适配 | 五问框架、PLAN→ADAPT、证据链、引注门禁、DOCX 脚注 |

## 相对 `master/main` 的优化与修改

仓库远程默认分支目前名为 `main`；本文所说的 `master/main` 指默认基线。本分支 `codex/hermes-codex-compatibility` 在不拆分方法论正文的前提下，完成了以下优化：

### 1. Hermes 与 Codex 兼容性分层

- 三项技能统一使用双方都能识别的 `SKILL.md` frontmatter。
- 为每项技能增加 `agents/openai.yaml`，补齐 Codex 的显示名、短描述和默认提示词。
- 修正 Hermes 的逐技能安装标识符，避免把整个仓库误装成一个技能。
- 增加当前分支的本地安装路径；分支尚未合并到 `main` 时，不会误装默认分支旧版本。

### 2. 用户入口和文档一致性

- 根 README 增加“目标 → 技能 → 输出”的决策表、三分钟工作流和验证步骤。
- 三项技能 README 统一安装、使用、依赖和适用范围说明。
- 清理旧技能名、旧 frontmatter、占位安装命令和过时路径说明。
- 明确哪些内容属于方法论、哪些内容属于运行时元数据，降低维护成本。

### 3. 批量脚本的安全边界

- 清洗、链接同步和规范段落脚本增加 `--dry-run`、备份目录、路径包含校验、禁止覆盖已有备份和原子写入。
- 移除作者本机硬编码路径；批量脚本改为接收调用方明确传入的 Wiki 路径。
- PDF 批量提取默认不覆盖已有文本，破坏性动作需要显式确认。

### 4. DOCX 脚注链路可验证

- `md2docx_footnotes.py` 支持显式命令行输入、唯一临时目录和 `[N]`/`[脚注N]` 标记。
- 模板没有 `footnotes.xml` 时自动补齐关系和内容类型声明。
- 增加真实 DOCX 生成、重新打开和脚注引用一致性检查。

### 5. 可回归验证

- 增加仓库级 Hermes/Codex 兼容性测试与脚本安全测试。
- 当前分支已验证：兼容性测试 5/5、安全测试 7/7、三个 Codex `quick_validate.py` 均通过。
- 本机 Hermes 隔离目录验证三个技能均能以 `local / enabled` 发现，并保留完整支持文件。

以上修改只改变兼容性、文档、脚本安全和验证层，不删除原有方法论内容；详细设计与实施记录见 [`docs/superpowers/`](docs/superpowers/)。

## 安装

<a id="current-branch-install"></a>

### 选项 A：当前分支安装（尚未合并到 `main` 时推荐）

当前分支包含本次优化，先克隆分支，再复制完整技能目录。请使用一个空的临时目录：

```powershell
$branch = 'codex/hermes-codex-compatibility'
$checkout = Join-Path $env:TEMP 'hermes-legal-skills-codex-compatibility'
git clone --branch $branch https://github.com/shawndeng321/hermes-obsidian-legal-cssci-wiki-writing-skills.git $checkout
```

Hermes：

```powershell
$hermesHome = if ($env:HERMES_HOME) { $env:HERMES_HOME } else { Join-Path $env:LOCALAPPDATA 'hermes' }
$hermesSkills = Join-Path $hermesHome 'skills'
New-Item -ItemType Directory -Force $hermesSkills | Out-Null
Copy-Item -Recurse -Force "$checkout\chinese-law-paper-writing" (Join-Path $hermesSkills 'chinese-law-paper-writing')
Copy-Item -Recurse -Force "$checkout\legal-research-wiki" (Join-Path $hermesSkills 'legal-research-wiki')
Copy-Item -Recurse -Force "$checkout\legal-wiki-audit-repair" (Join-Path $hermesSkills 'legal-wiki-audit-repair')
hermes skills list --source local --enabled-only
```

Codex：

```powershell
$codexSkills = Join-Path $HOME '.codex\skills'
New-Item -ItemType Directory -Force $codexSkills | Out-Null
Copy-Item -Recurse -Force "$checkout\chinese-law-paper-writing" (Join-Path $codexSkills 'chinese-law-paper-writing')
Copy-Item -Recurse -Force "$checkout\legal-research-wiki" (Join-Path $codexSkills 'legal-research-wiki')
Copy-Item -Recurse -Force "$checkout\legal-wiki-audit-repair" (Join-Path $codexSkills 'legal-wiki-audit-repair')
```

### 选项 B：分支合并到 `main` 后使用 Hermes Skills Hub

三个技能需要分别安装；脚本或 CI 环境加 `--yes`：

```bash
hermes skills install shawndeng321/hermes-obsidian-legal-cssci-wiki-writing-skills/chinese-law-paper-writing
hermes skills install shawndeng321/hermes-obsidian-legal-cssci-wiki-writing-skills/legal-research-wiki
hermes skills install shawndeng321/hermes-obsidian-legal-cssci-wiki-writing-skills/legal-wiki-audit-repair
```

```bash
hermes skills install shawndeng321/hermes-obsidian-legal-cssci-wiki-writing-skills/chinese-law-paper-writing --yes
hermes skills install shawndeng321/hermes-obsidian-legal-cssci-wiki-writing-skills/legal-research-wiki --yes
hermes skills install shawndeng321/hermes-obsidian-legal-cssci-wiki-writing-skills/legal-wiki-audit-repair --yes
```

安装后运行 `hermes skills list`，确认三个技能均为 `enabled`。本仓库是多文件技能；不要把仓库根 URL 或单个 `SKILL.md` 当成完整安装入口。

## 三分钟工作流

```text
1. PLAN       用 chinese-law-paper-writing 收窄主问题、范围和交付物
2. RESEARCH   用 legal-research-wiki 建来源登记、论点表和 Wiki 结构
3. AUDIT      用 legal-wiki-audit-repair 只读体检，建立 P0—P3 台账
4. REPAIR     用户确认范围后按 5—8 页小批修复，先备份再写入
5. DRAFT      回到写作 Skill 起草并同步记录脚注标识
6. AUDIT      终检引注、法律版本、匿名信息和目标期刊正式要求
```

## 验证与排错

### 安装验证

- Hermes：`hermes skills list --source local --enabled-only` 或 `hermes skills list`。
- Codex：新建任务后直接要求使用对应技能；技能目录必须包含 `SKILL.md` 和 `agents/openai.yaml`。
- 如果远程 Hub 因网络探测超时，使用“选项 A”的本地复制路径，不要重复下载单个 `SKILL.md`。

### 开发验证

```powershell
python -X utf8 -m unittest tests/test_skill_compatibility.py -v
python -X utf8 -m unittest tests/test_script_safety.py -v
```

Codex 技能校验：

```powershell
$validator = "$HOME\.codex\skills\.system\skill-creator\scripts\quick_validate.py"
python -X utf8 $validator chinese-law-paper-writing
python -X utf8 $validator legal-research-wiki
python -X utf8 $validator legal-wiki-audit-repair
```

## 目录结构

```text
README.md                    # 总入口、安装、分支变更和验证
chinese-law-paper-writing/   # 论文写作与投稿工作稿
legal-research-wiki/         # 研究 Wiki 建库与摄入
legal-wiki-audit-repair/     # Wiki 审计、批量修复与复核
docs/superpowers/             # 兼容性设计与实施记录
tests/                        # 兼容性和脚本安全回归测试
```

## 运行前提与边界

- Hermes Agent 或 OpenAI Codex；技能正文遵循标准 `SKILL.md` 结构。
- Python 3.11+；DOCX 脚注脚本需要 `python-docx` 与 `lxml`。
- PDF 提取按需安装 `pymupdf` 或 `marker-pdf`。
- 默认不扫描整个 Obsidian Vault，也不写回用户资料；只有用户明确授权并指定目标文件后才允许修改。
- 不编造法条、案号、页码、期刊规则或统计数字；资料不完整时必须保留待核状态。
- 不适用于合同、诉状、法律意见书、客户法律建议、学位论文或声称保证录用的内容。

## 版本与许可证

每项技能遵循 `X.Y.Z` 版本策略：内容能力变化升 `X`/`Y`，修订和兼容性修复升 `Z`。当前打包基线：2026-08-03。

MIT © 2026 Shawn Deng。内容来自法学论文写作与知识库管理实践；本项目不是 Hermes、OpenAI、Obsidian、CSSCI 期刊或其他机构的官方指南、认证或录用承诺。
