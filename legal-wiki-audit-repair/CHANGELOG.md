# 更新记录

新增能力或规则递增次版本号，措辞与格式修订递增修订号，面向所有使用者的结构性调整递增主版本号；变更同时更新 `SKILL.md` 的 `metadata.version`、技能包根目录的 `bundle-release.json` 与 README。

## 5.0.1（2026-09-28）

- 仓库更名为 `shawndeng321/legal-academic-research-skills`：更新器的清单地址与 README 中的安装命令随之更新。旧地址由 GitHub 自动跳转，已安装的用户不受影响。

## 5.0.0（2026-09-25）

- `SKILL.md` 通用化：移除特定项目的基线计数（页数、标签数、样本数、哈希文件数）和案例编号；每日检修改为对照台账中记录的本项目基线；检修脚本不再依赖某一宿主的固定路径，可用系统定时任务运行。
- 不再要求宿主提供 `llm-wiki`、`obsidian` 等外部技能；本技能自足。
- `references/batch-operations.md` 重写为通用流程；**更正**表格内别名链接写法为 `[[目标\|别名]]`（旧版该文件一处仍推荐 `&#124;`，与已验证规则矛盾）。
- 删除 `paper-case-theme-mapping.md` 与 `pure-link-verification.md`（均为单一项目的数据清单），其通用方法并入 `batch-operations.md` 第六节。
- `group-case-stats-extraction.md`、`comparison-page-format.md` 通用化。
- 脚本：移除示例中的真实作者与论文名；默认备份目录去掉日期后缀；`verify_case_link_sections.py` 的说明行检查改为宽松匹配。
- 技能包更新器识别 Claude Code 插件安装：`check` 输出 `update_channel`，并拒绝对插件目录执行 `apply`。
- 预检与示例命令改为 `python3`（Windows 用 `py`）；macOS 默认没有 `python` 命令。
- 兼容性：`description` 改为“英文开头句 + 中文触发词”（约 200—240 字符，Codex 与 Hermes 上限均为 1024）。开头一句不超过 57 字符，因为 Hermes 在系统提示的技能目录中只显示前 57 个字符；后半部分的中文触发词供 Claude Code、Codex 自动选用；Claude Code 插件安装时跳过更新预检，不再每次加载都弹出命令权限确认。
- 死链验收口径写明：`drafts/` 链接为容忍类，正式内容页死链为零即通过。
- 新增 `evals/pressure-tests.md`：15 个行为评估场景（工作模式与写入权限、证据判断、批量操作、检修与更新、报告）。
- 新增“配套技能”一节：写明用到其他两个技能的哪些内容，以及未安装时如何处理；跨技能引用改为按技能名查找，不再使用 `../../其他技能/` 相对链接（Hermes 等宿主可能把技能分放在不同子目录，相对链接会失效）。
- 技能包更新器支持分目录安装：按技能名在技能根目录或一层分类子目录（如 Hermes 的 `research/`）中定位各技能，原地备份、更新与回滚；同一技能装了两份时停止并报告。

## 4.3.0（2026-08）

技能包按需更新路由；multimodal-wiki 六项深检；每日检修与三日迭代。
