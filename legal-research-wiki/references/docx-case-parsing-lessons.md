# DOCX Case Compilation Parsing Lessons (2026-07-30)

Session: Parsing 53 Supreme Court authoritative cases from a single DOCX compilation
into individual Wiki entity pages under the 工伤认定群案研究Wiki.

## Source Structure

The source DOCX (`（最高法库存53个权威案例）工伤认定及相关工伤保险行政诉讼案例简编_按时间顺序.docx`)
organizes 53 cases with:

- **Year headers**: `2003年`, `2005年`, etc. — group cases by effective date
- **Separators**: Long dash lines (`————————————————————————————`, 28 em dashes) between cases
- **Case entries**: Numbered `N. Case Name`, followed by labeled fields

## Critical Parsing Pitfalls

### 1. Separator vs Subtitle Detection

The separator is 28 consecutive `—` characters. Some case titles contain `——` (2 dashes) as a subtitle delimiter (e.g., `吴某发、卢某英诉重庆市北碚区工伤保险管理所给付工伤保险金案——工伤职工冒用他人身份...`).

**DO NOT use `'——' in line` to detect separators** — it matches both separators (28 dashes) and subtitles (2 dashes), causing subtitle-bearing cases to be split mid-title.

**USE `line.count('—') > 5`** — this reliably distinguishes real separators from subtitles.

This single bug caused 10 out of 53 cases to be silently dropped in the first run.

### 2. Duplicate Filenames

When two cases generate the same short name (e.g., "李某" from 2024), the second `write_file` call silently overwrites the first. Use a counter dictionary:

```python
_filename_counter = {}

def make_filename(year, case_name):
    short = extract_short_name(case_name)
    base = f"案例-{year}-{short}"
    if base in _filename_counter:
        _filename_counter[base] += 1
        return f"{base}-{_filename_counter[base]}.md"
    else:
        _filename_counter[base] = 1
        return f"{base}.md"
```

This affected cases 44 and 52 (both "李某" in 2024).

## Field Extraction Regex Patterns

Standard regex patterns for Chinese legal case compilations:

```python
# Date
date_match = re.search(r'裁判/监督日期[：:]\s*(.+?)$', text, re.MULTILINE)

# Source
source_match = re.search(r'来源[：:]\s*(.+?)$', text, re.MULTILINE)

# Case number
cn_match = re.search(r'案号[：:]\s*(.+?)$', text, re.MULTILINE)

# Keywords
kw_match = re.search(r'关键词[：:]\s*(.+?)$', text, re.MULTILINE)

# Facts (to next section header)
facts_match = re.search(r'基本案情（简化）[：:]\s*(.+?)(?=\n裁判结果（简化）)', text, re.DOTALL)

# Result (to next section header)
result_match = re.search(r'裁判结果（简化）[：:]\s*(.+?)(?=\n裁判要旨[：:])', text, re.DOTALL)

# Gist (to next section header)
gist_match = re.search(r'裁判要旨[：:]\s*(.+?)(?=\n裁判依据[：:])', text, re.DOTALL)

# Legal basis (to end of text)
basis_match = re.search(r'裁判依据[：:]\s*(.+?)$', text, re.DOTALL)
```

## Legal Basis Normalization

The source compilation often repeats the same statute in multiple phrasings:
- `《工伤保险条例》第十四条第六项`
- `《工伤保险条例》第十四条第(六)项`
- `《工伤保险条例》第十四条第六项之规定`
- `《工伤保险条例》第十四条第六项的规定`

Basic dedup approach: split by `；`, normalize common law names (ensure `《》` brackets), create a whitespace-stripped key for dedup. Catches ~70% of duplicates.

```python
def normalize_legal_basis(text):
    items = re.split(r'[；;]', text)
    normalized = []
    seen = set()
    for item in items:
        item = item.strip()
        if not item or len(item) < 3: continue
        if item.startswith('一审') or item.startswith('二审'): continue
        # Ensure law names have brackets
        item = re.sub(r'(?<!《)工伤保险条例(?!》)', '《工伤保险条例》', item)
        item = re.sub(r'(?<!《)行政诉讼法(?!》)', '《行政诉讼法》', item)
        # ... more law name patterns
        key = re.sub(r'\s+', '', item)
        if key not in seen:
            seen.add(key)
            normalized.append(item)
    return "\n".join(f"- {item}" for item in normalized)
```

Limitation: doesn't catch all variations. Some repetition in the output is expected.

## Three-Dimension Auto-Classification

Keyword-scoring approach to assign each case to research dimensions:

```python
dim1_keywords = ["认定方法", "审查标准", "举证责任", "证据", "高度盖然性", "综合判断", "劳动关系认定"]
dim2_keywords = ["适用", "解释", "立法本意", "合理时间", "合理路线", "工作原因", "工作场所", "工伤保险责任", "上下班途中"]
dim3_keywords = ["撤销", "司法审查", "程序性行政行为", "行政复议", "检察监督", "抗诉", "不予认定", "送达", "注销"]
```

Special rules:
- "举证责任" + "分配" → dimension 1 (举证责任分配规则)
- "程序性行政行为" → dimension 3 (程序可诉性)
- "抗诉" or "检察监督" or "跟进监督" → dimension 3 (检察监督)

Score each dimension by keyword hits, take the top 1-2 dimensions.

## Tag Auto-Generation

Keyword-to-tag mapping for Chinese legal cases:

```python
tag_map = [
    ("举证责任", ["举证责任", "证明", "证据"]),
    ("上下班途中", ["上下班", "合理路线", "合理时间"]),
    ("工作原因", ["工作原因", "工作职责"]),
    ("工作场所", ["工作场所", "工作区域"]),
    ("工作时间", ["工作时间", "合理延伸"]),
    ("视同工伤", ["48小时", "突发疾病", "视同"]),
    ("劳动关系", ["劳动关系", "事实劳动", "从属性"]),
    ("工伤保险责任", ["工伤保险责任", "工伤保险待遇"]),
    ("违法转包", ["转包", "分包", "挂靠"]),
    ("新就业形态", ["骑手", "外卖", "平台", "快递员"]),
    ("超龄劳动者", ["退休", "超龄", "超过法定退休年龄"]),
    ("检察监督", ["检察", "抗诉", "监督"]),
    ("冒用身份", ["冒用", "身份"]),
    ("职业病", ["职业病", "职业", "诊断"]),
    ("因工外出", ["因工外出", "外出"]),
    ("用人单位注销", ["注销", "注销登记"]),
    ("行政复议", ["行政复议", "复议"]),
]
```

Always prepend `工伤认定` as the first tag. Cap at 5 tags.

## Concept and Thesis Linking

Link cases to concept pages by matching case content keywords against a concept-to-keyword map:

```python
concept_map = [
    ("工伤认定的核心要件", ["核心要件", "认定要件"]),
    ("工伤认定中的举证责任", ["举证责任", "举证", "证明责任"]),
    ("工伤认定中的不确定法律概念", ["不确定", "解释", "判断标准"]),
    ("工伤认定中的程序性问题", ["程序", "受理", "中止", "送达", "时效"]),
    ("工伤认定的司法审查", ["司法审查", "行政诉讼", "审查标准"]),
    ("上下班途中合理时间的认定边界", ["上下班", "合理时间", "合理路线"]),
    ("工作时间的功能主义解构", ["工作时间", "合理延伸", "准备性"]),
    ("劳动关系与工伤认定", ["劳动关系", "事实劳动", "从属性"]),
    ("工伤保险制度", ["工伤保险待遇", "工伤保险基金", "先行支付"]),
    ("检察跟进监督制度", ["检察", "抗诉", "监督", "检例"]),
    ("新就业形态劳动者职业伤害保障", ["骑手", "外卖", "平台", "快递"]),
]
```

Similarly for thesis entities. Max 3 links per section.

## Source Document Quality Issues

Not all cases in the source compilation have complete data:

- **5 cases** (公报案例) have "原公报文本未单列裁判案号" — no case numbers in source
- **2 cases** (检例205, 检例236) have "原文对法院案号作匿名处理" 
- **1 case** (邓金龙, case 12) has truncated 裁判要旨 — shows "广东省深圳市中级人民法院 / 行 政 判 决 书 / （2016）粤03行终792号" instead of the actual legal principle (source document error)
- **1 case** (谢某, case 32) has overlapping facts with case 24 (检例205) — both reference "李某" in their basic facts section (possible source document copy-paste error)

## Session Results

- **53 cases** parsed from 1 DOCX (64362 chars)
- **53 entity pages** created in `entities/`
- **5 cases** with missing case numbers (preserved as "原公报文本未单列裁判案号")
- **0 parsing errors** after fixing separator detection
- All pages have `群案研究定位`, tags, concept links, and thesis links

Parsing script saved to `_scripts/create_case_pages.py` in the wiki directory.
