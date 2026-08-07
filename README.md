# Hermes / Codex 法学研究技能包（Chinese Legal Research Skills）

面向中国法学研究的三项 AI Skill：先把论文、案例和法条整理成可追溯的 Wiki，再做全库审计与安全修复，最后把研究证据转化为可核验的论文工作稿。

> 本仓库兼容 Hermes 与 Codex。技能正文只保留一份，运行时元数据分别放在 `SKILL.md` 与 `agents/openai.yaml` 中。

[快速选择](#先从这里开始) · [更新内容](#2026-08-更新内容) · [安装](#安装) · [验证](#验证与排错)

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
| [`legal-research-wiki`](legal-research-wiki/) | **v4.1.0** | 新建、扩充或重新整理研究库 | 范围优先摄入、PDF/DOCX/图片/音频摄入、交叉引用、六维质量门禁、闭世界查询纪律、Obsidian 云端同步 |
| [`legal-wiki-audit-repair`](legal-wiki-audit-repair/) | **v4.2.0** | 已有 Wiki 出现死链、字段缺失或批量操作需求 | AUDIT_ONLY、P0—P3 分级、备份/DRY_RUN、小批修复、统计复核、每日检修（三日迭代）、六项深检脚本、闭世界查询纪律 |
| [`chinese-law-paper-writing`](chinese-law-paper-writing/) | **v5.1.0** | 选题、研究、起草、修订、审核或期刊适配 | 五问框架、PLAN→ADAPT、证据链、引注门禁、note-level 溯源引注、闭世界查询纪律、DOCX 脚注 |

## 2026-08 更新内容

本次发布将兼容性分支与 [kigner/multimodal-wiki](https://github.com/kigner/multimodal-wiki) v1.0.0 的通用能力统一纳入 `main`，并按中国法学研究、Hermes 与 Codex 双宿主及本仓库的安全边界完成适配。

### 多模态研究资料

- **图片与扫描件**：按宿主能力读取截图、图表和扫描页，保留原文件、提取页与来源关系。
- **音频与访谈**：在具备转录能力时生成逐字稿；能力不可用时保留原始材料并明确标记待处理。
- **PDF 与批量参考文献**：增加 PDF 提取、批量来源登记和 stub 补全流程；第三方摘要只作发现线索，不自动升级为已核验法律证据。
- **note-level 溯源**：回答和写作中的事实主张可追溯到具体来源笔记、来源块和原始文件。

### 审计与安全

- **六项深检**：新增 `multimodal_audit.py`，检查索引一致性、raw 摄入、frontmatter、wikilink、文件卫生和日志格式。
- **stub 与 SHA256 修复**：提供空壳来源重摄入、哈希漂移归因和批量修复指引。
- **批量脚本保护**：写入操作要求明确 Wiki 作用域、`DRY_RUN`、调用方指定备份、路径包含校验和原子写入；PDF 提取默认不覆盖已有文本。
- **Obsidian headless 加固**：登录改为交互式凭据输入；持续同步前要求备份、单写者纪律和单次同步验证。

### 双宿主与交付验证

- **Hermes / Codex 分层**：三项技能共用一份 `SKILL.md` 方法论正文，并分别通过标准 frontmatter 与 `agents/openai.yaml` 提供运行时元数据。
- **真实 DOCX 脚注**：`md2docx_footnotes.py` 支持显式输入、真实脚注关系、内容类型补齐及重新打开验证。
- **仓库级回归**：当前发布已通过兼容性测试 8/8、脚本安全测试 9/9，共 17/17；三个 Skill 均通过 Codex `quick_validate.py`。

本次更新保留原有法学研究与论文写作方法论；详细设计、实施和合并记录见 [`docs/superpowers/`](docs/superpowers/)。

## 安装

### Hermes Skills Hub

三个技能需要分别安装：

```bash
hermes skills install shawndeng321/hermes-obsidian-legal-cssci-wiki-writing-skills/chinese-law-paper-writing
hermes skills install shawndeng321/hermes-obsidian-legal-cssci-wiki-writing-skills/legal-research-wiki
hermes skills install shawndeng321/hermes-obsidian-legal-cssci-wiki-writing-skills/legal-wiki-audit-repair
```

脚本或 CI 环境加 `--yes`：

```bash
hermes skills install shawndeng321/hermes-obsidian-legal-cssci-wiki-writing-skills/chinese-law-paper-writing --yes
hermes skills install shawndeng321/hermes-obsidian-legal-cssci-wiki-writing-skills/legal-research-wiki --yes
hermes skills install shawndeng321/hermes-obsidian-legal-cssci-wiki-writing-skills/legal-wiki-audit-repair --yes
```

安装后运行 `hermes skills list`，确认三个技能均为 `enabled`。本仓库是多文件技能；不要把仓库根 URL 或单个 `SKILL.md` 当成完整安装入口。

### 源码安装（Hermes / Codex）

需要本地审查、离线安装或固定版本时，从 `main` 克隆仓库，再复制完整技能目录。请使用一个空的临时目录：

```powershell
$checkout = Join-Path $env:TEMP 'hermes-legal-skills'
git clone --branch main https://github.com/shawndeng321/hermes-obsidian-legal-cssci-wiki-writing-skills.git $checkout
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
- 如果远程 Hub 因网络探测超时，使用“源码安装”的本地复制路径，不要重复下载单个 `SKILL.md`。

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
README.md                    # 总入口、安装、更新内容和验证
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

每项技能遵循 `X.Y.Z` 版本策略：内容能力变化升 `X`/`Y`，修订和兼容性修复升 `Z`。当前打包基线：2026-08-07。

MIT © 2026 Shawn Deng。内容来自法学论文写作与知识库管理实践；本项目不是 Hermes、OpenAI、Obsidian、CSSCI 期刊或其他机构的官方指南、认证或录用承诺。
