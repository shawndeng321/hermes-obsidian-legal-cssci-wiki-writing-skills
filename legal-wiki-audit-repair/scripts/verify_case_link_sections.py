#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""验收论文页 '## 与案例的关联' 章节（PAPER-CASE-LINK模式）。

用法:
    python3 verify_case_link_sections.py <wiki根目录> <论文文件1.md> [论文文件2.md ...]

检查项:
  1. 章节 '## 与案例的关联' 位于 '## 与其他论文的关联' 之前；
  2. 新章节内所有 [[案例...]] 链接命中 entities/案例 下（递归）的真实文件stem（死链0）；
  3. 每条条目理由（'——'之后）60-150字；
  4. 章节开头有一行以 "> " 开头、说明“观点↔案例主旨”对应依据的说明行。

退出码: 0 = 全部通过, 1 = 有失败。
注意: 只检查'与案例的关联'章节本身；论文页其他章节的既有死链（如匿名化别名链接）不在本脚本范围。
"""
import re
import sys
from pathlib import Path

if len(sys.argv) < 3:
    print(__doc__)
    sys.exit(2)

base = Path(sys.argv[1])
ref_dir = base / 'entities/引用文献'
case_dir = base / 'entities/案例'
case_stems = {p.stem for p in case_dir.rglob('*.md')} if case_dir.exists() else set()
NOTE_RE = re.compile(r'^> .*主旨', re.M)

ok = True
for fn in sys.argv[2:]:
    path = ref_dir / fn
    text = path.read_text(encoding='utf-8')
    if '## 与案例的关联' not in text:
        print(fn, '| FAIL: 缺少 ## 与案例的关联 章节')
        ok = False
        continue
    if text.count('## 与其他论文的关联') != 1:
        print(fn, '| FAIL: "## 与其他论文的关联" anchor 数量 != 1')
        ok = False
        continue
    sec = text.split('## 与案例的关联', 1)[1].split('## 与其他论文的关联', 1)[0]
    links = re.findall(r'\[\[([^\]]+)\]\]', sec)
    dead = [l for l in links if l not in case_stems]
    bad_len = []
    for line in sec.split('\n'):
        if re.match(r'^\d+\. ', line):
            reason = line.split('——', 1)[1] if '——' in line else line
            n = len(reason)
            if n < 60 or n > 150:
                bad_len.append((line[:20], n))
    pos_ok = text.index('## 与案例的关联') < text.index('## 与其他论文的关联')
    note_ok = bool(NOTE_RE.search(sec))
    print(fn, '| 顺序OK:', pos_ok, '| 新章节链接数:', len(links),
          '| 死链:', dead if dead else 0, '| 理由字数超标:', bad_len if bad_len else '无',
          '| 说明行:', note_ok)
    ok = ok and pos_ok and not dead and not bad_len and note_ok

sys.exit(0 if ok else 1)
