# Main Branch Promotion and README Release Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Publish the Hermes/Codex-compatible multimodal skill package from `codex/hermes-codex-compatibility` to `main` with release-ready README files and verified identical branch trees.

**Architecture:** Treat the compatibility branch as the single source of truth. Update its documentation contract and four README files first, validate and push that branch, then fast-forward `main` to the exact same commit and revalidate before pushing `main`.

**Tech Stack:** Git, Markdown, Python `unittest`, Codex `quick_validate.py`, Python `py_compile`, PowerShell.

## Global Constraints

- Preserve all existing Git history; do not rebase, squash, cherry-pick, reset, or force-push.
- Use `git merge --ff-only codex/hermes-codex-compatibility` for the `main` promotion.
- Keep `codex/hermes-codex-compatibility`, its worktree, and all backup branches after publishing.
- Stage only the README, documentation-contract test, plan, and spec paths created or modified by this release.
- Do not access or modify a real Obsidian Vault, Hermes account, or external research corpus.
- Stop if a test fails, the remote moves, authentication fails, or fast-forward is no longer possible.

---

### Task 1: Establish the release checkpoint and README contract

**Files:**
- Modify: `tests/test_skill_compatibility.py`
- Reference: `docs/superpowers/specs/2026-08-07-main-promotion-readme-design.md`

**Interfaces:**
- Consumes: current README text and `ROOT` from `tests/test_skill_compatibility.py`.
- Produces: updated installation and stale-documentation contracts used by Task 2.

- [ ] **Step 1: Reconfirm clean worktrees and create the main recovery branch**

Run from the compatibility worktree:

```powershell
git status --short --branch
git -C ../.. status --short --branch
git branch backup/main-before-compat-promotion-20260807 main
git show --no-patch --oneline backup/main-before-compat-promotion-20260807
```

Expected: both worktrees have no path entries after the branch header; the backup points to `0a5797a`.

- [ ] **Step 2: Replace transition-state assertions with the main release contract**

In `test_installation_docs_use_real_skill_identifiers`, replace the assertions for `相对 master/main` and `current-branch-install` with:

```python
self.assertIn("## 2026-08 更新内容", root_readme)
self.assertIn("git clone", root_readme)
self.assertIn("#安装", root_readme)
```

In the per-skill README loop, replace the `current-branch-install` assertion with:

```python
self.assertIn("../README.md#安装", skill_readme)
```

In `test_documentation_has_no_known_stale_metadata_or_placeholders`, read all four README files and add:

```python
readmes = [ROOT / "README.md"]
readmes.extend(ROOT / skill_name / "README.md" for skill_name in SKILLS)
combined = "\n".join(path.read_text(encoding="utf-8") for path in readmes)
self.assertIn("Hermes 与 Codex", root_readme)
self.assertIn("兼容性测试 8/8", root_readme)
self.assertIn("脚本安全测试 9/9", root_readme)
self.assertNotIn("尚未合并到 `main`", combined)
self.assertNotIn("当前优化分支", combined)
self.assertNotIn("合并到 `main` 后", combined)
```

- [ ] **Step 3: Run the two targeted tests and verify the expected failures**

Run:

```powershell
python -X utf8 -m unittest tests.test_skill_compatibility.SkillCompatibilityTests.test_installation_docs_use_real_skill_identifiers tests.test_skill_compatibility.SkillCompatibilityTests.test_documentation_has_no_known_stale_metadata_or_placeholders -v
```

Expected: FAIL because the current README files still contain transition-state branch wording and the old `7/7` count.

### Task 2: Convert README files to the main release state

**Files:**
- Modify: `README.md`
- Modify: `chinese-law-paper-writing/README.md`
- Modify: `legal-research-wiki/README.md`
- Modify: `legal-wiki-audit-repair/README.md`
- Modify: `tests/test_skill_compatibility.py`

**Interfaces:**
- Consumes: the updated installation and stale-documentation contracts from Task 1 and current skill versions `5.1.0`, `4.1.0`, and `4.2.0`.
- Produces: one main-ready installation and update narrative shared by all README entrypoints.

- [ ] **Step 1: Rewrite the root project positioning and update section**

Apply these exact content decisions to `README.md`:

```text
Title: Hermes / Codex 法学研究技能包（Chinese Legal Research Skills）
Release heading: ## 2026-08 更新内容
Validation summary: 兼容性测试 8/8、脚本安全测试 9/9，共 17/17
```

The update section must list multimodal ingestion, note-level provenance, six-part audit, stub/SHA256 repair, dual-host metadata, batch-script safety, real DOCX footnotes, Obsidian credential/concurrency hardening, and repository regression tests.

- [ ] **Step 2: Replace transition-state installation sections in the root README**

Use these stable sections:

```markdown
## 安装

### Hermes Skills Hub
### 源码安装（Hermes / Codex）
```

The clone command must use the repository default `main` branch and must not mention `codex/hermes-codex-compatibility` as the required user path.

- [ ] **Step 3: Normalize the three skill README installation sections**

For each skill README:

```text
Remove heading: 当前优化分支
Remove wording: 尚未合并到 `main`
Remove heading/wording: 合并到 `main` 后
Keep: the exact per-skill Hermes Skills Hub command
Add/keep: Codex local-copy guidance pointing to the root README installation section
```

- [ ] **Step 4: Run the targeted test and all link/metadata tests**

Run:

```powershell
python -X utf8 -m unittest tests.test_skill_compatibility.SkillCompatibilityTests.test_installation_docs_use_real_skill_identifiers tests.test_skill_compatibility.SkillCompatibilityTests.test_documentation_has_no_known_stale_metadata_or_placeholders -v
python -X utf8 -m unittest tests/test_skill_compatibility.py -v
```

Expected: both targeted tests pass and all 8 compatibility tests pass.

- [ ] **Step 5: Review and commit only release documentation paths**

Run:

```powershell
git diff --check
git diff -- README.md chinese-law-paper-writing/README.md legal-research-wiki/README.md legal-wiki-audit-repair/README.md tests/test_skill_compatibility.py
git add -- README.md chinese-law-paper-writing/README.md legal-research-wiki/README.md legal-wiki-audit-repair/README.md tests/test_skill_compatibility.py
git commit -m "docs: prepare main release readmes"
```

Expected: one focused documentation commit with no unrelated paths.

### Task 3: Validate and publish the compatibility branch

**Files:**
- Verify: `tests/test_skill_compatibility.py`
- Verify: `tests/test_script_safety.py`
- Verify: `legal-wiki-audit-repair/scripts/multimodal_audit.py`

**Interfaces:**
- Consumes: the main-ready README commit from Task 2.
- Produces: a verified remote `codex/hermes-codex-compatibility` branch at the local HEAD.

- [ ] **Step 1: Run the full repository test suite**

Run:

```powershell
python -X utf8 -m unittest tests/test_skill_compatibility.py tests/test_script_safety.py -v
```

Expected: 17/17 tests pass: 8 compatibility tests and 9 script-safety tests.

- [ ] **Step 2: Validate each Skill and compile the imported audit script**

Run:

```powershell
$validator = "$HOME\.codex\skills\.system\skill-creator\scripts\quick_validate.py"
python -X utf8 $validator chinese-law-paper-writing
python -X utf8 $validator legal-research-wiki
python -X utf8 $validator legal-wiki-audit-repair
python -X utf8 -m py_compile legal-wiki-audit-repair/scripts/multimodal_audit.py
git diff --check
git status --short --branch
```

Expected: three `Skill is valid!` results, successful compilation, no diff errors, and a clean worktree.

- [ ] **Step 3: Push the compatibility branch without force**

Run:

```powershell
git push -u origin codex/hermes-codex-compatibility
git fetch origin
git rev-parse HEAD
git rev-parse origin/codex/hermes-codex-compatibility
```

Expected: both commit IDs are identical. If authentication or network access fails, stop before changing `main`.

### Task 4: Fast-forward, revalidate, and publish main

**Files:**
- Modify by fast-forward only: Git ref `main`
- Verify: the complete repository tree

**Interfaces:**
- Consumes: the pushed compatibility branch commit from Task 3.
- Produces: local and remote `main` pointing to the same verified commit and Git tree.

- [ ] **Step 1: Reconfirm ancestry and fast-forward local main**

Run from the main worktree:

```powershell
git fetch origin
git status --short --branch
git merge-base --is-ancestor origin/main codex/hermes-codex-compatibility
git merge --ff-only codex/hermes-codex-compatibility
```

Expected: the ancestry command exits 0 and the merge reports a fast-forward. Do not substitute a normal merge if it fails.

- [ ] **Step 2: Prove the two local branch trees are identical**

Run:

```powershell
git rev-parse 'main^{tree}'
git rev-parse 'codex/hermes-codex-compatibility^{tree}'
git diff --exit-code main codex/hermes-codex-compatibility
```

Expected: tree IDs are identical and `git diff` has no output.

- [ ] **Step 3: Rerun the full verification on main**

Run:

```powershell
python -X utf8 -m unittest tests/test_skill_compatibility.py tests/test_script_safety.py -v
$validator = "$HOME\.codex\skills\.system\skill-creator\scripts\quick_validate.py"
python -X utf8 $validator chinese-law-paper-writing
python -X utf8 $validator legal-research-wiki
python -X utf8 $validator legal-wiki-audit-repair
python -X utf8 -m py_compile legal-wiki-audit-repair/scripts/multimodal_audit.py
git diff --check
git status --short --branch
```

Expected: 17/17 tests, three valid Skills, successful compilation, no diff errors, and a clean worktree.

- [ ] **Step 4: Push and verify main without force**

Run:

```powershell
git push origin main
git fetch origin
git rev-parse main
git rev-parse origin/main
git rev-parse origin/codex/hermes-codex-compatibility
```

Expected: all three commit IDs are identical. If the push is rejected, stop and inspect the refreshed remote graph.

- [ ] **Step 5: Produce the release update list**

Report these categories from the final README and Git diff:

```text
1. Hermes/Codex dual-host compatibility
2. multimodal image/audio/PDF/reference ingestion
3. legal evidence and note-level provenance boundaries
4. audit, stub re-ingestion, and SHA256 repair
5. batch-script DRY_RUN/backup/scope safety
6. DOCX real-footnote generation and verification
7. Obsidian headless credential and concurrency hardening
8. repository-level compatibility and safety regression tests
```
