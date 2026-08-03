# Session 2026-07-31: Research-Design Upgrade + Controversy Map (研究设计升级 + 学术史争议地图)

Context: user's 写作思路 wiki audited against the merged Hermes skill `chinese-law-paper-writing` v3.0.0 (五问框架). Audit first, proposal first, execution after explicit confirmation (user said "先告诉我要不要完善和怎么完善…然后我来决定").

## Audit findings (report to user, then execute)

1. **Q4 素材清单 stale**: status column contradicted log.md (said 最高法参考 "待摄入" when 53-case ingestion + 最高检 usage had happened 2026-07-30/31). Fix = cross-check `ls raw/cases/` + log.md entries before writing any status.
2. **Missing 样本选取标准**: added 三层样本结构 (权威样本=官方汇编 / 统计样本=编译集 / 补充样本=裁判文书网按需), each with 选取标准/时间范围/用途. 双样本结构 answers the "样本偏斜" reviewer attack.
3. **Missing 资料截止日期 + 五项硬门禁状态表**: 案例数据截止 [待定], 法律规范现行版本 (《工伤保险条例》2010修订版 国务院令586号, 法释〔2014〕9号), 文献核验状态. Gates: 来源真实性✅ 法律有效性✅ 引注完整性✅ 论证充分性⚠️(待121案) 期刊适配✅.
4. **New page: 论点—证据—引注矩阵** (research-design/工伤认定群案论点证据引注矩阵.md): per dimension, rows = 子主张 | 证据类型 | 具体证据 | 支持范围 | 反方材料 | 核验状态 (VERIFIED/待核/缺证据). Statistics stay 待核 until 121案编译集 ingested — NEVER fabricate percentages. 6-item 统计口径清单 must be predefined (年代切片认定率, 改判率定义, 行政机关问题类型分布, 法条引用频率变迁, 撤诉/放弃比例, 裁判理由分化度).

## Controversy-map construction (争议地图)

Built concepts/工伤认定研究学术史争议地图.md (11.3KB) from repaired paper pages.

### Position extraction snippet (run in terminal, not memory)

```python
import re, glob
for f in sorted(glob.glob('entities/引用文献/*.md')):
    text = open(f, encoding='utf-8').read()
    core = re.search(r'## 核心论点(.*?)(?=## |\Z)', text, re.S)
    concl = re.search(r'## (?:主要)?结论(.*?)(?=## |\Z)', text, re.S)
    print('='*20, f.replace('.md',''))
    if core: print('【核心论点】', core.group(1).strip()[:500].replace(chr(10),' '))
    if concl: print('【结论】', concl.group(1).strip()[:300].replace(chr(10),' '))
```

### Page skeleton (per controversy)

争议问题 → 阵营表（立场 | 代表文献 [[wikilinks]] | 核心主张）→ 分歧点 bullets → 实务映射（检例205号 / 葛翔643案仅1.2%改判 / 艾琳141件 / 李超100案80%驳回）→ 未决问题（研究缺口 mapped to dimension）. Plus 延伸集群 (程序与监督, 新就业形态) and a 使用方法 section.

Result: 35 links, 0 dead. Each controversy's 未决问题 row doubles as Q3 理论空白 evidence — three controversies map to the three analysis dimensions.

### Backlink insertion (center-node pages)

After creating the map, inserted `- [[工伤认定研究学术史争议地图]]` into 相关概念 of 6 stable pages (研究设计页 + 5 concept pages) via a python script targeting `## 相关(?:概念|页面)\n(.*?)(?=\n## |\Z)`. Deliberately did NOT touch the 25 paper pages — parallel session was actively repairing entities/引用文献/ (log.md showed 第一批/第二批/第三批 entries appearing mid-session). Deferral recorded in log.md.

## Parallel-session log.md conflict (hit TWICE)

Other sessions append to log.md concurrently. My entries landed mid-file twice because I anchored on a remembered last line. Fix each time: patch out the misplaced block, re-read the true tail, append at the end. Also: after patch, log.md returns a "modified since last read" warning — always re-read the tail before appending.

## Verification numbers

- 矩阵页 23 links / 研究设计页 24 links / 争议地图 35 links / 方法论页 4 links — all 0 dead
- Vault-wide dead links: 2 known false positives (SCHEMA.md `[[wikilinks]]` doc example; log.md historical `[[工伤认定群案研究三层分析框架]]` before rename)
- index.md count 98→100, log.md entries in chronological order
- Methodology concept page synced with skill v3.0.0: added 启动纪律 (3 steps), 五项硬门禁, 任务模式↔五问锚点表, 工作稿/最终稿 marker system ([待核引注-01] etc.)
