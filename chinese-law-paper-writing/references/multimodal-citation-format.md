# Note-Level 引注格式（回答/查询溯源）— 多模态扩展

> **来源**：multimodal-wiki v1.0.0（kigner/multimodal-wiki），2026-08 融合。
> 用途：查询知识库或写作支撑时，每个事实主张必须能追溯到具体 raw 源文件（绝对路径）。
> 与 [citation-integrity.md](citation-integrity.md)（来源核验）互补：本格式规定“回答如何呈现来源”，citation-integrity 规定“来源如何核验”。
> 与法学纪律一致：来源性主张（法条/案号/文献页码）必须能回溯到库内页面 + raw 原始材料；禁止编造路径。

# Citation Format for Query Answers (note-level provenance)

Default Query behavior (Core Operations → Query, step ④) only cites `[[page]]`
wikilinks: "Based on [[page-a]]...". That tells the reader *which wiki page* an
answer used, but not *which source paper* a specific claim came from — so answers
end up with floating quotes like `§3.3: "..."` and no path back to the original.

This doc upgrades Query answers to **note-level provenance**: every factual claim
carries the raw source note it traces to, as a copy-pasteable absolute path.

## 宿主呈现差异（兼容 Hermes 与 Codex）

Hermes 与 Codex 的链接渲染能力可能不同：有的界面只显示纯文本，有的界面能打开 Markdown 本地文件链接。因此统一采用以下最低兼容格式：

- The anchor is a **copy-pasteable absolute native path** the reader can paste into
  Explorer / an editor. This is the required, load-bearing part.
- 不依赖 `file:///`；只有宿主明确支持时，才额外提供 Markdown 可点击路径。
- **Do NOT use `^[raw/...]` footnotes** in answers — page-internal, also plain text.
- Click-to-open lives in **Obsidian** (open the same vault): the `[[entity-page]]`
  wikilink in each source line is the jump-in point for the graph.

## Rules

1. **Trace before you write.** For each relevant Layer-2 page, read its `sources:`
   frontmatter and inline `^[raw/...]` markers — these hold the real raw-note
   filenames. Map each claim to the specific raw note it comes from. Never invent a
   path or a section number.

2. **Every claim carries a source.** No statement of fact may appear without a
   source. A bare section quote with no path (e.g. `§3.3: "uses a CLIP text
   encoder"`) is **not acceptable** — that is the exact failure this doc prevents.

3. **Source line format** — one per numbered marker, in a `## Sources` block
   (localize the heading, e.g. `## 来源`):

   ```
   [1] [[entity-page]] · `<WIKI_PATH>\raw\papers\<file>.md` · §x.y (optional short quote)

   [2] [[entity-page]] · `<WIKI_PATH>\raw\papers\<other>.md` · §x.y
   ```

   - **One BLANK LINE between every entry (hard break — required).** Markdown 渲染器可能折叠连续单换行；空行可以让每个 `[n]` 在 Hermes、Codex 和纯文本环境中都保持独立。
   - **`[[entity-page]]`** — the Layer-2 page, for Obsidian navigation.
   - **Backticked absolute native path** — *required, the anchor.* Native Windows
     path per [multimodal-pdf-extraction.md](../../legal-research-wiki/references/multimodal-pdf-extraction.md). Raw filenames contain `[hash]` brackets, so keep
     the path in backticks — never wrap it in `[[ ]]` or `^[ ]`.
   - **§x.y** — *only if it actually appears in the raw note.* Sections are
     best-effort: ingestion concatenates page text without reliable section markers,
     so never manufacture a section you cannot see.

4. **Every entry repeats its own path.** Do NOT write a bare "同上" / "same" /
   "ditto" that omits the path. If two claims share a source, repeat the full
   backticked path on each line — it's cheap and keeps every line self-resolving.

5. **Resolve Layer-2 to the raw note.** If a claim is supported by a Layer-2 page
   (a `queries/`, `comparisons/`, or `concepts/` page rather than a paper), follow
   that page's `sources:` down to the underlying raw note and cite the **raw-note
   path** — never stop the chain at the Layer-2 page. (Failure example: citing
   `[[arc2face-improvements]] §2.2` with no `raw/papers/...md` behind it.)

6. **Untraceable claims.** If a claim cannot be traced to a specific raw note, drop
   it or mark it `[来源不明]`. Do not fabricate a citation to fill the slot.

## 格式示例

以下仅展示格式，占位符不代表真实法律结论或真实来源：

```
某项来源性主张应在句末标注来源编号 [1]；另一项主张即使来自同一材料，也应重复完整路径 [2]。

## 来源
[1] [[某案例页]] · `<WIKI_PATH>\raw\papers\<judgment-file>.md` · §裁判理由

[2] [[某案例页]] · `<WIKI_PATH>\raw\papers\<judgment-file>.md` · §裁判结果
```

## Key points

- **The absolute native path is the contract.** Even when the host cannot render a clickable link, the reader can copy the path to open the source.
- **Note-level, not page-level:** the anchor is the specific extracted source note under `raw/`; from it the reader reaches the adjacent original file or recorded source URL.
- **Don't invent.** Copy paths verbatim from `sources:` / `^[...]`; copy sections
  only if present. An honest "[来源不明]" beats a fabricated citation.
