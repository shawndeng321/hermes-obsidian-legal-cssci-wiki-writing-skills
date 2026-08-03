#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""论文页"与案例的关联"缺漏扫描器（案例页→论文页 镜像同步用，2026-08第2批实测）。

扫描 entities/案例 三个子目录所有案例页的 '## 与论文的关联' 章节，
提取指向目标论文的条目（- **论文名**：本文观点X（…）以本案[要旨]为支撑——理由），
与论文页 '## 与案例的关联' 章节已有 [[案例stem]] 比对，报告缺漏。

用法：
  python3 scan_missing_paper_case_links.py <wiki根目录> <论文stem1> [论文stem2 …]
论文stem = entities/引用文献 下文件名去 .md（如 葛翔-规则还是惯例特殊类型工伤的行政认定与司法审查）。

输出：每篇论文的 案例页条目数 / 论文页已有链接数与最大编号 / 缺漏清单（含条目全文）。

注意：
- 理由需人工微调为论文视角（"论文"→"本文"、补"本案"主语等）再追加，60-150字；
- 追加编号 = 章节现有最大编号+1；追加前按当批指令确定去重范围（章节内 or 整页）；
- 插入到下一个 '## ' 标题前时，插入串必须自带尾换行（见 SKILL.md 九-6 换行双坑）。
"""
import os, re, sys, glob

BASE = sys.argv[1]
PAPERS = sys.argv[2:]
CASE_DIR = os.path.join(BASE, "entities", "案例")
PAPER_DIR = os.path.join(BASE, "entities", "引用文献")


def read(p):
    with open(p, encoding="utf-8") as f:
        return f.read()


def section(text, header):
    m = re.search(r"^## %s\s*$" % re.escape(header), text, re.M)
    if not m:
        return None
    start = m.end()
    nxt = re.search(r"^## ", text[start:], re.M)
    return text[start:start + nxt.start()] if nxt else text[start:]


case_files = sorted(glob.glob(os.path.join(CASE_DIR, "*", "*.md")))
entries = {p: [] for p in PAPERS}
for cf in case_files:
    stem = os.path.splitext(os.path.basename(cf))[0]
    sec = section(read(cf), "与论文的关联")
    if not sec:
        continue
    for line in sec.splitlines():
        line = line.strip()
        for p in PAPERS:
            m = re.match(r"^-\s*\*\*" + re.escape(p) + r"\*\*[:：]\s*(.+)$", line)
            if m:
                entries[p].append((stem, m.group(1).strip()))
                break

for p in PAPERS:
    print("=" * 20, p, f"{len(entries[p])} 条案例页条目")
    pf = os.path.join(PAPER_DIR, p + ".md")
    if not os.path.exists(pf):
        print("  论文页不存在！")
        continue
    sec = section(read(pf), "与案例的关联")
    if sec is None:
        print("  论文页无'## 与案例的关联'章节，全部待建")
        continue
    stems = {re.sub(r"\s+", "", l.split("|")[0].strip())
             for l in re.findall(r"\[\[([^\]]+)\]\]", sec)}
    nums = [int(m.group(1)) for m in re.finditer(r"^(\d+)\.\s+\*\*", sec, re.M)]
    print(f"  论文页已有 {len(stems)} 个链接，最大编号 {max(nums) if nums else 0}")
    missing = [(s, e) for s, e in entries[p] if re.sub(r"\s+", "", s) not in stems]
    print(f"  缺漏 {len(missing)} 条：")
    for s, e in missing:
        print(f"    - {s}")
        print(f"      条目: {e}")
