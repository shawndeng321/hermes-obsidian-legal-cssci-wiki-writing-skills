#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""NORM-REFERENCE模式：批量给概念/比较页插入'## 规范依据'小节。

用法：
1. 改下方 WIKI（wiki根目录）与 PLAN（键=待改页面相对wiki根的路径，如 'concepts/xxx.md'；
   值=[(法规范页文件名-无.md, 说明30-80字), ...]，每页2-4条）；
2. DRY_RUN=1 python3 insert_norm_sections.py   # 试跑：只校验不写
3. python3 insert_norm_sections.py             # 正式执行

规则（2026-08批次2实测固化）：
- 插在 '## 与比较页的关联' 之前；该anchor不存在时回退 '## 相关概念'；
- 格式：## 规范依据\\n\\n- [[法规范页完整文件名]]——说明（30-80字）\\n；
- 说明30-80字（CJK计数）；链接必须真实存在于 entities/法规范/ 下（os.walk）；
- 页面已有 '## 规范依据' 则跳过（幂等）；任务简称≠实际文件名时以实际文件为准。
"""
import os, sys

WIKI = "/Users/shawndeng/Desktop/法学wiki/工伤认定群案研究Wiki"
NORM_ROOT = os.path.join(WIKI, "entities", "法规范")

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


def main():
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

    for fn, items in PLAN.items():
        path = os.path.join(WIKI, fn)
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
        if os.environ.get("DRY_RUN"):
            print(f"[DRY-RUN 通过] {fn}: {len(items)}条")
            continue
        with open(path, "w", encoding="utf-8") as f:
            f.write(new_text)
        print(f"[已插入] {fn}: {len(items)}条")
    print("DONE")


if __name__ == "__main__":
    main()
