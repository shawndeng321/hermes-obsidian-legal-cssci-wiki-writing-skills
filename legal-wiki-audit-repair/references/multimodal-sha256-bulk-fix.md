# sha256 批量修复（raw 源文件哈希）— 多模态扩展

> **来源**：multimodal-wiki v1.0.0（kigner/multimodal-wiki）`references/sha256-bulk-fix.md`，2026-08 融合。
> 用法：检修发现大量 sha256 漂移/占位哈希时，批量重算一次到位。
> 注意：raw 应不可变——批量漂移优先怀疑系统性原因（占位哈希、行尾符、工具编码），修复前先归因。

# Sha256 Bulk Fix for Raw Sources

When lint reveals many sha256 mismatches (missing, placeholder, or drifted), use this
pattern through the current host's code-execution facility. It walks every `.md` file
in `raw/`, computes the body sha256 (everything after the closing `---`), and either
adds or updates the `sha256:` frontmatter field. The default mode is preview-only;
writing requires an explicit backup directory.

## Script

```python
import os, re, hashlib, shutil

WIKI = os.path.abspath(os.environ["WIKI_PATH"])
raw_dir = os.path.join(WIKI, 'raw')
DRY_RUN = os.environ.get("DRY_RUN", "1") != "0"
BACKUP_DIR = os.environ.get("BACKUP_DIR")

if not os.path.isdir(raw_dir):
    raise SystemExit(f"raw directory not found: {raw_dir}")
if not DRY_RUN and not BACKUP_DIR:
    raise SystemExit("BACKUP_DIR is required when DRY_RUN=0")
if BACKUP_DIR:
    BACKUP_DIR = os.path.abspath(BACKUP_DIR)

def write_with_backup(path, new_content):
    if DRY_RUN:
        return
    relative = os.path.relpath(path, raw_dir)
    backup_path = os.path.join(BACKUP_DIR, relative)
    if os.path.exists(backup_path):
        raise FileExistsError(f"backup already exists: {backup_path}")
    os.makedirs(os.path.dirname(backup_path), exist_ok=True)
    shutil.copy2(path, backup_path)
    with open(path, 'w', encoding='utf-8') as fh:
        fh.write(new_content)

stats = {'added': 0, 'updated': 0, 'skipped': 0}

for root, dirs, files in os.walk(raw_dir):
    for f in files:
        if not f.endswith('.md'):
            continue
        path = os.path.join(root, f)
        with open(path, 'r', encoding='utf-8') as fh:
            original = fh.read()

        # Must have frontmatter
        if not original.startswith('---'):
            stats['skipped'] += 1
            continue

        end = original.find('---', 3)
        if end == -1:
            stats['skipped'] += 1
            continue

        fm = original[3:end]
        body = original[end+3:]  # everything after closing ---

        # Compute current body sha256
        current_sha = hashlib.sha256(body.encode('utf-8')).hexdigest()

        # Check existing sha256
        sha_match = re.search(r'sha256:\s*(\S+)', fm)

        if sha_match:
            stored = sha_match.group(1)
            if stored == current_sha:
                stats['skipped'] += 1
                continue

            # Update sha256 — replace the stored value with current
            new_fm = fm.replace(f'sha256: {stored}', f'sha256: {current_sha}')
            new_content = '---\n' + new_fm + '\n---' + body
            write_with_backup(path, new_content)
            stats['updated'] += 1
        else:
            # No sha256 field — add one after ingested line
            ingested_match = re.search(r'ingested:.*', fm)
            if ingested_match:
                insert_pos = ingested_match.end()
                new_fm = fm[:insert_pos] + '\nsha256: ' + current_sha + fm[insert_pos:]
            else:
                new_fm = fm.rstrip() + '\nsha256: ' + current_sha

            new_content = '---\n' + new_fm + '\n---' + body
            write_with_backup(path, new_content)
            stats['added'] += 1

mode = "DRY-RUN" if DRY_RUN else "WRITE"
print(f"{mode}: {stats['added']} added, {stats['updated']} updated, {stats['skipped']} skipped")
```

先只设置 `WIKI_PATH` 运行，确认预览计数和抽样文件；确认后再设置一个新的 `BACKUP_DIR`，并显式设置 `DRY_RUN=0`。备份目标已有同名文件时脚本会停止，不会覆盖旧备份。

## Verification

After running, verify with a drift re-check:

```python
drifts = 0
for root, dirs, files in os.walk(raw_dir):
    for f in files:
        if not f.endswith('.md'):
            continue
        path = os.path.join(root, f)
        with open(path, 'r', encoding='utf-8') as fh:
            text = fh.read()
        end = text.find('---', 3)
        if end == -1:
            continue
        fm = text[3:end]
        sha = re.search(r'sha256:\s*(\S+)', fm)
        if not sha:
            continue
        body = text[end+3:]
        current = hashlib.sha256(body.encode('utf-8')).hexdigest()
        if current != sha.group(1):
            drifts += 1

print(f"Drifts remaining: {drifts}")  # should be 0
```

## When to Use

- After initial wiki creation where placeholder hashes were used
- After discovering systemic sha256 drift across many files
- As part of the lint workflow when sha256 mismatches exceed ~10 files (bulk-fix is faster than per-file patches)
