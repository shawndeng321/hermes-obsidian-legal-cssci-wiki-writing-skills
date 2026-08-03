# Paper↔Case Linking Pilot (2026-08-02)

Session-specific detail behind the "Corpus-overlap reality check" section of SKILL.md.

## Pilot findings

Piloted linking on 郑晓珊 (11 cited cases) + 杜强强 (10 cited cases) + spot-checked 李超/梁琼芳/黄辉:

| Paper | Cited cases | In 121-library |
|---|---|---|
| 郑晓珊 | 11 (3 CN + 8 foreign) | 0 (李雍/孟祥敏/陈建华 all absent) |
| 杜强强 | 10 (陈卫群/左光辉/潘儒虔…) | 0 |
| 李超 | 6 | 1 (王明德=案例11, already linked) |
| 梁琼芳 | 10 | 1 (何文良=案例1, already linked) |
| 黄辉 | 4 | 1 (孙立兴=案例3, already linked) |

Vault-wide authoritative-ID scan of all 25 papers found only 5 authoritative references:
- 侯玲玲: 指导案例40号 → 案例3 孙立兴 (already linked ✅)
- 张相军: 检例205号 → 底稿 page (was MISLINKED to 案例31)
- 梁琼芳/王东伟: 公报案例 (generic, no specific case)
- 黄辉: 指导案例91号 → 沙明保案 (房屋强拆案, NOT a 工伤 case — correctly unlinked)

## Wrong existing links found and fixed

张相军篇 had 2 wrong links:
1. `[[案例31-…李某案|刘自荣工伤认定纠纷抗诉案]]` — WRONG. 刘自荣案 has its own page: 案例64-2013-刘自荣诉米泉市劳动人事社会保障局工伤认定案 (最高法2014年八起典型案例之八, (2011)行提字第15号). Fixed.
2. `[[案例31-…李某案|检例第205号]]` — WRONG. 检例205号 is the 底稿 anchor page. Fixed to `[[检例205号案例分析-举证责任分配的司法偏差与检察纠正|检例第205号]]`.

Root cause of the original mislink: an earlier loose-keyword matcher paired "刘自荣" against 案例31 (李某案) — likely a substring/confusion error. Lesson: existing links are NOT trustworthy; re-verify each with 当事人+案号+案情 before adding new ones.

## Matching strategy that works

1. Scan papers for `指导案例N号` / `检例N号` / 公报案例 identifiers → match against library (these are the curated cases the library actually holds).
2. Case-number matching across corpora: ~0 hits (different case sets + format drift 第0034号 vs 第34号). Normalize before matching, but don't rely on it.
3. 当事人+法院+年份 triple-match for the rest — expect <10% success; leave the rest as plain text and report as expected.
4. Bare grep for a number (e.g. "91号") false-positives on unrelated pages — verify the ID against actual case content.

## Status at session end

User approved the plan: ① audit all existing paper→case links + fix errors ② add reverse links from case pages (案例页"相关论文") ③ paper tagging by 6 research themes (举证责任与司法审查 / 认定要件解释 / 排除规则与立法构想 / 新就业形态 / 程序问题 / 检察监督). Execution deferred to next session — user said "检修先等一下吧".

## 用户纠正后的主题链接工作流（2026-08-02 后半段，取代引用匹配为主逻辑）

用户纠正："案例和论文的链接并不在于论文里面和我放进来的案例一一对应 而是这些公报案例经典案例的主旨或者说一些要以能不能和论文里面的主要观点去对应"。

**新逻辑**：论文页新增 `## 与案例的关联` 章节（在 `## 与其他论文的关联` **之前**），按"核心论点 ↔ 裁判要旨"建立印证/支撑/反衬关系。不再是引用案例逐条匹配。

### 验收格式（侯玲玲篇试点，用户确认OK）

```markdown
## 与案例的关联

> 按"观点↔案例主旨"对应建立（2026-08试点）：论文核心论点与库内案例裁判要旨的印证关系，非引用关系。

1. **观点1（司法与行政对过失因素的分歧）** ↔ [[案例54-2024-王某诉辽宁省锦州市人力资源和社会保障局不予认定工伤决定案]]——交通管理部门无法认定事故责任时，社保部门须围绕"职工是否存在过错及过错大小"调查核实；而法院认为应结合证据审查社保部门的过错认定。**正是"行政部门以劳动者过错影响因果关系、司法部门以第16条限缩排除"分歧的实证样本**。
```

每条必须写明**要旨如何印证观点**（60-150字），不能只有链接。

### 试点映射示例（侯玲玲4观点→5案例）

- 观点1（司法/行政过失分歧）→ 案例54锦州（责任不明→过错调查）
- 观点2（上下班途中非本人主要责任=过错排除）→ 案例27欧帛 + 案例19王志国
- 观点4（过错纳入因果而非独立排除）→ 案例47百某物流（"故意或严重过失"=过错改变行为性质的司法表达）+ 案例3孙立兴指导40号（"过失不能排除关联"）
- 观点4补充（因果关系判断）→ 案例114（工作争执暴力伤害因果）

### 批量执行（24篇，3×delegate_task并行）

1. 建索引 `/tmp/case_yaozhi_index.json`：stem→yaozhi前400字（先验证121/121有要旨）。
2. 子代理指令必须含：索引路径、试点页路径（侯玲玲篇作格式参照）、插入位置、完整stem含年份链接（`[[案例N-YYYY-标题]]`）、不得改其他章节、无对应时如实写"与个案要旨直接对应较少"（制度构建/立法构想类论文）。
3. 完成后主代理统一做案例页反向"与论文的关联"小节（先查是否已存在避免重复）。
4. 验收：全库死链0（\|和|双分隔符解析）、每篇有"与案例的关联"。

### 附加教训

- 试点选篇看重合度：郑晓珊/杜强强全部不在库内——选已有权威案例链接的篇目（侯玲玲/李超/梁琼芳）试点更有效。
- 宽泛关键词匹配严重误报（10条不相干案例全误匹配到案例11）——必须精读要旨文本确认，不能只靠关键词计数。
- 引用文献6类主题标签已全量打上（25篇），SCHEMA标签规范已同步。

