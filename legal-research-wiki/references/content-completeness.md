# Wiki Content Completeness — Mandatory Discipline

> 来源：原独立技能 `wiki-content-completeness` v1.0.0，于 v3.0.0 合并入 `legal-research-wiki`（内容一条未删）。
> 本文件是**强制纪律**：摄入任何素材建 Wiki 时，每页必须写满实质内容，不允许空壳页面。

**CRITICAL RULE**: Every wiki page created during ingestion MUST contain substantive, detailed content. Empty pages with only metadata are worthless for academic work. This is non-negotiable.

## When This Rule Applies
- ALWAYS — when ingesting any file, paper, case, or document into a wiki
- When creating concept pages, entity pages, comparison pages, or any wiki page
- When the user says "摄入" (ingest), "建wiki", or "添加到知识库"

## Content Requirements by Page Type

### Case Pages (案例实体页)
Each case page MUST include:
- 裁判日期 (date of judgment)
- 来源 (source: 公报/指导案例/典型案例 etc.)
- 案号 (case number)
- 基本案情 (facts — full or summarized)
- 裁判结果 (outcome)
- 裁判要旨 (holding/key legal rule — the MOST important field)
- 裁判依据 (legal basis — statutes cited)
- Cross-references to at least 2 concept pages

### Paper Pages (论文实体页)
Each paper page MUST include:
- Author and affiliation
- Full abstract or detailed content overview (not just one line)
- Key arguments and conclusions
- Research method used
- Relevance to the wiki's domain
- Cross-references to at least 2 concept pages

### Concept Pages (概念页)
Each concept page MUST include:
- Clear definition/explanation of the concept
- Current state of knowledge from ingested sources
- Specific examples from cases or papers
- Contradictions or debates (if any)
- Cross-references to at least 2 other pages

## Anti-Patterns (NEVER DO)
- ❌ Creating a page with only title + "详见原始文件"
- ❌ Using placeholder text like "_待评估_" or "_待分类_"
- ❌ One-line summaries for papers with rich content available
- ❌ Batch-creating hundreds of empty shells

## Workflow for Filling Pages

1. Read the source file completely
2. Extract all substantive content
3. Write the page with full details
4. Add cross-references
5. Verify the page has at least 500 characters of meaningful content

## Verification Command
```bash
# Find thin pages that need enrichment
find wiki/entities wiki/concepts -name "*.md" -exec wc -c {} \; | sort -n | head -20
```

## 六维质量检查（与主技能正文联动）

合并自原技能后，主技能正文的六维标准继续适用（摘要≥50字纯中文 / 结论≥200字无碎片 / 无PDF残留 / 关键词干净 / YAML无引号嵌套 / 标题后空行）。本文件的"至少500字符"是底线，六维是质量门禁，两者都执行。
