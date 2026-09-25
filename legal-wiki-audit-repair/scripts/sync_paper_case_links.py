#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CASE-PAPER-SYNC: 案例页'## 与论文的关联' → 论文页'## 与案例的关联' 批量同步。

用法：
1. 改 WIKI 与 TARGETS（论文完整stem（不带.md） → 论文文件名），只列本批要同步的论文；
2. `python3 sync_paper_case_links.py /path/to/wiki --dry-run` 先试跑看判缺/字数报告；
3. 确认无误后正式跑（自动备份到 `<wiki>/.maintenance/.../before_batchN/`，只追加不修改既有条目）。

也可用 `WIKI_PATH`/`DRY_RUN=1` 兼容旧调用；脚本不会再使用作者机器上的固定绝对路径。

规则：
- 观点文本取自案例页条目 '本文观点X（…）'，理由取自 '——' 后（60-150 CJK字）；
- 编号接续论文页章节现有最大编号+1；
- 去重按案例完整stem（论文页章节内全部 [[…]] 链接，一条论文页条目可含多案例）；
- 同一作者有多篇论文时必须整名匹配，严禁用作者名前缀 startswith。
"""
import argparse
import os
import re
import shutil
import tempfile

WIKI = CASE_DIR = PAPER_DIR = TASK_DIR = BACKUP_DIR = None

# 论文完整stem（案例页条目中出现的名字，不带.md）→ 论文文件名
TARGETS = {
    # 每批在此列出要同步的论文，例如：
    # "作者-论文题名": "作者-论文题名.md",
}


def extract_case_entries(filepath):
    """返回 (paper_key, entry_line) 列表，来自 '## 与论文的关联' 章节。"""
    with open(filepath, encoding="utf-8") as f:
        text = f.read()
    m = re.search(r"^## 与论文的关联\s*\n(.*?)(?=^## )", text, re.M | re.S)
    if not m:
        return []
    results = []
    for line in m.group(1).splitlines():
        line = line.strip()
        if not line.startswith("- **"):
            continue
        for key in TARGETS:
            if line.startswith(f"- **{key}**：") or line.startswith(f"- **{key}**:"):
                results.append((key, line))
                break
    return results


def parse_view_and_reason(entry):
    """从案例页条目提取 (观点标签, 理由)。lookahead (?=以本案) 处理嵌套括号。"""
    m = re.search(r"本文观点\s*(\d+)?\s*（(.*?)）(?=以本案)", entry)
    if m:
        num, brief = m.group(1), m.group(2)
        view = f"观点{num}（{brief}）" if num else "本文观点"
    else:
        view = "本文观点"
    mr = re.search(r"以本案(?:要旨)?为支撑——(.*)$", entry, re.S)
    if mr:
        reason = mr.group(1).strip()
    else:
        idx = entry.find("——")
        reason = entry[idx + 2:].strip() if idx != -1 else ""
    return view, reason


def load_paper_state(path):
    """返回 (既有案例stem集合, 最大编号) 来自 '## 与案例的关联'。"""
    with open(path, encoding="utf-8") as f:
        text = f.read()
    m = re.search(r"^## 与案例的关联\s*\n(.*?)(?=^## )", text, re.M | re.S)
    if not m:
        return set(), 0
    section = m.group(1)
    stems = set(re.findall(r"\[\[([^\]]+)\]\]", section))
    nums = [int(n) for n in re.findall(r"^(\d+)\.\s", section, re.M)]
    return stems, (max(nums) if nums else 0)


def append_entries(path, new_entries):
    """把新条目追加到 '## 与案例的关联' 章节末尾（最后非空行之后，保留空行结构）。"""
    with open(path, encoding="utf-8") as f:
        text = f.read()
    m = re.search(r"(^## 与案例的关联\s*\n)(.*?)(?=^## )", text, re.M | re.S)
    if not m:
        raise RuntimeError(f"section not found in {path}")
    section = m.group(2)
    lines = section.split("\n")
    last_idx = max(i for i, l in enumerate(lines) if l.strip())
    new_lines = lines[:last_idx + 1] + new_entries + lines[last_idx + 1:]
    new_section = "\n".join(new_lines)
    new_text = text[:m.start()] + m.group(1) + new_section + text[m.end():]
    fd, tmp_name = tempfile.mkstemp(prefix=".paper-case-sync.", suffix=".tmp", dir=os.path.dirname(path))
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as f:
            f.write(new_text)
        os.replace(tmp_name, path)
    except Exception:
        try:
            os.unlink(tmp_name)
        except FileNotFoundError:
            pass
        raise


def cjk_len(s):
    return len(re.findall(r"[\u4e00-\u9fff\u3000-\u303f\uff00-\uffef]", s))


def adjust_reason(paper_key, case_stem, reason):
    """轻微调整理由使以论文视角表述。默认保持原文（案例页理由已含论文视角表述）；
    个别案例需手工微调时在此加规则。"""
    r = reason
    # 例：理由中泛指的“这一原则”需点明系论文所述
    # if case_stem.startswith("案例60-") and "这一原则" in r and "论文" not in r:
    #     r = r.replace("这一原则", "论文所述的这一原则")
    return r


def configure_paths(wiki, backup_dir=None):
    """Configure all paths from the caller's vault; never use a host path."""
    global WIKI, CASE_DIR, PAPER_DIR, TASK_DIR, BACKUP_DIR
    WIKI = os.path.abspath(os.path.expanduser(wiki))
    CASE_DIR = os.path.join(WIKI, "entities", "案例")
    PAPER_DIR = os.path.join(WIKI, "entities", "引用文献")
    if not os.path.isdir(CASE_DIR) or not os.path.isdir(PAPER_DIR):
        raise ValueError("wiki must contain entities/案例 and entities/引用文献")
    TASK_DIR = os.path.join(WIKI, ".maintenance", "paper-case-link")
    BACKUP_DIR = os.path.abspath(os.path.expanduser(backup_dir)) if backup_dir else os.path.join(TASK_DIR, "before_batchN")
    if os.path.commonpath([BACKUP_DIR, PAPER_DIR]) == PAPER_DIR:
        raise ValueError("backup directory must not be inside entities/引用文献")


def safe_paper_path(filename):
    path = os.path.abspath(os.path.join(PAPER_DIR, filename))
    if os.path.commonpath([path, PAPER_DIR]) != PAPER_DIR:
        raise ValueError(f"target paper escapes entities/引用文献: {filename}")
    return path


def env_truthy(name):
    return os.environ.get(name, "").lower() in {"1", "true", "yes", "on"}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("wiki", nargs="?", default=os.environ.get("WIKI_PATH"),
                        help="wiki root (or set WIKI_PATH)")
    parser.add_argument("--dry-run", action="store_true", help="report missing links without writing")
    parser.add_argument("--backup-dir", help="backup directory; defaults to <wiki>/.maintenance/.../before_batchN")
    args = parser.parse_args(argv)
    if not args.wiki:
        parser.error("wiki root is required (pass it as an argument or set WIKI_PATH)")
    try:
        configure_paths(args.wiki, args.backup_dir)
    except ValueError as exc:
        parser.error(str(exc))
    dry_run = args.dry_run or env_truthy("DRY_RUN")

    pending = []
    by_paper = {k: [] for k in TARGETS}
    for root, _, files in os.walk(CASE_DIR):
        for fn in sorted(files):
            if not fn.endswith(".md"):
                continue
            stem = fn[:-3]
            for key, line in extract_case_entries(os.path.join(root, fn)):
                by_paper[key].append((stem, line))

    total = 0
    for key, fn in TARGETS.items():
        ppath = safe_paper_path(fn)
        if not os.path.isfile(ppath):
            raise FileNotFoundError(f"target paper does not exist: {ppath}")
        existing, max_num = load_paper_state(ppath)
        missing = [(stem, line) for stem, line in by_paper[key] if stem not in existing]
        print(f"\n=== {key}  现有编号至 {max_num}，案例页条目 {len(by_paper[key])}，缺失 {len(missing)}")
        if not missing:
            continue
        if dry_run:
            for stem, line in missing:
                view, reason = parse_view_and_reason(line)
                print(f"  [待加] {stem} | {view} | {cjk_len(reason)}字")
            continue
        pending.append((key, fn, ppath, missing, max_num))

    if not pending:
        print("\n总计追加: 0 条")
        return 0

    # Preflight backups for the whole batch before changing any paper page.
    os.makedirs(BACKUP_DIR, exist_ok=True)
    backup_pairs = []
    for _, fn, ppath, _, _ in pending:
        destination = os.path.join(BACKUP_DIR, fn)
        if os.path.exists(destination):
            raise RuntimeError(f"backup already exists; refusing to clobber it: {destination}")
        backup_pairs.append((ppath, destination))
    for ppath, destination in backup_pairs:
        os.makedirs(os.path.dirname(destination), exist_ok=True)
        shutil.copy2(ppath, destination)

    for key, fn, ppath, missing, max_num in pending:
        new_entries, n = [], max_num
        for stem, line in missing:
            n += 1
            view, reason = parse_view_and_reason(line)
            reason = adjust_reason(key, stem, reason)
            new_entries.append(f"{n}. **{view}** ↔ [[{stem}]]——{reason}")
            total += 1
            print(f"  + {stem} | {view} | {cjk_len(reason)}字")
        append_entries(ppath, new_entries)
        print(f"  → 已追加 {len(new_entries)} 条（编号 {max_num + 1}-{n}），备份: {BACKUP_DIR}")
    print(f"\n总计追加: {total} 条")


if __name__ == "__main__":
    main()
