#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""NORM-REFERENCE模式：批量给概念/比较页插入'## 规范依据'小节。

用法：
1. 改下方 WIKI（wiki根目录）与 PLAN（键=待改页面相对wiki根的路径，如 'concepts/xxx.md'；
   值=[(法规范页文件名-无.md, 说明30-80字), ...]，每页2-4条）；
2. `python3 insert_norm_sections.py /path/to/wiki --dry-run`   # 试跑：只校验不写
3. `python3 insert_norm_sections.py /path/to/wiki`             # 正式执行

也可用 `WIKI_PATH`/`DRY_RUN=1` 兼容旧调用；写入前会备份到 wiki 内的
`.maintenance/norm-reference-2026-08/before/`，且不会覆盖已有备份。

规则（2026-08批次2实测固化）：
- 插在 '## 与比较页的关联' 之前；该anchor不存在时回退 '## 相关概念'；
- 格式：## 规范依据\\n\\n- [[法规范页完整文件名]]——说明（30-80字）\\n；
- 说明30-80字（CJK计数）；链接必须真实存在于 entities/法规范/ 下（os.walk）；
- 页面已有 '## 规范依据' 则跳过（幂等）；任务简称≠实际文件名时以实际文件为准。
"""
import argparse
import os
import shutil
import sys
import tempfile

WIKI = NORM_ROOT = BACKUP_DIR = None

PLAN = {
    # 示例（batch2实测）：
    # "concepts/上下班途中合理时间的认定边界.md": [
    #     ("工伤保险条例（2010修订）", "第十四条第六项确立“上下班途中”与“非本人主要责任”认定要件，系“合理时间”问题的规范起点。"),
    #     ("司法解释-审理工伤保险行政案件规定（法释2014-9号）", "第六条以“合理时间”“合理路线”界定“上下班途中”的四种情形，为“合理时间”解释提供权威基准。"),
    # ],
}

ANCHOR_1 = "## 与比较页的关联"
ANCHOR_2 = "## 相关概念"
NEW_SECTION = "## 规范依据"


def link_exists(link):
    for dirpath, dirnames, filenames in os.walk(NORM_ROOT):
        if link + ".md" in filenames:
            return True
    return False


def configure_paths(wiki, backup_dir=None):
    global WIKI, NORM_ROOT, BACKUP_DIR
    WIKI = os.path.abspath(os.path.expanduser(wiki))
    NORM_ROOT = os.path.join(WIKI, "entities", "法规范")
    if not os.path.isdir(WIKI) or not os.path.isdir(NORM_ROOT):
        raise ValueError("wiki must contain entities/法规范")
    BACKUP_DIR = os.path.abspath(os.path.expanduser(backup_dir)) if backup_dir else os.path.join(
        WIKI, ".maintenance", "norm-reference-2026-08", "before"
    )
    if os.path.commonpath([BACKUP_DIR, NORM_ROOT]) == NORM_ROOT:
        raise ValueError("backup directory must not be inside entities/法规范")


def safe_page_path(filename):
    path = os.path.abspath(os.path.join(WIKI, filename))
    if os.path.commonpath([path, WIKI]) != WIKI:
        raise ValueError(f"planned page escapes wiki root: {filename}")
    return path


def atomic_write(path, text):
    fd, tmp_name = tempfile.mkstemp(prefix=".norm-reference.", suffix=".tmp", dir=os.path.dirname(path))
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as f:
            f.write(text)
        os.replace(tmp_name, path)
    except Exception:
        try:
            os.unlink(tmp_name)
        except FileNotFoundError:
            pass
        raise


def env_truthy(name):
    return os.environ.get(name, "").lower() in {"1", "true", "yes", "on"}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("wiki", nargs="?", default=os.environ.get("WIKI_PATH"),
                        help="wiki root (or set WIKI_PATH)")
    parser.add_argument("--dry-run", action="store_true", help="validate and preview without writing")
    parser.add_argument("--backup-dir", help="backup directory; defaults to <wiki>/.maintenance/.../before")
    args = parser.parse_args(argv)
    if not args.wiki:
        parser.error("wiki root is required (pass it as an argument or set WIKI_PATH)")
    try:
        configure_paths(args.wiki, args.backup_dir)
    except ValueError as exc:
        parser.error(str(exc))
    dry_run = args.dry_run or env_truthy("DRY_RUN")

    if not PLAN:
        sys.exit("PLAN 为空：先在脚本顶部填写待插入页面与链接清单")
    ok = True
    for fn, items in PLAN.items():
        if not (2 <= len(items) <= 4):
            print(f"[条数超限] {fn}: {len(items)}条（需2-4条）")
            ok = False
        for link, desc in items:
            n = len(desc)
            if not (30 <= n <= 80):
                print(f"[字数超限] {fn} / {link}: {n}字（需30-80）")
                ok = False
            if not link_exists(link):
                print(f"[链接缺失] {fn} -> {link} 在 {NORM_ROOT} 下未找到（核对实际文件名）")
                ok = False
    if not ok:
        sys.exit(1)

    changes = []
    for fn, items in PLAN.items():
        path = safe_page_path(fn)
        with open(path, encoding="utf-8") as f:
            text = f.read()
        if NEW_SECTION in text:
            print(f"[跳过-已存在] {fn}")
            continue
        anchor = ANCHOR_1 if ANCHOR_1 in text else ANCHOR_2
        cnt = text.count(anchor)
        if cnt != 1:
            print(f"[错误] {fn} 中 '{anchor}' 出现 {cnt} 次")
            sys.exit(1)
        block = NEW_SECTION + "\n\n" + "".join(f"- [[{link}]]——{desc}\n" for link, desc in items) + "\n"
        new_text = text.replace(anchor, block + anchor, 1)
        if dry_run:
            print(f"[DRY-RUN 通过] {fn}: {len(items)}条")
            continue
        changes.append((fn, path, new_text))

    if dry_run or not changes:
        print("DONE")
        return 0

    # Back up every page before the first write and never overwrite an old backup.
    os.makedirs(BACKUP_DIR, exist_ok=True)
    backup_pairs = []
    for fn, path, _ in changes:
        destination = os.path.join(BACKUP_DIR, fn)
        if os.path.exists(destination):
            raise RuntimeError(f"backup already exists; refusing to clobber it: {destination}")
        backup_pairs.append((path, destination))
    for path, destination in backup_pairs:
        os.makedirs(os.path.dirname(destination), exist_ok=True)
        shutil.copy2(path, destination)
    for fn, path, new_text in changes:
        atomic_write(path, new_text)
        print(f"[已插入] {fn}: {len(PLAN[fn])}条")
    print("DONE")
    return 0


if __name__ == "__main__":
    main()
