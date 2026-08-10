# 法学研究技能包按需自动更新设计

## 目标

为以下三个 Skill 增加跨 Hermes 与 Codex 的统一更新能力：

- `chinese-law-paper-writing`
- `legal-research-wiki`
- `legal-wiki-audit-repair`

任意一个 Skill 被加载时运行本地只读检查。自动联网检查最多每 6 小时一次；用户也可以随时要求“检查法学技能更新”并绕过缓存。发现新版后只提示，不静默更新。用户确认后，三个 Skill 作为一个 Bundle 统一下载、校验、备份、更新和验证；失败时恢复旧版本。

## 已确认的产品规则

- 自动联网检查间隔为 6 小时。
- 每次加载任意一个受管 Skill 都运行本地检查器；缓存有效时不联网。
- 手动检查绕过 6 小时缓存。
- “稍后提醒”暂停提示 4 小时，使用已缓存的更新信息，不重复联网。
- “忽略此版本”只忽略当前 Bundle 版本；更高版本仍提示。
- 更新源为 GitHub `main` 分支上的机器可读清单和源码包。
- 三个 Skill 是同一个更新单元，不允许静默部分更新。
- 发现本地修改时必须再次确认，不自动合并。
- 更新失败自动回滚。
- 更新完成后提示用户新建 Agent 任务，使新版 Skill 正文完全生效。
- 本版不安装启动 Hook、后台服务或常驻进程。

## 非目标

- 不在 Agent 单纯启动时运行检查。
- 不自动更新 Hermes、Codex、Python 或其他 Skill。
- 不修改用户的 Obsidian Vault、论文、案例、PDF、DOCX 或研究资料。
- 不尝试三方合并用户对 Skill 的本地定制。
- 不引入第三方 Python 依赖、GitHub Token 或新的账号登录流程。
- 不在首版实现测试版/稳定版双通道、数字签名或后台推送通知。

## 核心架构

### 1. Skill 内更新预检

三个 `SKILL.md` 各增加一段简短且一致的强制预检：

1. 解析当前 `SKILL.md` 所在目录。
2. 执行同目录下 `scripts/legal_skills_update.py check --json`。
3. `up_to_date`、`cached`、`offline` 或非致命检查错误均不打断原任务。
4. `update_available` 时按脚本返回的结构化数据展示提示并等待用户选择。
5. 用户明确同意后才执行 `apply`。

三份更新器脚本保持字节一致，由仓库测试保证。脚本放入每个 Skill 是因为 Hermes Skills Hub 和 Codex 源码安装均按单个 Skill 目录分发，不能依赖仓库根目录中的共享运行时文件。

手动更新请求统一由 `legal-wiki-audit-repair` 作为路由入口：它的 frontmatter `description` 增加“检查或更新本技能包”的触发意图，并继续满足当前不超过 60 字符的兼容性约束。其余两个 Skill 保留原有业务路由，只在已经因写作或研究任务被加载后执行相同预检，避免一次手动更新请求同时加载三份较长的 Skill 正文。

### 2. 本地状态目录

检查时间、ETag、忽略版本、稍后提醒和备份不写入 Skill 目录，避免被更新覆盖或误判为本地修改。

默认位置：

- Windows：`%LOCALAPPDATA%/hermes-legal-skills-updater/`
- Linux/macOS：`$XDG_STATE_HOME/hermes-legal-skills-updater/`；未设置时使用 `~/.local/state/hermes-legal-skills-updater/`
- 高级用户可通过 `LEGAL_SKILLS_UPDATE_HOME` 指定其他位置。

目录至少包含：

```text
state.json                 # 上次检查、ETag、忽略和稍后提醒状态
operation.lock             # 跨进程互斥锁
downloads/                 # 临时下载；成功或失败后清理
backups/<timestamp>/       # 三个 Skill 和必要的 Hub 状态快照
```

`state.json` 使用临时文件加原子替换写入。检查操作短暂持有状态锁，更新操作在完整事务期间持有独占锁；另一个 Agent 同时检查或更新时返回 `busy`，不得重复下载或交叉替换目录。首版不自动删除备份，避免误删包含用户本地修改的版本。

### 3. Bundle 与单 Skill 版本

新增独立 Bundle 版本，同时保留现有 Skill 版本：

| 对象 | 自动更新首版 |
|---|---:|
| 整体技能包 | `1.0.0` |
| `chinese-law-paper-writing` | `5.2.0` |
| `legal-research-wiki` | `4.2.0` |
| `legal-wiki-audit-repair` | `4.3.0` |

Bundle 使用 `X.Y.Z`。更新提示以 Bundle 版本决定是否有新版，并同时展示三个 Skill 的版本变化。某个 Skill 没有业务变化时可以保持自身版本，但仍参与整个 Bundle 的哈希校验和交付。

### 4. 远端发布清单

仓库根目录新增 `bundle-release.json`。它是 GitHub `main` 上的更新入口，至少包含：

```json
{
  "schema_version": 1,
  "bundle_id": "hermes-legal-research-skills",
  "bundle_version": "1.0.0",
  "published_at": "2026-08-10T00:00:00+08:00",
  "update_level": "feature",
  "summary": "增加按需更新检查、统一备份和回滚",
  "skills": {
    "chinese-law-paper-writing": "5.2.0",
    "legal-research-wiki": "4.2.0",
    "legal-wiki-audit-repair": "4.3.0"
  },
  "compatibility": {
    "hermes": true,
    "codex": true,
    "python": ">=3.11"
  },
  "changes": [],
  "history": [],
  "files": {},
  "archive_url": "https://github.com/shawndeng321/hermes-obsidian-legal-cssci-wiki-writing-skills/archive/refs/heads/main.zip"
}
```

`files` 保存三个受管目录内文件的 SHA256。每个 Skill 同时携带 `bundle-lock.json`，记录安装时的 Bundle 版本和该 Skill 的官方文件哈希，用于检测后续本地修改。锁文件自身不包含自己的哈希；远端根清单负责校验锁文件。

`history` 至少保留可覆盖近期版本的结构化更新记录。用户跨过多个版本时，检查器聚合所有高于当前版本且不高于最新版本的记录，避免短时间连续发布导致中间更新说明丢失。

### 5. 发布准备工具

仓库新增 `tools/prepare_bundle_release.py`，负责：

- 校验 Bundle 和三个 Skill 的版本格式；
- 计算受管文件哈希；
- 先计算各 Skill 中除自身锁文件外的官方文件哈希，再生成或刷新三个 `bundle-lock.json`；
- 最后更新 `bundle-release.json`，并把三个锁文件也纳入远端根清单哈希；
- 检查更新历史是否包含当前 Bundle 版本；
- 拒绝存在路径越界、重复文件、缺少 `SKILL.md` 或缺少 `agents/openai.yaml` 的包；
- 提供 `--check` 模式供 CI 验证仓库内容与清单一致。

任何受管 Skill 文件变化都必须更新 Bundle 版本和清单；只修改仓库根文档、测试或设计记录时不要求发布新 Bundle。CI 负责阻止“代码已变而清单未更新”的提交进入可发布状态。

## 检查流程

### 自动检查

1. 读取 `state.json`。
2. 如果当前时间早于 `snooze_until`，返回 `snoozed`。
3. 如果距离 `last_network_check` 不足 6 小时，读取缓存：缓存最新版等于 `ignored_version` 时返回 `ignored`，否则返回缓存的最新状态。
4. 缓存超过 6 小时后，无论旧缓存是否曾被忽略，都用 HTTPS 获取 GitHub `main` 上的 `bundle-release.json`，并携带上次 ETag；这样更高版本不会被旧的忽略记录挡住。
5. 远端返回未变化时更新时间戳，并按当前缓存决定 `up_to_date`、`ignored` 或 `update_available`。
6. 远端版本更高时，校验清单结构、Bundle ID、版本、Skill 集合和允许的下载地址，保存缓存；只有新版本仍等于 `ignored_version` 时返回 `ignored`，否则返回 `update_available`。
7. 超时、断网或无效响应在自动模式下返回非致命状态，不影响原任务。

网络软超时为 3 秒。检查器只访问固定 GitHub HTTPS 地址，遵循系统标准代理环境，不读取或打印凭据。

### 手动检查

`check --force --json` 忽略 6 小时缓存和稍后提醒时间，立即联网。它仍不自动安装，也不绕过“忽略此版本”的记录；返回结果会标明该版本已被忽略，由 Agent 询问是否重新显示或更新。

## 用户交互

### 简短提示

```text
发现法学研究技能包新版本

当前版本：v1.0.0
最新版本：v1.2.0
将跨越版本：v1.1.0、v1.2.0

本次统一更新：
- chinese-law-paper-writing
- legal-research-wiki
- legal-wiki-audit-repair

主要变化：
- v1.1.0：优化图片资料引用格式
- v1.2.0：增加扫描件来源审核和更新回滚

[立即更新] [查看更新说明] [稍后提醒] [忽略此版本]
```

### 本地修改提示

```text
暂未更新：检测到本地修改

修改或新增文件：
- chinese-law-paper-writing/SKILL.md
- legal-research-wiki/references/workflow.md

[查看差异] [完整备份后覆盖] [取消更新]
```

选择“完整备份后覆盖”后必须再次确认。首版不提供自动合并。

### 成功提示

```text
法学研究技能包更新完成

技能包：v1.0.0 → v1.2.0
✓ chinese-law-paper-writing 5.2.0 → 5.3.0
✓ legal-research-wiki 4.2.0 → 4.2.1
✓ legal-wiki-audit-repair 4.3.0 → 4.4.0

备份位置：<实际路径>
请新建一个 Agent 任务，使新版 Skill 内容完全生效。
```

## 更新应用流程

### 通用准备

用户确认更新后：

1. 把当前更新器复制到状态目录并从该目录运行工作进程，避免 Windows 替换正在运行的 Skill 目录时锁住更新器本身。
2. 下载 `main` 源码包到临时目录。
3. 拒绝绝对路径、`..`、符号链接和不属于仓库根前缀的 ZIP 条目。
4. 只提取三个固定 Skill 目录。
5. 比较源码包内的 `bundle-release.json` 与检查阶段缓存的清单；两者的版本、Skill 集合或文件哈希不同即视为 `main` 在检查后发生变化，停止本次更新并要求重新检查。
6. 逐文件验证远端清单中的 SHA256，并拒绝缺失文件、额外受管文件或版本不一致。
7. 检查三个安装目录及本地锁文件，列出修改、新增、删除和版本不一致项。
8. 任一 Skill 缺失时不静默继续；向用户提供“安装缺失项并统一更新”或“取消”。

### Codex 或源码复制安装

- 把三个新版目录暂存到与目标安装目录相同的文件系统。
- 完整备份三个旧目录。
- 依次把旧目录移动到事务备份位置，再把三个暂存目录移动到正式位置。
- 完成后重新读取三个 `SKILL.md`、`agents/openai.yaml` 和 `bundle-lock.json` 验证版本和哈希。
- 任一步失败即移除已放入的新目录并恢复三个旧目录。

如果安装根目录是 Git 工作树、三个 Skill 是指向开发仓库的符号链接，或者目标不在识别出的 Skill 根目录内，`apply` 必须拒绝执行并提示使用 Git 更新源码。

### Hermes Skills Hub 安装

- 读取 Hub lock，仅用于确认三个 Skill 的来源和安装路径；不把其他 Hub Skill 纳入范围。
- 只接受实现时已经测试支持的 Hub lock `version`；遇到未知结构时拒绝自动应用并提示使用 Hermes 官方命令。
- 更新前对三个 Skill 目录和 Hub lock 文件做完整快照，并记录三个目标条目之外内容的哈希。
- 分别调用 `hermes skills update <skill-name>`，让 Hermes 自己维护来源和 lock 状态。
- 三项完成后，按远端清单验证实际安装文件和版本。
- 任一命令或验证失败时，恢复三个目录；确认 Hub lock 的非目标内容没有被其他进程改变后，再恢复更新前的完整 lock 快照，并明确报告失败原因。
- 如果更新期间另一个 Hermes 进程修改了非目标 Hub 条目，不覆盖该并发变化；停止写入，保留备份，并给出三个目标条目的人工恢复步骤。
- 成功时保留 Hermes 生成的新 lock，不由自定义更新器重写其结构。

该路径要求三个 Skill 均由同一 GitHub 仓库来源管理。混合安装来源时拒绝统一更新，并提供重新安装说明。

## 错误处理

| 状态 | 自动检查行为 | 用户主动更新后的行为 |
|---|---|---|
| 断网或超时 | 静默继续原任务 | 明确提示未修改文件，可稍后重试 |
| 清单 JSON 无效 | 静默记录诊断 | 拒绝更新并提示发布清单异常 |
| 不支持的清单版本 | 不更新 | 要求按 README 手动升级更新器 |
| SHA256 不匹配 | 不适用 | 删除暂存包，不改安装目录 |
| 本地修改 | 显示更新可用 | 二次确认后才备份覆盖 |
| 三项安装不完整 | 显示状态异常 | 用户确认安装缺失项后才继续 |
| Hermes 来源不一致 | 不更新 | 拒绝并给出统一来源安装方法 |
| 另一个更新事务正在运行 | 使用缓存或静默继续 | 返回 `busy`，不启动第二个写事务 |
| 事务中途失败 | 不适用 | 自动回滚并保留诊断和备份 |
| 并发外部修改或回滚失败 | 不适用 | 停止一切写入，列出实际路径和人工恢复步骤 |

自动模式不得把网络错误、GitHub 限流或更新器异常伪装成“已是最新版”。只有明确验证版本相等时才能返回 `up_to_date`。

## 安全边界

- 只允许 HTTPS GitHub 源和明确允许的重定向主机。
- 下载内容永不作为命令直接执行；只把通过清单校验的三个 Skill 文件复制到目标目录。
- 拒绝 ZIP Slip、符号链接、设备文件、路径大小写冲突和超出合理大小的包。
- 所有目标路径在写入前解析并验证位于识别出的 Skill 根目录内。
- 不使用 GitHub Token，不打印代理、环境变量或用户路径中的秘密值。
- 更新器只写三个 Skill、状态目录、备份目录，以及 Hermes 更新失败时恢复的原 lock 文件。
- SHA256 用于校验内容完整性和发布一致性；首版的软件供应链信任边界仍是 GitHub 仓库账号与 HTTPS，不宣称具备独立代码签名。

## 预计文件变化

新增：

```text
bundle-release.json
tools/prepare_bundle_release.py
tests/test_bundle_updater.py
chinese-law-paper-writing/scripts/legal_skills_update.py
chinese-law-paper-writing/bundle-lock.json
legal-research-wiki/scripts/legal_skills_update.py
legal-research-wiki/bundle-lock.json
legal-wiki-audit-repair/scripts/legal_skills_update.py
legal-wiki-audit-repair/bundle-lock.json
```

修改：

```text
README.md
.gitignore
tests/test_skill_compatibility.py
chinese-law-paper-writing/SKILL.md
chinese-law-paper-writing/README.md
legal-research-wiki/SKILL.md
legal-research-wiki/README.md
legal-wiki-audit-repair/SKILL.md
legal-wiki-audit-repair/README.md
```

不在三个 Skill 内新增独立更新 README 或 CHANGELOG。详细说明保留在仓库根 README，Skill 正文只保留运行所需的最短指令。

## 测试策略

### 单元测试

- 6 小时缓存边界、ETag、强制检查、4 小时稍后提醒和忽略版本；
- Semantic Version 比较及跨多个版本的说明聚合；
- 断网、超时、GitHub 错误、无效 JSON 和不支持的清单版本；
- 文件哈希、本地新增/修改/删除检测；
- ZIP 越界、符号链接、大小写冲突和大小上限；
- 安装根目录、Git 工作树和符号链接识别；
- 三份更新器脚本一致；
- Hermes 与源码复制两种适配器的命令和状态转换。

### 临时目录集成测试

- 三个未修改 Skill 从旧 Bundle 更新到新 Bundle；
- 跨两个版本直接更新到最新版并展示累计说明；
- 任一 Skill 缺失时拒绝部分更新；
- 本地修改时不写入，确认后保留完整备份；
- 第二项替换失败时三个 Skill 全部回滚；
- Hermes 命令部分失败时恢复目录和原 lock；
- 两个并发检查只产生一次联网请求，两个并发应用只能有一个进入写事务；
- 更新器自身位于待替换目录时仍能从状态目录工作进程完成事务。

所有网络测试使用本地模拟响应，不依赖 GitHub。发布前另做一次只读真实清单检查和一次隔离目录端到端演练。

### 仓库回归

```powershell
python -X utf8 -m unittest tests/test_skill_compatibility.py -v
python -X utf8 -m unittest tests/test_script_safety.py -v
python -X utf8 -m unittest tests/test_bundle_updater.py -v
```

另对三个 Skill 运行 Codex `quick_validate.py`，并执行 `git diff --check`。README 中不再固化会随测试增长而过期的用例总数，改为说明三组测试均须通过。

## 首版迁移

旧安装中没有更新器，无法自行发现首个自动更新版本。因此：

- 新用户按新版安装说明安装后直接获得自动检查。
- 旧用户必须按 README 手动更新或重新复制一次三个 Skill。
- 完成这次一次性升级后，后续 Bundle 才能按本设计自动检查并提示。
- Hermes Hub 用户的一次性升级使用 Hermes 官方更新命令；Codex 和源码复制用户按新版根 README 重新复制三个完整目录。

## 验收标准

- 任意 Skill 加载时执行本地检查，6 小时内不重复联网。
- 用户可强制检查，且任何检查都不会静默安装。
- 三项 Skill 共用 Bundle 版本、状态、更新说明和更新决策。
- 连续发布多个版本时不遗漏中间更新说明。
- 本地修改、缺失 Skill、混合来源和开发工作树均不会被静默覆盖。
- 成功更新后三个 Skill 与远端清单完全一致。
- 在没有外部并发修改的正常失败场景中，任一步失败时三个 Skill 和受管 Hub 状态恢复到更新前状态；若外部状态已变化或无法完全恢复，必须停止写入并给出准确路径和人工恢复步骤。
- 自动检查失败不影响原本的法学研究、Wiki 审计或论文写作任务。
- 原有兼容性、安全和 Skill 校验全部通过。
- README 明确一次性迁移、检查间隔、手动检查、更新边界和恢复方法。
