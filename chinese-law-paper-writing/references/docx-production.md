---
name: academic-paper-docx
description: Use when 把论文md转成投稿docx（真实Word脚注、样稿格式复刻）。docx生产执行细则。
version: 1.0.0
---

# 学术论文投稿 docx 生成（真实脚注 + 样稿格式复刻）

> 2026-08 实测：3.0 初稿 docx → 4.0 初稿 docx 完全复刻（用户强调"格式也很重要"——投稿稿 docx 必须与已定稿样稿逐项一致：字体/字号/行距/缩进/页边距/真脚注）。与 chinese-law-paper-writing（写作总纲，user-owned）配合：总纲管内容与期刊适配，本技能管 docx 生产执行。

## When to Use

- 论文 md 工作稿 → 投稿 docx（带**真实 Word 脚注**，页脚自动编号，非文末列表）；
- 已有定稿样稿 docx，新版本要逐项复刻其格式；
- 任何需要在 docx 中注入真实脚注、或从样稿继承样式/页面设置的任务。

## 核心思路：以样稿 docx 为模板，不从零设样式

1. `shutil.copy(样稿.docx, 新稿.docx)` → python-docx 打开；
2. 清空 body 内除 `w:sectPr` 外的全部元素（样式/页面设置自动继承，天然一致）；
3. 写入新内容（应用样稿已有样式名：一级标题/二级标题/三级标题/正文1/FootnoteText/FootnoteReference）；
4. 注入真实脚注（见下）。

## python-docx 的脚注限制（关键坑）

- python-docx **不解析 footnotes 关系**：`doc.part.package.part_related_by(".../footnotes")` 抛 `KeyError`。不要试图用它直接操作脚注。
- **两步法**：
  1. python-docx 写正文，脚注位置插入唯一占位符文本（如 `〔FNREF_1〕`，全角括号避免与正文歧义）；
  2. zipfile 重打包：读 `word/document.xml`，正则把占位符替换为
     `<w:r><w:rPr><w:rStyle w:val="FootnoteReference"/></w:rPr><w:footnoteReference w:id="N"/></w:r>`；
     用 lxml 重建整个 `word/footnotes.xml`（保留 `id="-1"` separator、`id="0"` continuationSeparator，追加 N 条 footnote：段落样式 `FootnoteText`、`<w:footnoteRef/>` + 内容 run，字号 `sz val="18"`=9pt）。
- 保存 = zipfile 重写整个 zip：读出所有条目，仅替换 document.xml 与 footnotes.xml，其余原样写回（`zout.writestr(info, data)` 保留原 ZipInfo）。

## lxml 坑

- `etree.SubElement(el, tag, {w("xml:space"): "preserve"})` 抛 `ValueError: Invalid attribute name 'xml:space'`（xml 前缀保留）→ 先建元素再 `t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")`。

## 环境

- macOS 系统 python3 常无 pip；用 `~/.hermes/bin/uv run --with python-docx python3 script.py`（uv 临时依赖，免装环境）。
- 长中文脚本先 write_file 存 .py 再运行（heredoc 偶发编码失败）。

## 《政治与法律》样稿格式规范（实测值，可直接套用）

| 项目 | 值 |
|---|---|
| 页面 | A4 21×28.5cm；边距 上2.05 下1.65 左2.10 右2.10 cm |
| 大标题 | 黑体(eastAsia)+Times New Roman(ascii) 20pt 居中 |
| 作者姓名 | Times New Roman 11pt 居中 |
| 单位 | 楷体 10.5pt 居中 |
| 摘要/关键词 | "摘　要："黑体 + 内容楷体，两端对齐（Normal 样式，首行缩进继承） |
| 一级标题（一、二…） | 黑体 11pt 居中，样式"一级标题"（段前12pt 段后7pt，行距20pt固定） |
| 二级标题（（一）（二）…） | 楷体 10.5pt 左对齐，样式"二级标题" |
| 三级标题（1. 2. …） | 宋体 10.5pt 左对齐，样式"三级标题" |
| 正文 | 宋体(eastAsia)+Times New Roman 10.5pt，两端对齐，首行缩进 266700EMU(≈2字符)，行距 254000EMU(20pt固定)，样式"正文1" |
| 脚注 | Word 真实脚注（页面底部自动编号），字号9pt |

run 字体设置要点：`run.font.name = 西文字体` + `rPr.rFonts.set(qn('w:eastAsia'), 中文字体)` + `run.font.size = Pt(n)`；eastAsia 不设则中文回退默认字体。

## md → docx 段落映射

- `# ` 标题 → 大标题（20pt 黑体居中）；`## ` → 一级标题；`### ` → 二级标题；`#### ` → 三级标题
- `摘　要：`/`关键词：` 行 → 双 run（黑体标签 + 楷体内容）特殊处理
- 文末 `## 脚注` 列表（`[N] 内容`）→ 不输出为正文，转为真脚注内容；正文 `[N]` 标记 → footnoteReference
- `---` 分隔线、空行跳过

## 验证（生成后必跑）

1. `Document(DST)` 重新打开无异常；
2. zipfile 读 document.xml：`footnoteReference` 计数 == 脚注条数，ID 集合 == range(1, N+1) 无缺失无重复；
3. footnotes.xml 条目数 == 引用数（-1/0 系统脚注除外）；
4. 抽样段落 style/字体/字号/对齐；抽查脚注 [1]、[N] 内容与 md 一致；
5. 交付：文件路径（MEDIA:）+ 格式说明表（页面/字体/标题层级/脚注），提醒用户打开通读校对。

## 与相邻技能分工

- chinese-law-paper-writing（user-owned，勿编辑）：五问/反说/逻辑链纪律、期刊适配、引注纪律总纲；
- legal-paper-argumentation（user-owned，勿编辑）：推理链与统计口径执行细则；
- 本技能：docx 生产执行细则（真脚注注入、样稿格式复刻）；
- bundled `docx` skill（protected）：通用 docx 操作（合并run/审阅/注释/validate.py）——本技能的两步法脚注注入技术如被该技能采纳可迁移，未采纳前以本技能为准。
