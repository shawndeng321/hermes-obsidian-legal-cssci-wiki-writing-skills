# Main 分支提升与 README 收敛设计

日期：2026-08-07
目标分支：`codex/hermes-codex-compatibility`
目标默认分支：`main`

## 1. 背景与已确认状态

- 最新远端 `origin/main` 为 `ac08920`。
- 当前兼容分支为 `aafca55`，已经通过双父合并提交 `f28ac52` 吸收 `origin/main` 的 multimodal-wiki 内容，并在冲突处保留兼容分支的双宿主、安全和验证设计。
- 本地 `main` 为 `0a5797a`，其两个远端未包含提交只增加兼容性设计文档、实施计划和 `.worktrees/` 忽略规则，没有修改三个技能的正文。
- `origin/main` 与本地 `main` 都是当前兼容分支的祖先，因此最终提升可以使用 `git merge --ff-only`。该操作只移动 `main` 指针，不会再次执行内容级冲突合并。

## 2. 目标

1. 让根 README 和三个技能 README 反映“兼容能力已经进入 main”的最终状态。
2. 保留 Hermes/Codex 双宿主入口、multimodal-wiki 增量、脚本安全边界和法律证据纪律。
3. 先推送完整兼容分支，再将 `main` 快进到同一 Git tree，最后推送 `main`。
4. 给使用者提供一段可直接阅读的版本更新清单，而不是依赖 Git 历史理解变化。
5. 保留功能分支和恢复分支；本次不删除任何分支或工作树。

## 3. 非目标

- 不把旧 `main` 文件覆盖到兼容分支。
- 不使用 rebase、force-push、squash 或选择性 cherry-pick 重写现有历史。
- 不修改三个技能的方法论范围，不新增与本次发布无关的功能。
- 不安装或运行真实 Obsidian Vault、Hermes 账户或外部资料库。

## 4. README 信息架构

### 4.1 根 README

保留并强化以下用户入口：

1. 项目一句话定位与 Hermes/Codex 双宿主说明。
2. “目标 → 技能 → 输出”决策表和推荐工作流。
3. 三个技能的当前版本与核心能力。
4. `2026-08` 更新内容，明确列出：
   - multimodal-wiki 图片、音频、PDF、批量参考文献和 note-level 溯源；
   - 六项深检、stub 重摄入与 SHA256 修复；
   - Hermes/Codex 元数据兼容；
   - 批量脚本 DRY_RUN、备份、作用域和原子写入；
   - DOCX 真脚注链路；
   - Obsidian headless 凭据与并发编辑安全加固；
   - 仓库级回归测试。
5. 安装入口收敛到 `main`：Hermes Skills Hub、源码复制安装和 Codex 本地技能目录。
6. 开发验证、目录结构、运行前提和边界。

删除或改写以下临时内容：

- “当前分支尚未合并到 main”的说明；
- `选项 A/选项 B` 这种过渡期安装命名；
- “相对 master/main 的分支优化”措辞，改成已经发布的“本次更新内容”；
- 已过时的测试数字，统一为兼容性测试 `8/8`、脚本安全测试 `9/9`，总计 `17/17`。

### 4.2 三个技能 README

- 移除“当前优化分支”和“合并到 main 后”的双重安装入口。
- 统一提供 main 上的 Hermes 安装命令和 Codex 本地安装指引。
- 保留各技能当前版本、典型流程、依赖和边界。
- 修复因根 README 锚点调整而失效的内部链接。

## 5. Git 与发布流程

1. 在兼容分支创建 `backup/main-before-compat-promotion-20260807`，指向发布前的本地 `main`。
2. 在兼容分支修改 README 与相应文档契约测试，只暂存本次相关路径。
3. 运行完整验证并提交 README 收敛改动。
4. 推送 `codex/hermes-codex-compatibility`，然后读取远端引用确认提交已到达。
5. 在主工作树执行：
   - 再次确认工作树干净；
   - `git merge --ff-only codex/hermes-codex-compatibility`；
   - 确认 `main^{tree}` 与兼容分支的 tree 完全相同。
6. 在合并后的 `main` 重新运行完整验证。
7. 普通推送 `main`；若远端移动或认证失败，停止并报告，不使用 force-push。
8. 远端核验 `origin/main` 与 `origin/codex/hermes-codex-compatibility` 均指向最终提交。

## 6. 验证门禁

发布前和 `main` 快进后均执行：

```powershell
python -X utf8 -m unittest tests/test_skill_compatibility.py tests/test_script_safety.py -v
python -X utf8 "$HOME\.codex\skills\.system\skill-creator\scripts\quick_validate.py" chinese-law-paper-writing
python -X utf8 "$HOME\.codex\skills\.system\skill-creator\scripts\quick_validate.py" legal-research-wiki
python -X utf8 "$HOME\.codex\skills\.system\skill-creator\scripts\quick_validate.py" legal-wiki-audit-repair
python -X utf8 -m py_compile legal-wiki-audit-repair/scripts/multimodal_audit.py
git diff --check
```

附加 Git 门禁：

- README 不再包含“尚未合并到 main”或旧分支安装入口。
- 所有本地 Markdown 链接继续由兼容性测试验证。
- `git merge --ff-only` 必须成功。
- 合并后 `git rev-parse main^{tree}` 必须等于 `git rev-parse codex/hermes-codex-compatibility^{tree}`。
- 两个工作树在推送前均无未提交改动。

## 7. 失败与回退

- README 测试失败：只修正文档或相应文档契约，不继续推送。
- 兼容分支推送失败：保留本地提交，不推进 `main`。
- `--ff-only` 失败：说明分支关系发生变化，停止并重新 fetch/审查，不改用普通 merge 掩盖问题。
- `main` 合并后测试失败：不推送 `main`，保留工作树和恢复分支调查。
- `main` 推送被拒绝：重新 fetch 并报告远端变化，不强推。

## 8. 完成标准

- 根 README 与三个技能 README 都以 `main` 已发布状态呈现。
- README 明确列出本轮 multimodal、兼容、安全和验证更新。
- 完整测试为 `17/17`，三个 Skill 校验与脚本编译均通过。
- 远端兼容分支与远端 `main` 指向同一最终提交。
- 恢复分支、兼容分支工作树和历史均保留。
