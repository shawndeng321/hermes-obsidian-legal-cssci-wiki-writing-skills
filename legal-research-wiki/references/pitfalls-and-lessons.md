# Pitfalls and Lessons

This reference contains the full failure-mode catalog moved out of the main skill to keep its routing file below Hermes's size limit.

- **CRITICAL: Recursive vault scans.** This wiki stores pages below nested directories such as `entities/引用文献/`, `entities/案例/`, and `entities/底稿/`. A top-level `os.listdir()` or `Path.glob('*.md')` scan falsely reports valid literature links as dead. Build the page-stem set with recursive traversal (`Path.rglob('*.md')`) before judging links.
- **CRITICAL: Validate YAML after every frontmatter patch.** When replacing a frontmatter block with surrounding context, an accidental leading space before a top-level key (for example ` type: entity`) can change YAML structure. Re-parse the edited page immediately and inspect the diff; never assume a successful patch means valid frontmatter.
- **CRITICAL: User-facing audit reports must be action-first.** For this user's legal-Wiki work, do not lead with a long inventory. State the first batch, exact pages, one change per page, and a short verification result. Keep later batches deferred until the user can see and accept the first result.
- **CRITICAL: Vault-root ghost files.** Obsidian auto-creates 0-byte `.md` files at the vault ROOT when the user clicks an unresolved wikilink. Subdirectory-only scans (entities/concepts/research-design) miss them — run `find "$WIKI" -maxdepth 1 -name '*.md' -size 0` in every health check, grep for inbound links, then delete or retarget.
- **CRITICAL: `&`-suffix ghost files resurrect via workspace.json (GHOST-AMP-CLEANUP 2026-08).** Obsidian auto-creates 0-byte `案例N-…&.md` files (or any `&`-bearing variant) when a link with `&` is clicked, AND `.obsidian/workspace.json` → `lastOpenFiles` stores their paths — so Obsidian **recreates deleted ghost files on every launch**. Deleting the files alone never fixes it. Fix: (1) archive ghosts to `.maintenance/ghosts/`; (2) strip ALL `entities/案例` paths containing `&` from workspace.json (re-check with `grep -c '&\.md' .obsidian/workspace.json` — first pass can miss entries); (3) add `"userIgnoreFilters": [".maintenance","ghosts"]` to `.obsidian/app.json` so backup dirs don't display; (4) tell user to Cmd+Q fully quit Obsidian (in-memory workspace overwrites cleanup on window-close).
- **CRITICAL: Graph View ghost nodes ≠ missing files — example wikilinks in maintenance docs get parsed even inside backticks (GRAPH-CLEANUP 2026-08).** When Graph View shows blank/unresolved nodes but the file system is clean, the culprit is example `[[wikilinks]]` in SCHEMA.md / log.md / 台账 (e.g. `[[wikilinks]]`, `[[目标|显示]]`, `[[案例N-标题|X案]]`, `[[A|[[B|C]]]]`). **Obsidian's link graph parses wikilinks inside backticks too** — backticks only affect rendering, not link resolution. Fix: write example links as plain text (strip the `[[ ]]` entirely, add `（示例）` note) in ALL maintenance docs — including new log entries you append yourself (self-referential trap: a log entry describing this very bug reintroduced 4 ghost nodes). Verify with a vault-wide unresolved-link scan: parse every `[[...]]`, split alias on `\|` or `|`, check target stem exists. A clean file list does NOT mean a clean graph.
- **CRITICAL: 核心论点 section header leak.** PDF structural headers (`**一、...**`, `**二、...**`) can be dumped verbatim into `## 核心论点` sections, making them unreadable. Scan for `\*\*[一二三四五六]、...\*\*` patterns in core argument sections and rewrite as proper thesis statements. See `references/session-2026-07-30-wangdongwei-repair.md`.
- **CRITICAL: Wrong section as conclusion.** pymupdf may grab a mid-body numbered section (e.g., `三、再造`) as the conclusion instead of the actual `余论`/`结语` at the paper's end. Check that conclusion text doesn't start with a numbered section header. Search for `余论` as an additional conclusion marker. Same reference file.
- **CRITICAL: Three-section triage.** When one of `## 摘要` / `## 核心论点` / `## 主要结论` has a defect, check ALL THREE — they often fail together. Wang Dongwei's article had abstract typo + core-argument header leak + mid-body-as-conclusion simultaneously.
- **CRITICAL: Keep `sources:` in sync with PDF filenames.** After renaming PDFs (e.g., stripping curly quotes), verify every frontmatter `sources:` path with `os.path.exists`. Prefer renaming the file to the clean name.
- **CRITICAL: Subagent lazy markers and format drift.** Subagents may write `*提取受限*` disclaimers instead of extracting, and `## Header\nText` without the blank line — both pass batch-level "completed" status while failing content. Verify per-file content after every delegation batch; re-extract manually when found.
- Don't mass-ingest without user buy-in. Survey, discuss, ask scope.
- Don't silently filter duplicate files. Tell the user.
- Batch PDF extraction goes through a temp file, not inline.
- **CRITICAL: PDF format artifacts survive into wiki pages.** Always run the
  format check above after batch ingestion. Common artifacts: ］［ brackets,
  broken lines, corrupted keywords. See "PDF Format Artifact Cleanup" section.
- **CRITICAL: Cross-reference network is mandatory.** Content + no dead links is NOT
  enough. If 25 papers each link only to the methodology page and 1-2 concepts, the
  wiki is a pile of isolated islands. Every paper MUST link to the anchor/draft (底稿)
  AND to at least 2 other papers, with specific theoretical connections. Run the
  cross-reference check after every ingestion batch. See "Cross-Reference Network
  Construction" section above.
- **CRITICAL: Dead links after ingestion.** Always run the dead-link check above
  after creating pages. Zero dead links is the target. The user WILL find dead
  links in Obsidian and lose trust in the wiki.
- **CRITICAL: "详见原文" is NOT acceptable content.** If auto-extraction fails,
  re-extract with a dedicated script reading all pages with multiple regex patterns.
- **CRITICAL: Curly-quote filename mismatch.** Chinese PDF filenames from CNKI
  frequently contain Unicode punctuation (curly quotes ""、——、：) that differs
  from ASCII equivalents in user-provided lists. A file listed as
  `论工伤认定"循环诉讼"...pdf` with straight quotes will appear MISSING.
  Always verify filenames against the filesystem with `ls` or
  `search_files(target='files')` before assuming absence.
- **CRITICAL: search_files false negatives for Chinese patterns.** Content search via
  `search_files` can return 0 matches for Chinese regex patterns that `grep` finds
  dozens of (observed: pattern `五问研究设计|群案研究：五问` → 0 results, while
  `grep -rn` found 38 matches across 38 files). NEVER conclude "no backlinks /
  isolated page / missing term" from a search_files zero result alone — cross-validate
  suspicious zeroes with terminal `grep -rn` before reporting a negative finding or
  starting remediation work. This almost caused a wrong "研究设计页是孤岛" report.
- **CRITICAL: read_file dedup + write_file corruption.** Never use `read_file()` → string replace → `write_file()` in a loop for bulk edits. The `read_file` dedup system returns cached content with line-number prefixes (`6|tags: [...]`), which get written back as actual content, corrupting files to zero-byte. Use `sed` on the filesystem for bulk tag/string replacements instead.
- **CRITICAL: Each page must be in index.md.** After batch-creating entity pages from compilations, rebuild `index.md` to list every single page with `- [[slug]]`. Section headers without individual links will look empty to the user.
- **CRITICAL: YAML frontmatter quote escaping.** Chinese PDF filenames with curly quotes
  (""") carried into `title:` and `sources:` fields cause Obsidian to mark pages red
  (frontmatter parse failure). Always run the YAML quote check after batch ingestion
  and strip ALL quotes from frontmatter fields. See "YAML Frontmatter Quote Escaping" section.
- **CRITICAL: Fragmented conclusions.** pymupdf regex may extract mid-text fragments
  as conclusions (starting with `，` or `；`). Always check conclusion quality — if it
  starts with punctuation or is <100 chars, manually rewrite from the PDF's actual
  concluding section. See "Fragmented Conclusion Detection" section.
- **Chinese punctuation in execute_code string literals.** In older Hermes
  runtimes, full-width punctuation like `、` (U+3001) and `""` (U+201C/U+201D)
  could cause `SyntaxError: invalid character` when inline in Python source
  inside `execute_code`. As of 2026-07-30, the current runtime handles Chinese
  Unicode text in string literals correctly. The `write_file` to `/tmp/` →
  `open().read()` approach remains a safe fallback if any encoding issue
  arises, but is no longer strictly required.
  See `references/session-2026-07-30-conclusion-reextraction.md` and
  `references/session-2026-07-30-threesection-repair.md` for details.
- **CRITICAL: Fullwidth English abstract contamination.** CNKI PDFs contain
  English abstracts in fullwidth characters (`ＯｎｔｈｅＪｕｄｉｃｉａｌ...`)
  after the Chinese conclusion. The naive regex `[Ａ-Ｚａ-ｚ０-９...]+` to strip
  them is too aggressive — it nukes Chinese text that has scattered fullwidth
  chars. Instead, remove fullwidth-English-dominant LINES:
  `if fw_count > cn_count * 2 and fw_count > 10: continue`. See the reusable
  `clean_conclusion()` function in
  `references/session-2026-07-30-conclusion-reextraction-batch2.md`.
- **CRITICAL: Embedded page headers in mid-sentence text.** PDF page headers
  (`0\n6\n中州学刊2020 年第12 期\n`) get embedded mid-sentence during extraction.
  Strip them with targeted regex BEFORE running the line-join regex, otherwise
  they merge into the text and create garbage like "在06中州学刊2020年第12期效果上是存疑的".
- **CRITICAL: Section headers split across newlines.** 王敏's `结语` header
  appears as `结\n语` (two chars on separate lines) in extraction. A simple
  `find("结语")` fails. Always try both `"结语"` and `"结\n语"` patterns.
  Also check for `结　语` (fullwidth space U+3000 between chars).
- **CRITICAL: Surgical section replacement with regex.** When replacing a single
  section (e.g., `## 主要结论`) in a wiki page, use the pattern
  `r'(## 主要结论\n)([\s\S]*?)(\n## |\Z)'` to replace ONLY that section's content
  while preserving all other sections. Do NOT reconstruct the full file manually —
  this risks dropping or corrupting other sections.
- **Don't create compilation summary pages INSTEAD of individual pages.** Users expect to click each individual case/interpretation/Q&A, not just a page describing the compilation. Summary pages are supplementary, not a substitute.
- **One vault per research project.** When the user has multiple distinct research domains (e.g., 工伤认定 and 长三角治理), create separate wiki vaults. Mixing unrelated domains clutters Graph View, dilutes search, and makes tag taxonomies unmanageable. Cross-project methodology reuse happens via Skills, not shared wiki pages.
- **CRITICAL: DOCX separator vs subtitle clash.** When parsing Chinese case compilations (.docx), separators are long dash lines (`————————————————————————————`, ~28 em dashes). Some case titles contain `——` (2 dashes) as subtitle delimiters. Using `'——' in line` for separator detection silently drops all subtitle-bearing cases. Use `line.count('—') > 5` instead. See `references/docx-case-parsing-lessons.md`.
- **CRITICAL: Duplicate filenames in batch creation.** When two cases generate the same slug (e.g., "李某" in two different years), the second `write_file` overwrites the first. Use a counter dict to append `-2`, `-3` suffixes. See `references/docx-case-parsing-lessons.md`.
- **CRITICAL: Batch reverse-link insertion must exclude self-links and dedupe.** When programmatically inserting "与其他案例的关联" reverse entries across many case pages, a page must never link to itself — the batch script inserted `- [[案例74-韩某…]]` (target == the page being edited) with a misattributed description into 26 pages in one pass. Also check for duplicate entries of the same target (one correct entry + one prefixed `与[[...]]的关联` variant). Post-insertion audit: regex per page for `\[\[<own-stem>` (self-link) and Counter over link targets (duplicates); delete the malformed lines. The same bug family can occur when reverse-linking any entity type (papers, norms).
- **CRITICAL: Truncated wikilinks that swallow the next section heading (CASE83-LINK 2026-08).** A malformed link like `[[案例62-某劳务公司…案## 相关概念` (missing closing `]]`; the following `## 相关概念` heading gets absorbed INTO the link target) breaks the page structure AND the link. It survives dead-link scans because the target string contains `##` and no closing bracket pair — a plain `[[…]]` regex never sees it. Detection: scan for `\[\[[^]]*##` (link containing `##`) and compare per-file `[[` vs `]]` counts (unbalanced = truncated link). This is the only surviving malformed link after the year-rename batch — batch renames must include a truncated-link sweep, not just the four normal link forms.
- **CRITICAL: OPT execution-record numbering drift.** Execution-record OPT numbers can drift from the task ledger (observed: the second batch of OPT-001 was logged as `OPT-002` while ledger OPT-002 is a *different* task — the case-generator script). Before appending an execution record, check its number against the ledger's task status table; when a conflict is found, keep historical entries verbatim and add a clarification note in the ledger instead of rewriting history.
