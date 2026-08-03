# Session Lessons: 2026-07-24

## User Corrections (First-Class Signals)

### 1. "Empty wiki pages are useless"
User explicitly stopped work and demanded all pages be filled with substantive content.
Created `wiki-content-completeness` skill as a mandatory discipline. Every page must have
at least 500 characters of meaningful content. No "详见原始文件" placeholders.

**Root cause**: Batch-creating entity pages from parsed JSON produced empty shells with only
YAML frontmatter. The agent prioritized speed over quality.

**Fix**: Read each source file completely before writing its wiki page. After writing, verify
file size with `terminal wc -c` (NOT `read_file` which caches). If <500 bytes, rewrite.

### 2. "Tags should be Chinese, not pinyin"
User found pinyin tags unreadable in Obsidian Graph View. All tags converted from
`gongshang-renting` → `工伤认定` etc.

**Fix**: Always use native-language tags. For Chinese legal research: 工伤认定, 程序违法,
法律适用, 争议问题, 举证责任, 新业态, 上下班途中, 最高人民法院.

**Bulk conversion**: Use `sed -i ''` on filesystem, NOT read_file→write_file loops.
read_file caching causes silent data loss in loops.

### 3. "Ask before bulk ingestion"
User stopped a 121-case bulk ingestion: "等一下弄错了 把前面摄入的内容都去掉"
Then later: "不要自作主张一口气全吞"

**Fix**: Always preview directory contents and confirm scope before processing 10+ files.
Even when user says "ingest all", break into thematic batches and discuss after each.

### 4. "Separate vaults per research project"
User found mixing 工伤认定 and 长三角治理 in one wiki "太杂乱反而我搞不清".

**Fix**: One vault per research project. `~/Desktop/法学wiki/工伤认定群案研究Wiki/`
not `~/Desktop/法学研究wiki/` (the old mixed vault).

### 5. "Always ask research design FIRST"
User: "之后都要记住要先问我研究思路是什么 然后再让我摄入论文和案例"

**Fix**: MANDATORY sequence for new wiki:
1. Ingest CSSCI methodology as concept page
2. Ask user for research design
3. Write research-design page
4. Only then ingest papers → cases

### 6. "Every item in a compilation gets its own wiki page"
User: "如果一个文件里面都是案例、汇编、司法解释等等的 要把里面所有案例、汇编、司法解释等等都分别建wiki"

**Fix**: When a .docx contains 133 cases or 29 guiding cases, extract EACH as its own
entity page. Do NOT create one summary page for the whole compilation.

### 7. "Index must list every individual page"
User found index.md had section headers but no individual links: "这些还是没有单独的wiki页面呢？"

**Fix**: After batch creation, rebuild index.md with `- [[slug]]` for EVERY page.
Section headers alone are invisible in Obsidian.

## Technical Quirks Discovered

### read_file caching
`read_file` aggressively caches and deduplicates. After `write_file`, a subsequent
`read_file` returns stale content with line-number prefixes (e.g., `6|tags: [...]`).
Using this cached content as input to `write_file` corrupts files to zero bytes.

**Workaround**: For post-write verification, use `terminal` with `wc -c` or `head`.
For bulk string replacements, use `sed -i ''` directly on the filesystem.

### write_file silent failures
`write_file` through `execute_code` sometimes silently fails on large content or
rapid successive calls. Files end up empty or with partial content.

**Workaround**: After batch writes, run `find ... -size -500c` to detect thin pages.
Rewrite failed pages using Python's `open()/write()` via `terminal`.

### python-docx parsing
Gazette case compilations have TOC entries followed by full case text. The TOC
entries have page number suffixes (e.g., `案\t186`) that must be stripped.

Compilation .docx files may contain ONLY the TOC, not full case text. Always verify
by searching for 工伤 keywords in the full paragraph list before assuming full text
is available. Full case text may be in a SEPARATE compilation file (e.g., the 121-case
compilation has full text, while the 133-case gazette compilation only has TOC + some
full text).

### Duplicate file detection
macOS creates `(1)` suffix copies. Use `diff` or `shasum` to verify before filtering.
In this session, 5 of 30 PDF files were byte-identical duplicates.

## Model Switch
Session started on DeepSeek, switched to GLM-5.2 (zai provider) mid-session.
No workflow changes needed — both models handle the same tool calls.
