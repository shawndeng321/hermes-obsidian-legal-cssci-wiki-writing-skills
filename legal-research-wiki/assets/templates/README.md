# 页面模板

新建研究库或新增页面时复制使用。`〈…〉` 为待填内容；HTML 注释（`<!-- -->`）是给代理和作者的填写提示，填写完成后可以删除。模板中的链接是占位符，复制后改成真实页面名。

| 模板 | 页面类型 | 放在哪里 |
|---|---|---|
| `SCHEMA.md`、`index.md`、`log.md` | 根目录元文件 | vault 根目录 |
| `case.md` | case | `entities/案例/` |
| `paper.md` | paper | `entities/引用文献/` |
| `norm.md` | norm（普通法规范页） | `entities/法规范/〈层级〉/` |
| `norm-entity.md`、`norm-version.md`、`norm-clause-version.md` | norm（时序研究：规范实体、版本、条款版本） | `entities/法规范/〈层级〉/〈规范名〉/` |
| `concept.md` | concept | `concepts/` |
| `comparison.md` | comparison | `comparisons/` |
| `wiki-design-brief.md` | research-design（建库访谈结果：Wiki 设计书 / 加深方案） | `research-design/` |
| `research-design.md`、`claim-evidence-matrix.md` | research-design | `research-design/` |
| `journal-style-card.md` | methodology | `methodology/` |
| `model-article.md` | model-article | `entities/范文/` |
| `anchor-draft.md` | draft（底稿） | `entities/底稿/` |
| `moc.md`、`handoff.md`、`writing-outline.md` | moc、handoff、query | `queries/` |

这些模板来自一个实际运行的法学研究库，经通用化处理；页面分类、章节和字段可以按项目调整，调整后同步修改 `SCHEMA.md`。
