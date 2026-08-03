# Session 2026-07-30: Cross-Reference Network Lessons

## The Problem

After ingesting 25 papers + 15 concept pages + dead link cleanup, the user
reported two issues in Obsidian:

1. **4 papers still had "详见原文"** for abstract/conclusion — auto-extraction
   had failed silently and placeholders weren't caught before reporting done.
   Fix: re-extract with dedicated script reading ALL pages with multiple regex
   patterns (already documented in SKILL.md).

2. **133 dead links** — every keyword in "涉及概念" was wrapped in `[[]]`.
   Fix: high-frequency (3+ refs) → themed concept pages; low-frequency →
   plain text. (Already documented in SKILL.md.)

3. **CRITICAL NEW LESSON: Zero cross-references between papers.** After fixing
   dead links, every paper linked only to [[CSSCI法学论文写作方法论]] and
   1-2 concept pages. No paper linked to the anchor draft (底稿) or to any
   other paper. The wiki was a pile of isolated islands despite having rich
   content and zero dead links.

## Why This Happened

- Batch ingestion focused on individual page content, not inter-page relationships
- The "涉及概念" section was populated with keywords from auto-extraction, not
  with deliberate cross-references to peer papers
- The anchor draft (检例205号) was treated as just another entity page, not as
  the central hub that all papers must connect to
- Dead link cleanup removed broken links but didn't add missing connections

## The Fix

### Step 1: Anchor-first cross-reference
Manually add a "与引用文献的关联" section to the anchor/draft, linking to ALL
papers with specific theoretical connections grouped by theme.

### Step 2: Per-paper cross-references via parallel delegate_task
- Split papers into groups of 8-9
- Each subagent reads the paper + the anchor's key theoretical contributions
- Writes "与底稿的关联" and "与其他论文的关联" sections
- Quality bar: each connection must specify the theoretical point and the
  nature of the relationship (呼应/补充/分歧 + reason)

### Step 3: Verification
Run the cross-reference check script. Target:
- Every paper has "与底稿的关联" section ✅
- Every paper has 3-6 entity cross-references ✅
- Anchor links to all papers ✅
- Zero papers with only concept-page links ✅

## Results

| Metric | Before | After |
|---|---|---|
| Paper-to-paper links | 0 | 122 |
| Papers with draft link | 0/25 | 25/25 |
| Anchor outbound links | 3 (concepts only) | 19 (all papers) |
| Avg outbound links/paper | 0 | 4.9 |

## Key Insight

**Content completeness has three layers, not two:**
1. ~~Empty pages~~ → pages with full content
2. ~~Dead links~~ → all links resolve
3. **Isolated pages → cross-reference network** ← THIS IS THE THIRD LAYER

A wiki can pass checks 1 and 2 and still be useless if check 3 fails.
The cross-reference network is what makes a wiki a *wiki* rather than a
collection of standalone summaries.
