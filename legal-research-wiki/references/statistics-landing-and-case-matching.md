# 统计落地与案号匹配技术（2026-08-03实证）

## 一、docx脚注提取（python-docx默认不读脚注）

**问题**：python-docx的 `Document().paragraphs` 只含正文段落，**脚注在 `word/footnotes.xml` 里**——用python-docx提取的正文会静默丢失全部脚注（用户初稿42个脚注曾全丢）。

**正确方法**（zipfile直接解析XML）：

```python
import zipfile, re
z = zipfile.ZipFile('初稿.docx')
footxml = z.read('word/footnotes.xml').decode('utf-8')
# 提取脚注条目
footnotes = re.findall(r'<w:footnote[^>]*w:id="(\d+)"[^>]*>(.*?)</w:footnote>', footxml, re.DOTALL)
texts = {}
for fid, content in footnotes:
    # 关键：排除 w:footnoteRef 元素（脚注自身的序号标记），否则文本开头残留"[]"
    content_clean = re.sub(r'<w:footnoteRef[^>]*/>', '', content)
    ts = re.findall(r'<w:t[^>]*>([^<]*)</w:t>', content_clean)
    txt = ''.join(ts).strip()
    if txt: texts[fid] = txt
# 正文脚注引用位置：document.xml 里的 w:footnoteReference w:id="N"
docxml = z.read('word/document.xml').decode('utf-8')
refs = re.findall(r'<w:footnoteReference[^>]*w:id="(\d+)"', docxml)
```

**要点**：
- 正文脚注位置标记：遍历 `<w:p>` 段落，段内按 `w:footnoteReference` 出现顺序插入 `[脚注N]`
- 脚注文本开头的 `[]` 可能是源文档自带（用户写作残留），也可能是 `w:footnoteRef` 未排除——先排除footnoteRef再看
- 合并产物：正文（带[N]标记）+ `## 脚注` 表（[N] 文本），保证一一对应

## 二、案号精确匹配（论文脚注↔知识库案例）

**问题**：按年份匹配案号会大量误配（"2019"匹配到多个案例）；全角/半角括号都会出现。

**正确方法**：
1. **完整案号**：`（年份+行政区划代码+法院层级+字号）`，如 `（2019）苏0903行初209号`
2. **正则**：`re.findall(r'（(20\d{2})）([^，。；]*?号)', text)` —— `（）`为全角；案例页案号可能用半角`()`，须两套都试
3. **比对**：`full in case_ah or case_ah in full`（完整案号互含），不只用年份
4. **知识库侧索引**：从案例页 `案号**：` 字段提取（一页可能多个案号，如一审+二审+再审）

**教训**：首次匹配11条全"成功"但5条误配（尾号巧合）——必须完整案号复核，且提取正则要同时处理全角/半角括号。

## 三、大样本统计工作流（100+案）

1. 提取全部案例的 `裁判结果/裁判依据/裁判要旨` 到JSON（每案截取前500/300/300字符）
2. 3个子代理并行逐案归类（每批30-40案），分类维度：`final`（认定工伤/不认定/撤销重作/程序/撤诉/其他/无法判定）+ `agency_issue`（举证/概念/程序/其他/无）
3. **严格基于文本**：文本未明说最终结果 → 标"无法判定"，不猜测
4. 合并后算比率：改判率=撤销重作/总数；认定率=认定工伤/总数
5. 年代切片：按年份分段（2003-2010/2011-2016/2017-2024/2025），算各段认定率/撤销率
6. 法条频率：从裁判依据章节 `第X条` 计数（第十四条最高=77次）
7. 写回引注矩阵（口径→数据）+ 研究设计（假说→已验证）+ 交接文件（可执行→已完成）
8. 附样本代表性警示：精选案例库非随机样本
