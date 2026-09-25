# DOCX 脚注提取（python-docx 不读脚注）

**关键事实**：python-docx 的 `Document().paragraphs` **只返回正文段落，不含脚注**。脚注在 docx 包内的 `word/footnotes.xml`。只读正文会静默丢失全部脚注——初稿的引注装置（案例脚注带案号、文献脚注带页码）全丢，用户一定会问"你能读到我的脚注吗"。

## 提取方法

```python
import zipfile, re
z = zipfile.ZipFile('初稿.docx')

# 0) 先确认存在脚注文件
print([n for n in z.namelist() if 'foot' in n.lower()])  # 期望含 word/footnotes.xml

# 1) 提取脚注文本（每个 w:footnote 按 w:id 取全部 <w:t> 拼接）
footxml = z.read('word/footnotes.xml').decode('utf-8')
footnotes = re.findall(r'<w:footnote[^>]*w:id="(\d+)"[^>]*>(.*?)</w:footnote>', footxml, re.DOTALL)
fn_texts = {}
for fid, content in footnotes:
    ts = re.findall(r'<w:t[^>]*>([^<]*)</w:t>', content)
    txt = ''.join(ts).strip()
    if txt: fn_texts[fid] = txt

# 2) 正文脚注引用位置（按出现顺序编号）
docxml = z.read('word/document.xml').decode('utf-8')
refs = re.findall(r'<w:footnoteReference[^>]*w:id="(\d+)"', docxml)

# 3) 输出：正文段落带 [脚注N] 位置标记 + 文末脚注表 [N] 文本
```

## 陷阱

1. **脚注文本自带 `[]` 前缀**：脚注 0 的原文是 `<w:t>[</w:t>...` —— 源 docx 的脚注内容本身以 `[]` 开头（文献管理工具/复制粘贴残留）。**不要当成提取 bug 反复"修复"**——先看 footnotes.xml 原始 XML 确认是原文如此，再在 md 输出里清理（`re.sub(r'(\[\d+\]) \[\]', r'\1 ', s)`）。
2. **脚注自身序号是 `<w:footnoteRef/>` 元素**，不是文本——不需要（也不用）提取；正文引用顺序就是脚注编号。
3. **正则提取 `<w:t>` 时脚注文本可能跨多个 run**，必须 `''.join(ts)` 而不是取第一个。
4. 生成 md 时：正文在 `footnoteReference` 处插入 `[脚注N]`（按 refs 顺序），文末列 `## 脚注（正文引用顺序）` 表 `[N] 文本`；未被正文引用的脚注单独标 `[未引用]`。

## 引用位自带方括号时：工作版标记呈现为 `[[脚注N]]`

有些稿件的正文引用位本身被字面方括号包着（`[` + 脚注引用 + `]`，Word 中显示为 [①] 样式）。按第 4 条插入 `[脚注N]` 后，正文会呈现为 `[[脚注N]]`：

- 先检查这一点：统计引用位前后是否紧邻字面 `[`、`]`。若全部如此，`[[脚注N]]` 就是该项目工作版的既定形态，各版本保持一致（版本之间 diff 才干净），不要清理成单方括号；
- 它看起来像 Obsidian 链接，但不是：`scripts/check_wikilinks.py` 会把 `drafts/` 中的 `[[脚注N]]` 列为容忍类，不计死链，不要批量“修复”；
- 脚本用两步：先在引用位插入不与正文冲突的占位符（如 `«FN1»`），再把 `\[«FN(\d+)»\]`（连同字面括号）整体替换为 `[[脚注N]]`；断言替换数、标记数、脚注表行数都等于引用数，且无残余占位符；
- 生成后查“杂项方括号”：先去掉完整的 `[[脚注N]]`，再找残余的 `[`、`]`。合法的残余包括脚注表行首的 `[N] ` 和文献中的国别前缀（`[德]`、`[日]`），不是缺陷。

## 验收

- `len(fn_texts)` 应等于正文 `len(refs)`（或至少脚注数>0）
- 案例脚注应带案号（如"（2019）苏0903行初209号"），文献脚注带期刊+期数+页码
- 带案号的案例脚注可与库内案例页回验，作为“初稿用了哪些案例”的索引（案号匹配规则见 `linking-and-cross-references.md`）
