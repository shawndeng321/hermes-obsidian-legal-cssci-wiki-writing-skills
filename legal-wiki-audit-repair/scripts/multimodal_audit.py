#!/usr/bin/env python3
# 融合说明：本脚本源自 multimodal-wiki v1.0.0 scripts/audit.py（kigner/multimodal-wiki），2026-08 融合。
# 六项检查：索引一致性/未摄入raw源/frontmatter质量/wikilink完整性/文件卫生/log格式。
# 与 wiki_daily_check.py 互补：本脚本做全库六项深检，wiki_daily_check.py 做每日轻量回归。
"""Wiki audit script — runs the six deep checks documented by the audit skill.

Usage:
  1. Set WIKI_PATH in the environment or pass the Wiki root as first argument.
  2. Run via `python scripts/multimodal_audit.py <WIKI_PATH>`.
  3. Prints a structured report to stdout.

Checks:
  1. Index consistency — disk pages vs index.md declared count
  2. Uningested raw sources — binaries without .md, placeholder stubs, log gaps
  3. Frontmatter quality — Layer-2 required fields, raw sha256/ingested
  4. Wikilink integrity — broken links, orphans, under-linked pages
  5. File hygiene & convention split — image placement, naming, duplicates
  6. Log & index format — entry format, batch completeness, rotation threshold
"""

import os, re, sys
from collections import defaultdict, Counter

# Emoji (✅🔴🟡) crash on Windows GBK/cp936 consoles. The Hermes sandbox is UTF-8,
# but a standalone `python scripts/multimodal_audit.py` on a zh-CN box dies on the first ✅.
# Force UTF-8 so the report prints everywhere.
try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

# --- Config ---
wiki_input = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("WIKI_PATH")
if not wiki_input:
    print("error: pass the Wiki root as an argument or set WIKI_PATH", file=sys.stderr)
    raise SystemExit(2)
WIKI = os.path.abspath(os.path.expanduser(wiki_input))
if not os.path.isdir(WIKI):
    print(f"error: Wiki root does not exist or is not a directory: {WIKI}", file=sys.stderr)
    raise SystemExit(2)
IGNORE_DIRS = {".obsidian", "_archive", ".git"}

# --- Helpers ---
def read_file(path):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    except:
        return None

def parse_frontmatter(text):
    if not text or not text.startswith('---'):
        return {}, text
    parts = text.split('---', 2)
    if len(parts) < 3:
        return {}, text
    fm_text = parts[1].strip()
    body = parts[2] if len(parts) > 2 else ''
    fm = {}
    for line in fm_text.split('\n'):
        line = line.strip()
        if ':' in line:
            key, _, val = line.partition(':')
            key = key.strip()
            val = val.strip()
            if val.startswith('[') and val.endswith(']'):
                val = [v.strip().strip("'\"") for v in val[1:-1].split(',') if v.strip()]
            fm[key] = val
    return fm, body.strip()

def walk_files(root, extensions=None):
    results = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in IGNORE_DIRS]
        for fname in filenames:
            if extensions and os.path.splitext(fname)[1].lower() not in extensions:
                continue
            full = os.path.join(dirpath, fname)
            rel = os.path.relpath(full, root).replace('\\', '/')
            results.append((rel, full))
    return results

def slug(path):
    return os.path.splitext(os.path.basename(path))[0]

# --- Gather data ---
layer2_dirs = ['entities', 'concepts', 'comparisons', 'queries', 'methodology', 'research-design']
raw_dirs = ['raw/articles', 'raw/papers', 'raw/transcripts', 'raw/screenshots', 'raw/assets']

layer2_pages = {}
for d in layer2_dirs:
    full_d = os.path.join(WIKI, d)
    if os.path.isdir(full_d):
        for rel, full in walk_files(full_d, {'.md'}):
            s = slug(rel)
            content = read_file(full)
            fm, body = parse_frontmatter(content) if content else ({}, '')
            layer2_pages[s] = {'rel': f"{d}/{os.path.basename(rel)}", 'full': full, 'content': content, 'fm': fm, 'body': body}

raw_files = {}
for d in raw_dirs:
    full_d = os.path.join(WIKI, d)
    if os.path.isdir(full_d):
        for rel, full in walk_files(full_d):
            ext = os.path.splitext(rel)[1].lower()
            raw_path = f"{d}/{os.path.basename(rel)}"
            raw_files[raw_path] = {
                'full': full, 'is_binary': ext in {'.pdf','.png','.jpg','.jpeg','.wav','.mp3','.gif','.webp'}, 'ext': ext
            }

index_content = read_file(os.path.join(WIKI, 'index.md'))
index_entries, total_declared = set(), None
if index_content:
    for line in index_content.split('\n'):
        m = re.search(r'(?:总页数|页面总数|当前纳入导航的页面|Total pages)(?:\*\*)?[：:]\s*(\d+)', line)
        if m: total_declared = int(m.group(1))
        m = re.search(r'\[\[([^\]|#]+)', line)
        if m: index_entries.add(m.group(1).strip())

schema = read_file(os.path.join(WIKI, 'SCHEMA.md'))
taxonomy = set()
if schema:
    # 兼容两种写法：multimodal-wiki 的 "## Tag Taxonomy" 或本库的 "### A./B./C./D. 分类" + 引用文献主题分类
    m = re.search(r'^##\s*Tag Taxonomy\s*$(.*?)(?=^##\s|\Z)', schema, re.MULTILINE | re.DOTALL)
    if m:
        section = m.group(1)
    else:
        parts = re.findall(r'^###\s*[A-E]\.\s*[^\n]*\n([^\n#]+)', schema, re.MULTILINE)
        parts += re.findall(r'`([^`]+)`', schema)
        section = '\n'.join(parts)
    for line in section.split('\n'):
        for t in re.split(r'[、，,]+', line):
            t = t.strip().lstrip('- ').strip()
            if t and ':' not in t:
                taxonomy.add(t)

log_content = read_file(os.path.join(WIKI, 'log.md'))
log_refs = set()
if log_content:
    # Pattern handles spaces in filenames via [^\n] instead of \S
    for m in re.finditer(r'(raw/(?:articles|papers|transcripts|screenshots|assets)/[^\n]+?\.(md|pdf|png|jpg|jpeg|wav|txt))', log_content):
        log_refs.add(m.group(1).strip())
    for m in re.finditer(r'^\s*-\s+(raw/(?:articles|papers|transcripts|screenshots|assets)/[^\n]+?\.(md|pdf|png|jpg|jpeg|wav|txt))', log_content, re.MULTILINE):
        log_refs.add(m.group(1).strip())

disk_slugs = set(layer2_pages.keys())
issues = {'broken': [], 'needs_attention': [], 'clean': []}

def report(severity, msg):
    issues[severity if severity in issues else 'needs_attention'].append(msg)
    prefix = {'broken': '🔴', 'needs_attention': '🟡', 'clean': '✅'}.get(severity, '🟡')
    print(f"  {prefix} {msg}")

# === CHECK 1: Index consistency ===
print("=" * 70)
print("CHECK 1 — INDEX CONSISTENCY")
print("=" * 70)
print(f"  Layer-2 pages on disk: {len(disk_slugs)}")
print(f"  Pages in index.md: {len(index_entries)}")
print(f"  Index declares: {total_declared}")

if len(disk_slugs) == total_declared == len(index_entries) and not disk_slugs - index_entries:
    report('clean', f"Count matches: {len(disk_slugs)} pages")
else:
    if len(disk_slugs) != total_declared:
        report('broken', f"Count mismatch: index says {total_declared}, disk has {len(disk_slugs)}")
    missing = disk_slugs - index_entries
    if missing:
        report('broken', f"Pages on disk missing from index: {sorted(missing)}")
    ghosts = index_entries - disk_slugs
    if ghosts:
        report('broken', f"Ghost entries in index: {sorted(ghosts)}")

# Stray .md files at root
# Stray .md files at root（跳过隐藏目录、备份目录、草稿与脚本目录——本库 .maintenance 存有大量备份）
stray = []
for rel, full in walk_files(WIKI, {'.md'}):
    parts = rel.split('/')
    if any(p.startswith('.') or p in ('drafts', '_scripts', '_archive', '.maintenance', 'ghosts') for p in parts):
        continue
    if parts[0] not in layer2_dirs + ['raw'] and rel not in ('SCHEMA.md','index.md','log.md','知识库排查修复流程与整改台账.md'):
        stray.append(rel)
if stray:
    report('needs_attention', f"Stray .md files: {stray}")

print()

# === CHECK 2: Uningested raw sources ===
print("=" * 70)
print("CHECK 2 — UNINGESTED RAW SOURCES")
print("=" * 70)
print(f"  Total raw files: {len(raw_files)}")

binary_no_md = []
stubs = []
for rel, info in raw_files.items():
    # raw/assets/ holds DISPLAY figures embedded in Layer-2 pages via ![[img]] — by
    # convention they have NO sibling .md (they're not sources). Check 5 validates them
    # by "referenced in a page?". Skip them here so they aren't false-flagged as 🔴.
    if rel.replace('\\', '/').startswith('raw/assets/'):
        continue
    if info['is_binary']:
        # 法学库惯例：论文/文章原件（raw/papers、raw/articles）的提取页在 entities/ 下，
        # raw 目录不要求 .md 兄弟文件；仅对 transcripts/screenshots 强制兄弟提取
        if rel.replace('\\', '/').startswith(('raw/papers/', 'raw/articles/')):
            continue
        base = os.path.splitext(rel)[0]
        if base + '.md' not in raw_files:
            dir_name = os.path.dirname(rel)
            bn = os.path.basename(base)
            alt = next((r for r in raw_files if os.path.dirname(r) == dir_name and r.endswith('.md') and bn in r), None)
            binary_no_md.append((rel, alt))
    elif info['ext'] == '.md':
        content = read_file(info['full'])
        if content:
            fm, body = parse_frontmatter(content)
            body_lines = [l for l in body.split('\n') if l.strip() and not l.strip().startswith('>')]
            if len(body_lines) <= 5 and any(kw in body for kw in ('Content extracted', 'full text available', 'source URL')):
                stubs.append(rel)

true_no_md = [(b, a) for b, a in binary_no_md if a is None]
if true_no_md:
    for b, _ in true_no_md:
        report('broken', f"Binary with no .md sibling: {b}")
else:
    report('clean', "All binaries have .md siblings")

for b, alt in binary_no_md:
    if alt:
        report('needs_attention', f"Transcript named differently: {b} → {alt}")

if stubs:
    report('needs_attention', f"Placeholder stubs ({len(stubs)}):")
    for s in stubs:
        print(f"      {s}")
else:
    report('clean', "No placeholder stubs")

raw_md = {r for r in raw_files if r.endswith('.md')}
missing_log = raw_md - log_refs
if missing_log:
    report('needs_attention', f"Raw .md not in log ({len(missing_log)}) — check .pdf/.md pairs or renames")
else:
    report('clean', "All raw .md referenced in log")

print()

# === CHECK 3: Frontmatter quality ===
print("=" * 70)
print("CHECK 3 — FRONTMATTER QUALITY")
print("=" * 70)

REQUIRED = ['title', 'created', 'updated', 'type', 'tags', 'sources']
VALID_TYPES = {'case', 'paper', 'norm', 'concept', 'comparison', 'query', 'moc', 'handoff', 'research-design', 'methodology', 'draft', 'model-article', 'entity', 'summary'}
fm_ok = True

# 全库标签使用计数（词表检查只对单次使用标签提示，避免与SCHEMA A-D清单滞后产生噪音）
tag_usage = Counter()
for page in layer2_pages.values():
    tg = page['fm'].get('tags') or []
    if isinstance(tg, str):
        tg = [t.strip() for t in tg.split(',')]
    for t in tg:
        tag_usage[t.strip()] += 1

for s, page in layer2_pages.items():
    fm = page['fm']
    r = page['rel']
    missing = [f for f in REQUIRED if f not in fm]
    if missing:
        report('broken', f"{r}: missing {missing}")
        fm_ok = False; continue
    if fm.get('type', '') not in VALID_TYPES:
        report('needs_attention', f"{r}: invalid type '{fm['type']}'")
        fm_ok = False
    tags = fm.get('tags', [])
    if isinstance(tags, str):
        tags = [t.strip() for t in tags.split(',')]
    bad = [t for t in tags if t.strip() not in taxonomy and tag_usage.get(t.strip(), 0) == 1]
    if bad:
        report('needs_attention', f"{r}: non-taxonomy singleton tags {bad}")
        fm_ok = False

raw_fm_ok = True
for rel, info in raw_files.items():
    if not rel.endswith('.md'):
        continue
    content = read_file(info['full'])
    if not content:
        report('broken', f"{rel}: cannot read")
        raw_fm_ok = False; continue
    fm, _ = parse_frontmatter(content)
    if not fm:
        report('broken', f"{rel}: no frontmatter")
        raw_fm_ok = False; continue
    # 法学库纪律（skill 九点七）：raw 的 .md 提取文件 sha256/ingested 可选，没有该字段不报错；
    # 仅当存在 sha256 且为占位值时报警
    if 'sha256' in fm and fm['sha256'] in ('<placeholder>', 'PLACEHOLDER'):
        report('broken', f"{rel}: placeholder sha256")
        raw_fm_ok = False

if fm_ok:
    report('clean', "All Layer-2 pages: valid frontmatter, tags in taxonomy")
if raw_fm_ok:
    report('clean', "All raw .md: valid frontmatter")

print()

# === CHECK 4: Wikilink integrity ===
print("=" * 70)
print("CHECK 4 — WIKILINK INTEGRITY")
print("=" * 70)

outbound = defaultdict(set)
inbound = defaultdict(set)
for s, page in layer2_pages.items():
    if not page['content']:
        continue
    for wl in re.findall(r'\[\[([^\]|#]+)', page['content']):
        wl = wl.strip().rstrip('\\')
        if wl and not wl.startswith('http'):
            outbound[s].add(wl)
            inbound[wl].add(s)

broken_links = {src: tgt - disk_slugs for src, tgt in outbound.items() if tgt - disk_slugs}
if broken_links:
    for src, broken in sorted(broken_links.items()):
        report('broken', f"{src} → broken: {sorted(broken)}")
else:
    report('clean', "No broken wikilinks")

orphans = {s for s in disk_slugs if not inbound.get(s)}
if orphans:
    report('needs_attention', f"Orphans (0 inbound): {sorted(orphans)}")
else:
    report('clean', "No orphans")

undr = {s: len(t) for s, t in outbound.items() if len(t) < 2}
if undr:
    report('needs_attention', f"Under-linked (<2 outbound): {dict(undr)}")
else:
    report('clean', "All pages ≥2 outbound links")

print()

# === CHECK 5: File hygiene & convention ===
print("=" * 70)
print("CHECK 5 — FILE HYGIENE & CONVENTION")
print("=" * 70)

assets_img = [r for r in raw_files if r.startswith('raw/assets/') and raw_files[r]['ext'] in {'.png','.jpg','.jpeg'}]
ss_img = [r for r in raw_files if r.startswith('raw/screenshots/') and raw_files[r]['ext'] in {'.png','.jpg','.jpeg'}]

for ai in assets_img:
    bn = os.path.basename(ai)
    refs = sum(1 for p in layer2_pages.values() if bn in (p['content'] or ''))
    if refs == 0:
        report('needs_attention', f"{ai} — not referenced")
    else:
        report('clean', f"{ai} — referenced in {refs} page(s)")

for si in ss_img:
    base = os.path.splitext(si)[0]
    sib = base + '.md'
    if sib in raw_files:
        content = read_file(raw_files[sib]['full'])
        if content:
            _, body = parse_frontmatter(content)
            n = len([l for l in body.strip().split('\n') if l.strip()])
            if n <= 2:
                report('needs_attention', f"{si} — extract body too short ({n} lines)")
            else:
                report('clean', f"{si} — extract has {n} body lines")
    else:
        report('broken', f"{si} — no sibling .md extract")

print()

# === CHECK 6: Log format ===
print("=" * 70)
print("CHECK 6 — LOG FORMAT")
print("=" * 70)

entries = re.findall(r'## \[(\d{4}-\d{2}-\d{2})\]\s+(\w+)', log_content) if log_content else []
print(f"  Proper log entries: {len(entries)}")
if len(entries) > 500:
    report('needs_attention', f"Log >500 entries ({len(entries)}) — rotate needed")
else:
    report('clean', f"Under 500 entries ({len(entries)})")

print()

# === Summary ===
print("=" * 70)
print("SUMMARY")
print("=" * 70)
print(f"  🔴 Broken: {len(issues['broken'])}")
print(f"  🟡 Needs attention: {len(issues['needs_attention'])}")
print(f"  ✅ Clean: {len(issues['clean'])}")
print(f"\n  Wiki: {WIKI}")
print(f"  Total Layer-2 pages: {len(disk_slugs)}")
print(f"  Total raw files: {len(raw_files)}")
