# 通用化为法学学术研究技能包（Bundle 2026.0925.0）

## 目标

1. 把三个技能从“为单一研究项目迭代出来的工具”改为适用于任何法学领域的通用学术研究技能包；
2. 写作技能同步 [VictorTran1023/law-paper-writing-skill](https://github.com/VictorTran1023/law-paper-writing-skill) `codex/legal-writing-quality` 分支（1.2.0-rc.1，基线 `04f3841`）；
3. Hermes、Claude Code、Codex 通用。

## 关键决定

| 问题 | 决定 | 理由 |
|---|---|---|
| 两个仓库历史不相关、结构不同 | 以本技能包为底座，合并 Victor 的写作内容；不整目录覆盖 | Victor 版有意去掉了 DOCX、多模态、更新器与 `agents/openai.yaml`，整目录替换会让已安装用户失去这些能力并破坏更新器 |
| 写作技能版本号 | 6.0.0（沿用本技能包版本线） | 已安装用户的版本比较是单调的；退到 1.x 会被更新器视为降级 |
| 技能名与 `bundle_id` | 保持不变 | 改名会让 Hermes Hub、Codex 安装和已安装的 1.0.0 更新器全部失效 |
| 项目专属内容 | 删除或改写为“先问用途、按项目设计”的通用流程；示例一律合成 | 通用技能不应把一个项目的分类、框架、样本数量和期刊实测值当规则 |
| 20 份 `session-*.md` | 合并为 5 份主题参考文件，删除原文件 | 其中含本机路径、作者名单、个人信息和一次性数字；通用经验按主题重组后更易检索 |
| 宿主适配 | 每个 `SKILL.md` 一节宿主中立的“运行环境”，而不是每个宿主各写一节 | 避免正文随宿主数量膨胀；`dsh/dsh-compatibility` 分支的思路由此并入主线 |
| Claude Code 分发 | 仓库根目录 `.claude-plugin/plugin.json`（`skills` 列出三个目录）+ `marketplace.json`（`source: "./"`） | 一条命令安装三个技能；不改变现有目录结构，Hermes/Codex 安装路径不受影响 |
| 插件安装的更新 | `check` 输出 `update_channel`；`detect_installation_mode` 拒绝插件目录 | 插件缓存由 Claude Code 管理，更新器不应写入 |

## 验证

- `python -m unittest discover -s tests`：91 项全部通过（本机 Python 3.9 需为 `Path.write_text(newline=)` 加兼容垫片；正式环境要求 3.11+）；
- `claude plugin validate`：插件与 marketplace 清单通过；在隔离的 `CLAUDE_CONFIG_DIR` 中实际安装，`plugin details` 列出 3 个技能；
- 用 `origin/main` 的 1.0.0 更新器对 1.0.0 安装执行 `diff`/`apply`：接受 2.0.0 清单，升级后三个目录与仓库逐字节一致，旧会话文件被移除，备份保留；
- `md2docx_footnotes.py`：空白模板（缺自定义样式）生成 3 条真实脚注与红色标注，样式正确回退；
- 全部技能文件扫描项目专属词（`tests/test_skill_compatibility.py::test_skills_are_host_neutral_and_project_neutral`）。
