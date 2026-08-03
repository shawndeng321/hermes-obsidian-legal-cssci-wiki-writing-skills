# Session 2026-07-30 (Phase 3): Root Ghost Files, Statute/Case Sections, Subagent QC

## 1. Vault-root ghost files (subdirectory scans miss them)

Obsidian auto-creates 0-byte `.md` files at the vault ROOT when the user clicks an
unresolved `[[wikilink]]`. Standard scans only cover `entities/`, `concepts/`,
`research-design/` — so these ghosts survive every "zero dead links / zero orphan"
verification and the user finds them first.

**Check and clean:**
```bash
find "$WIKI" -maxdepth 1 -type f -name '*.md' -size 0
```
Before deleting, grep the whole vault for `[[<name>]]` inbound links; if none, delete.
If inbound links exist, retarget them to the proper concept page first.
Prevention for the user: Obsidian Settings → Files & Links → disable auto-create.

## 2. Keep frontmatter `sources:` in sync with actual PDF filenames

When PDFs are renamed (e.g., stripping curly quotes `"两高"` → `两高`), the
`sources:` field in frontmatter must match the on-disk name. Verify:
```python
m = re.search(r'sources:\s*\[(.*?)\]', frontmatter)
for src in m.group(1).split(','):
    src = src.strip().strip('"\'')
    if 'raw/' in src and not os.path.exists(f"{wiki}/{src}"):
        # fix: either rename file to match sources, or update sources
```
Prefer renaming the FILE to the clean name (keeps frontmatter quote-free).

## 3. 引用规范 (statutes) section completion

Two defect classes:
1. **Non-statute contamination**: journal names (《法学杂志》《中外法学》), book
   titles (《...释义》《...逐条注释》《行政审判探索与实践》), and paper titles
   (《论...》《...的思考》) get auto-listed as "statutes". Strip with keyword
   blocklist: 学报/杂志/研究/思考/评析/观察/兼评/借镜/探索与实践/价值衡量/释义/注释/逐条.
2. **Missing article numbers**: users want `《工伤保险条例》第14、15、16条`,
   not bare `《工伤保险条例》` (条 level only, no 项/款 needed).

**Extraction** from PDF full text:
```python
re.findall(r'《([^》\n]{2,40})》\s*第\s*([0-9一二三四五六七八九十百]+)\s*条', text)
```
**Normalization pitfall**: PDFs mix Arabic and Chinese numerals
(`第14、十五、15条` after merging). Map 一..十/十四/十五... to ints, dedupe,
sort, re-emit Arabic: `第1、14、15、16条`.
Also fix broken book-title nesting (`《劳动和社会保障部关于实施《工伤保险条例》...`).

## 4. 引用案例 (cases) section completion

Extract from PDF full text — NEVER fabricate:
- Case numbers: `（2019）京01行终123号` → regex `[（(]\s*(\d{4})\s*[）)]\s*([^\s,，。；;]{2,15})\s*第?\s*(\d+)\s*号`
- 指导案例: `指导案例\s*(\d+)\s*号`
- Named cases: 孙立兴案/刘自荣案 etc. (grep known names)
- Judicial replies: `《最高人民法院...(?:批复|答复|复函)》` (key for 批复评析 papers)

If a paper is genuinely case-free (pure theory/legislation pieces), write
`- 本文未引用具体案例，为纯理论分析` — an honest marker, not a blank section.

**Subagent lazy marker**: subagents may write `*案号提取受限*` instead of doing
the extraction. This is a failure disguised as a disclaimer. Re-extract manually;
papers titled 批复评析/司法审查 almost always contain real cases.

## 5. Reverse-link backfill for concept pages

Concept pages have a `## 相关概念` section (name varies — check actual headers).
Entities linking to the concept must also be listed there; Obsidian backlinks panel
is not enough for the user's reading workflow. Script: for each concept, find all
entity pages containing `[[concept]]`, append missing ones as `- [[entity]]`.

## 6. Subagent section-format drift

Subagents writing `## 主要结论\nText` (single newline, no blank line) break:
- regex verifications expecting `## 主要结论\n\n`
- Obsidian rendering (heading glued to body)
After any subagent batch, normalize: `re.sub(r'(## [^\n]+)\n(?=[^\n#])', r'\1\n\n', content)`
and re-run the full 6-dimension check on CONTENT, not on subagent self-reports.

## 7. Subagent batch failure (HTTP 429)

One of two parallel case-extraction batches died with API overload. The parent's
verification (per-file section content scan) caught it. Lesson: dispatch verification
must enumerate the exact files each batch owned and check each one's content —
batch-level "completed" status is not evidence of per-file success.
