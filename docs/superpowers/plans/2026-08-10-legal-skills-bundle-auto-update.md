# Legal Skills Bundle Auto-Update Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a six-hour, prompt-before-write Bundle updater that checks GitHub `main`, updates the three legal Skills together, preserves local changes through explicit confirmation and backups, and rolls back failed Codex/source-copy or Hermes Hub updates.

**Architecture:** A self-contained standard-library Python updater is developed and tested from `chinese-law-paper-writing/scripts/legal_skills_update.py`, then copied byte-for-byte into the other two separately installed Skill packages. A repository release-preparation tool generates per-Skill lock files and a root `bundle-release.json`; the runtime checker uses those locks for local-modification detection and the remote manifest for version checks, update notes, archive verification, and transactions.

**Tech Stack:** Python 3.11+ standard library (`argparse`, `contextlib`, `dataclasses`, `hashlib`, `json`, `pathlib`, `shutil`, `subprocess`, `tempfile`, `urllib`, `zipfile`), `unittest`, Markdown, JSON, Hermes CLI.

## Global Constraints

- Automatic network checks occur at most once every 6 hours (`21_600` seconds).
- “Remind later” suppresses notices for 4 hours (`14_400` seconds) without a second network request.
- Every write requires prior user confirmation; no check command may install files.
- The three managed Skills form one update unit: `chinese-law-paper-writing`, `legal-research-wiki`, and `legal-wiki-audit-repair`.
- No third-party Python dependency, GitHub Token, startup hook, background service, or modification of user research files.
- Runtime downloads are restricted to approved GitHub HTTPS hosts, safe ZIP entries, and files covered by SHA256 in the manifest.
- The updater must refuse to overwrite a Git worktree or symlinked development installation.
- The three installed updater scripts must remain byte-identical.
- Existing repository compatibility, safety, and Codex validation checks must continue to pass on Windows with UTF-8 mode.

---

## File Responsibility Map

- `tools/prepare_bundle_release.py`: developer-only manifest/lock generator and `--check` validator.
- `bundle-release.json`: current Bundle version, structured release notes, per-Skill versions, download URL, and repository-relative file hashes.
- `<skill>/bundle-lock.json`: installed baseline version and per-file official hashes for one Skill.
- `<skill>/scripts/legal_skills_update.py`: self-contained runtime CLI; all three copies are identical.
- `tests/test_bundle_updater.py`: release-tool, cache, manifest, archive, modification, transaction, concurrency, and Hermes adapter tests.
- `tests/test_skill_compatibility.py`: package-level contract, routing description, version, updater-copy, lock, and README assertions.
- `README.md`: end-user update behavior, one-time migration, manual commands, boundaries, and recovery.
- `<skill>/SKILL.md`: minimal preflight instructions; only the audit Skill becomes the update-only routing entrypoint.
- `<skill>/README.md`: short pointer to the root update guide and current Skill version.

---

### Task 1: Define the Release Manifest and Lock Contract

**Files:**
- Create: `tools/prepare_bundle_release.py`
- Create: `tests/test_bundle_updater.py`

**Interfaces:**
- Produces: `collect_skill_files(skill_dir: Path) -> dict[str, str]`
- Produces: `read_skill_version(skill_dir: Path) -> str`
- Produces: `build_lock(skill_name: str, skill_version: str, bundle_version: str, files: dict[str, str]) -> dict`
- Produces: `build_manifest(root: Path, release: dict) -> dict`
- Produces CLI: `python tools/prepare_bundle_release.py --write --bundle-version VERSION --published-at ISO8601 --update-level LEVEL --summary TEXT --change TEXT` and `python tools/prepare_bundle_release.py --check`

- [ ] **Step 1: Write failing contract tests**

Create `tests/test_bundle_updater.py` with import helpers and the first tests:

```python
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PREPARE = ROOT / "tools" / "prepare_bundle_release.py"
UPDATER = ROOT / "chinese-law-paper-writing" / "scripts" / "legal_skills_update.py"
SKILLS = (
    "chinese-law-paper-writing",
    "legal-research-wiki",
    "legal-wiki-audit-repair",
)


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


class ReleaseContractTests(unittest.TestCase):
    def test_collect_skill_files_is_stable_and_excludes_lock_and_cache(self):
        module = load_module(PREPARE, "prepare_bundle_release")
        with tempfile.TemporaryDirectory() as tmp:
            skill = Path(tmp) / "demo"
            (skill / "scripts" / "__pycache__").mkdir(parents=True)
            (skill / "SKILL.md").write_text("demo", encoding="utf-8")
            (skill / "bundle-lock.json").write_text("{}", encoding="utf-8")
            (skill / "scripts" / "tool.py").write_text("print(1)\n", encoding="utf-8")
            (skill / "scripts" / "__pycache__" / "tool.pyc").write_bytes(b"cache")

            files = module.collect_skill_files(skill)

            self.assertEqual(set(files), {"SKILL.md", "scripts/tool.py"})
            self.assertRegex(files["SKILL.md"], r"^[0-9a-f]{64}$")

    def test_build_lock_uses_exact_contract(self):
        module = load_module(PREPARE, "prepare_bundle_lock")
        lock = module.build_lock("demo-skill", "2.3.4", "1.0.0", {"SKILL.md": "a" * 64})
        self.assertEqual(lock, {
            "schema_version": 1,
            "bundle_id": "hermes-legal-research-skills",
            "bundle_version": "1.0.0",
            "skill_name": "demo-skill",
            "skill_version": "2.3.4",
            "files": {"SKILL.md": "a" * 64},
        })
```

- [ ] **Step 2: Run the tests and confirm the missing-tool failure**

Run:

```powershell
python -X utf8 -m unittest tests.test_bundle_updater.ReleaseContractTests -v
```

Expected: FAIL because `tools/prepare_bundle_release.py` does not exist.

- [ ] **Step 3: Implement the deterministic release tool**

Create `tools/prepare_bundle_release.py` with these constants and functions:

```python
ROOT = Path(__file__).resolve().parents[1]
SKILLS = (
    "chinese-law-paper-writing",
    "legal-research-wiki",
    "legal-wiki-audit-repair",
)
BUNDLE_ID = "hermes-legal-research-skills"
LOCK_NAME = "bundle-lock.json"
IGNORED_NAMES = {"__pycache__", ".DS_Store"}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def collect_skill_files(skill_dir: Path) -> dict[str, str]:
    files = {}
    for path in sorted(skill_dir.rglob("*")):
        if not path.is_file() or LOCK_NAME in path.parts or any(part in IGNORED_NAMES for part in path.parts):
            continue
        if path.suffix == ".pyc":
            continue
        files[path.relative_to(skill_dir).as_posix()] = sha256_file(path)
    return files


def read_skill_version(skill_dir: Path) -> str:
    text = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
    match = re.search(r'^\s{2}version:\s*["\']?(\d+\.\d+\.\d+)["\']?\s*$', text, re.MULTILINE)
    if not match:
        raise ValueError(f"missing metadata.version: {skill_dir}")
    return match.group(1)
```

Add manifest validation for exact Skill names, SemVer, current history entry, `SKILL.md`, `agents/openai.yaml`, and HTTPS GitHub archive URL. `--write` must write locks first and then hash every Skill file including the generated lock into the root manifest. The first `--write` requires all release metadata arguments; later runs may reuse the current release entry. Rewriting the same Bundle version replaces that history entry instead of duplicating it. `--check` must build expected data in memory and exit nonzero when the checked-in JSON differs.

- [ ] **Step 4: Test release-history replacement without touching repository metadata**

Create three minimal Skill fixtures in a temporary repository and call `build_manifest` twice for Bundle `1.0.0`. Assert the second call replaces the existing `1.0.0` history entry and preserves one entry with these structured Chinese changes:

```json
[
  "增加每6小时一次的按需更新检查",
  "增加三个Skill统一备份、校验、更新和失败回滚",
  "增加本地修改检测、稍后提醒和忽略当前版本"
]
```

Do not generate real repository locks or a manifest yet. Task 6 first bumps versions and installs all managed files, then creates the authoritative Bundle metadata once so no provisional baseline can conceal changes.

- [ ] **Step 5: Run the release contract tests**

Run the same unittest command. Expected: PASS for file collection, lock shape, release-history replacement, and validation errors. The repository-level `--check` assertion is added in Task 6 after all managed files exist.

- [ ] **Step 6: Commit the contract and release tool**

```powershell
git add tools/prepare_bundle_release.py tests/test_bundle_updater.py
git commit -m "feat: define legal skills bundle release contract"
```

---

### Task 2: Implement Cached, Prompt-Only Update Checks

**Files:**
- Create: `chinese-law-paper-writing/scripts/legal_skills_update.py`
- Modify: `tests/test_bundle_updater.py`

**Interfaces:**
- Produces: `parse_semver(value: str) -> tuple[int, int, int]`
- Produces: `validate_manifest(data: object) -> dict`
- Produces: `get_state_root(env: Mapping[str, str] | None = None, platform_name: str | None = None) -> Path`
- Produces: `load_state(path: Path) -> dict`
- Produces: `save_state(path: Path, state: dict) -> None`
- Produces: `operation_lock(path: Path) -> ContextManager[None]`
- Produces: `fetch_manifest(url: str, etag: str | None, timeout: float = 3.0) -> FetchResult`
- Produces: `check_for_update(skill_dir: Path, *, force: bool = False, now: float | None = None, fetcher=fetch_manifest) -> dict`
- Produces CLI: `check [--force] [--json]`, `snooze [--hours 4] [--json]`, `ignore VERSION [--json]`, and `details [--json]`

- [ ] **Step 1: Add failing cache and state tests**

Add tests using a temporary Skill directory with a minimal `bundle-lock.json` and an injected fetcher:

```python
class UpdateCheckTests(unittest.TestCase):
    def test_fresh_cache_avoids_network_for_six_hours(self):
        module = load_module(UPDATER, "legal_skills_update")
        calls = []
        state = {
            "last_network_check": 1_000.0,
            "cached_manifest": make_manifest("1.0.0"),
            "etag": '"abc"',
        }
        with updater_fixture(state=state) as fixture:
            result = module.check_for_update(
                fixture.skill_dir,
                now=1_000.0 + 21_599,
                fetcher=lambda *args: calls.append(args),
            )
        self.assertEqual(result["status"], "cached")
        self.assertEqual(calls, [])

    def test_six_hour_boundary_fetches_and_finds_newer_version(self):
        module = load_module(UPDATER, "legal_skills_update_boundary")
        with updater_fixture(last_check=1_000.0) as fixture:
            result = module.check_for_update(
                fixture.skill_dir,
                now=1_000.0 + 21_600,
                fetcher=lambda *_: module.FetchResult(make_manifest("1.1.0"), '"new"', False),
            )
        self.assertEqual(result["status"], "update_available")
        self.assertEqual(result["current_version"], "1.0.0")
        self.assertEqual(result["latest_version"], "1.1.0")
```

Also add exact tests for force bypass, ETag-not-modified, offline-not-up-to-date, atomic state writes, Windows/POSIX state roots, snooze expiry, ignored current version, higher version after an ignored version, and cross-version history aggregation.

- [ ] **Step 2: Run the focused tests and confirm failure**

```powershell
python -X utf8 -m unittest tests.test_bundle_updater.UpdateCheckTests -v
```

Expected: FAIL because the updater module and interfaces do not exist.

- [ ] **Step 3: Implement state, manifest, and network primitives**

Use these immutable values:

```python
CHECK_INTERVAL_SECONDS = 6 * 60 * 60
DEFAULT_SNOOZE_SECONDS = 4 * 60 * 60
NETWORK_TIMEOUT_SECONDS = 3.0
MANIFEST_URL = (
    "https://raw.githubusercontent.com/shawndeng321/"
    "hermes-obsidian-legal-cssci-wiki-writing-skills/main/bundle-release.json"
)
ALLOWED_DOWNLOAD_HOSTS = {
    "github.com",
    "raw.githubusercontent.com",
    "codeload.github.com",
    "objects.githubusercontent.com",
    "release-assets.githubusercontent.com",
}
```

Implement standard-library OS locks with `msvcrt.locking(..., LK_NBLCK, 1)` on Windows and `fcntl.flock(..., LOCK_EX | LOCK_NB)` on POSIX. Keep the file descriptor open for the context lifetime so process exit releases the lock automatically. Write `state.json` through a sibling temporary file, `flush`, `os.fsync`, and `os.replace`.

`fetch_manifest` must return a dataclass:

```python
@dataclass(frozen=True)
class FetchResult:
    manifest: dict | None
    etag: str | None
    not_modified: bool
```

Do not return `up_to_date` for exceptions. Return structured `offline`, `invalid_manifest`, or `busy` statuses with `fatal: False` in automatic check mode.

- [ ] **Step 4: Implement prompt-only CLI state actions**

All commands print one JSON object when `--json` is present. `check` never calls any apply function. `snooze` writes `snooze_until = now + hours * 3600`; `ignore` writes `ignored_version`; `details` returns cached manifest and aggregated history without networking.

- [ ] **Step 5: Run focused tests and full existing regression**

```powershell
python -X utf8 -m unittest tests.test_bundle_updater.UpdateCheckTests -v
python -X utf8 -m unittest tests/test_skill_compatibility.py -v
python -X utf8 -m unittest tests/test_script_safety.py -v
```

Expected: all tests PASS.

- [ ] **Step 6: Commit cached checks**

```powershell
git add chinese-law-paper-writing/scripts/legal_skills_update.py tests/test_bundle_updater.py
git commit -m "feat: add cached legal skill update checks"
```

---

### Task 3: Validate Archives and Detect Local Modifications

**Files:**
- Modify: `chinese-law-paper-writing/scripts/legal_skills_update.py`
- Modify: `tests/test_bundle_updater.py`

**Interfaces:**
- Consumes: validated manifest and state from Task 2.
- Produces: `safe_extract_bundle(archive: Path, destination: Path, manifest: dict) -> Path`
- Produces: `verify_staged_bundle(bundle_root: Path, manifest: dict) -> None`
- Produces: `inspect_installation(skills_root: Path, manifest: dict) -> dict`
- Produces: `format_incoming_diff(skills_root: Path, staged_root: Path, changed_paths: list[str]) -> str`

- [ ] **Step 1: Write failing hostile-archive and modification tests**

Create in-memory ZIP fixtures and assert rejection of:

```python
for member in ("../escape.txt", "/absolute.txt", "repo/../../escape.txt"):
    with self.subTest(member=member):
        archive = make_zip({member: b"bad"})
        with self.assertRaises(module.ArchiveError):
            module.safe_extract_bundle(archive, destination, manifest)
```

Add tests for symlink-mode entries, duplicate case-insensitive paths, a package over the configured uncompressed limit, missing Skill directories, extra files not in the manifest, wrong SHA256, archive/checked-manifest drift, modified files, deleted files, and local extras. Assert the installation report uses exact keys:

```python
{
    "status": "local_changes",
    "modified": [...],
    "deleted": [...],
    "added": [...],
    "missing_skills": [...],
}
```

- [ ] **Step 2: Run focused tests and confirm failure**

```powershell
python -X utf8 -m unittest tests.test_bundle_updater.ArchiveSafetyTests tests.test_bundle_updater.InstallationInspectionTests -v
```

Expected: FAIL with missing archive and inspection functions.

- [ ] **Step 3: Implement bounded safe extraction**

Set explicit limits:

```python
MAX_ARCHIVE_BYTES = 50 * 1024 * 1024
MAX_UNCOMPRESSED_BYTES = 200 * 1024 * 1024
MAX_ARCHIVE_FILES = 2_000
```

Validate every `ZipInfo` before writing anything. Reject absolute/drive paths, `..`, backslashes that normalize ambiguously, symlinks via Unix mode bits, file-count/size limits, and case-fold collisions. Extract only after the complete central directory passes validation.

- [ ] **Step 4: Implement manifest and installation verification**

Compare the archive’s `bundle-release.json` semantic fields (`schema_version`, `bundle_id`, `bundle_version`, `skills`, `files`) with the cached manifest before accepting files. Verify exact repository-relative SHA256 coverage. Compare installed files against each local `bundle-lock.json`; classify every mismatch without changing the installation.

Generate incoming unified diffs only for UTF-8 text files smaller than 1 MiB. For binary or larger files, list path and hash change without loading the body.

- [ ] **Step 5: Run focused and full updater tests**

```powershell
python -X utf8 -m unittest tests.test_bundle_updater -v
```

Expected: all updater tests PASS.

- [ ] **Step 6: Commit safe staging**

```powershell
git add chinese-law-paper-writing/scripts/legal_skills_update.py tests/test_bundle_updater.py
git commit -m "feat: validate legal skill update archives"
```

---

### Task 4: Add Source-Copy Transactions, Backup, and Rollback

**Files:**
- Modify: `chinese-law-paper-writing/scripts/legal_skills_update.py`
- Modify: `tests/test_bundle_updater.py`

**Interfaces:**
- Consumes: staged and verified Bundle from Task 3.
- Produces: `detect_installation_mode(skills_root: Path, skill_names: Sequence[str]) -> str`
- Produces: `apply_source_transaction(skills_root: Path, staged_root: Path, manifest: dict, state_root: Path, *, allow_local_changes: bool = False, install_missing: bool = False, fault_hook=None) -> dict`
- Produces CLI: `diff [--json]` and `apply [--allow-local-changes] [--install-missing] [--json]`

- [ ] **Step 1: Write failing transactional tests**

Use three tiny fake Skill directories and assert:

```python
result = module.apply_source_transaction(
    fixture.skills_root,
    fixture.staged_root,
    fixture.manifest,
    fixture.state_root,
)
self.assertEqual(result["status"], "updated")
self.assertEqual(read_bundle_versions(fixture.skills_root), {"1.1.0"})
self.assertTrue(Path(result["backup_path"]).exists())
```

Add a fault hook that raises after replacing the second Skill and assert all three old directories are restored. Add tests that local changes require `allow_local_changes=True`, missing Skills require `install_missing=True`, Git worktrees and symlinked Skill directories are rejected, and two simultaneous apply calls yield one `updated` and one `busy` result.

- [ ] **Step 2: Run focused tests and confirm failure**

```powershell
python -X utf8 -m unittest tests.test_bundle_updater.SourceTransactionTests -v
```

Expected: FAIL because transaction functions do not exist.

- [ ] **Step 3: Implement worker copy and transaction boundaries**

Before replacing directories, copy the updater to `<state-root>/worker/legal_skills_update.py`. The CLI `apply` command re-executes that copy with a private `worker-apply` subcommand, an explicit Skills root, cached manifest path, and staged path. Never use the process current directory as an implicit target.

Hold `operation.lock` for the full write transaction. Create a timestamped backup directory containing all existing Skill directories and `transaction.json`. Move staged directories from the same filesystem into place. Validate installed locks and hashes after all three moves. On exception, remove only directories recorded as newly installed by this transaction and restore every old directory from the backup.

- [ ] **Step 4: Implement confirmation gates in the CLI**

`apply` without `--allow-local-changes` returns `confirmation_required` plus the modification report and performs no write. `--allow-local-changes` represents the user’s second confirmation. `--install-missing` separately represents permission to install absent Skill directories. Neither flag may be inferred from the other.

- [ ] **Step 5: Run transaction and updater suites**

```powershell
python -X utf8 -m unittest tests.test_bundle_updater.SourceTransactionTests -v
python -X utf8 -m unittest tests.test_bundle_updater -v
```

Expected: all tests PASS and temporary fixtures contain no files outside their own roots.

- [ ] **Step 6: Commit source-copy updating**

```powershell
git add chinese-law-paper-writing/scripts/legal_skills_update.py tests/test_bundle_updater.py
git commit -m "feat: update legal skill bundle transactionally"
```

---

### Task 5: Add the Hermes Skills Hub Adapter

**Files:**
- Modify: `chinese-law-paper-writing/scripts/legal_skills_update.py`
- Modify: `tests/test_bundle_updater.py`

**Interfaces:**
- Consumes: shared operation lock, backups, manifest verification, and transaction result schema.
- Produces: `read_hermes_lock(lock_path: Path) -> dict`
- Produces: `detect_hermes_bundle(lock_data: dict, skills_root: Path) -> dict`
- Produces: `apply_hermes_transaction(skills_root: Path, lock_path: Path, manifest: dict, state_root: Path, *, runner=subprocess.run, allow_local_changes: bool = False) -> dict`

- [ ] **Step 1: Write failing Hub provenance and rollback tests**

Build a version-1 fake Hub lock with three target entries and one unrelated entry. Inject a runner that records exact commands:

```python
expected = [
    ["hermes", "skills", "update", "chinese-law-paper-writing"],
    ["hermes", "skills", "update", "legal-research-wiki"],
    ["hermes", "skills", "update", "legal-wiki-audit-repair"],
]
self.assertEqual(commands, expected)
```

Add tests for mixed sources, unknown lock version, a failure on command two, post-update hash mismatch, restoration of the original three directories and lock, and refusal to overwrite a lock whose unrelated entry changed during the transaction.

- [ ] **Step 2: Run focused tests and confirm failure**

```powershell
python -X utf8 -m unittest tests.test_bundle_updater.HermesAdapterTests -v
```

Expected: FAIL with missing Hermes adapter functions.

- [ ] **Step 3: Implement source-aware Hub updates**

Accept only lock schema `version == 1`, exact target names, and one common GitHub repository provenance. Snapshot directories and lock bytes before invoking Hermes. Run one explicit named command per Skill with `capture_output=True`, `text=True`, UTF-8 decoding, and no shell. Never call bare `hermes skills update` because it could update unrelated Skills.

After commands complete, verify all target files against the manifest. On failure, compare the parsed non-target lock content with the snapshot; restore the full lock only when non-target content is unchanged. Otherwise restore directories, preserve both lock copies in the backup, return `manual_recovery_required`, and stop writing.

- [ ] **Step 4: Run Hub, updater, and existing safety tests**

```powershell
python -X utf8 -m unittest tests.test_bundle_updater.HermesAdapterTests -v
python -X utf8 -m unittest tests.test_bundle_updater -v
python -X utf8 -m unittest tests/test_script_safety.py -v
```

Expected: all tests PASS.

- [ ] **Step 5: Commit the Hermes adapter**

```powershell
git add chinese-law-paper-writing/scripts/legal_skills_update.py tests/test_bundle_updater.py
git commit -m "feat: orchestrate Hermes skill bundle updates"
```

---

### Task 6: Wire the Updater Into All Three Skills

**Files:**
- Create: `bundle-release.json`
- Create: `chinese-law-paper-writing/bundle-lock.json`
- Create: `legal-research-wiki/bundle-lock.json`
- Create: `legal-wiki-audit-repair/bundle-lock.json`
- Modify: `chinese-law-paper-writing/SKILL.md`
- Modify: `legal-research-wiki/SKILL.md`
- Modify: `legal-wiki-audit-repair/SKILL.md`
- Modify: `chinese-law-paper-writing/README.md`
- Modify: `legal-research-wiki/README.md`
- Modify: `legal-wiki-audit-repair/README.md`
- Create: `legal-research-wiki/scripts/legal_skills_update.py`
- Create: `legal-wiki-audit-repair/scripts/legal_skills_update.py`
- Modify: `tests/test_skill_compatibility.py`
- Modify: `tests/test_bundle_updater.py`

**Interfaces:**
- Consumes: complete updater CLI and release tool.
- Produces: three separately installable Skills with identical updater behavior.

- [ ] **Step 1: Add failing package-wiring tests**

Update expected versions to `5.2.0`, `4.2.0`, and `4.3.0`. Add assertions:

```python
updaters = [ROOT / name / "scripts" / "legal_skills_update.py" for name in SKILLS]
self.assertTrue(all(path.exists() for path in updaters))
self.assertEqual(len({path.read_bytes() for path in updaters}), 1)
for skill_name in SKILLS:
    text = (ROOT / skill_name / "SKILL.md").read_text(encoding="utf-8")
    self.assertIn("legal_skills_update.py check --json", text)
    self.assertIn("6 小时", text)
```

Assert only `legal-wiki-audit-repair` has update-only routing language in its frontmatter description and that the description remains at most 60 characters.

- [ ] **Step 2: Run compatibility tests and confirm failure**

```powershell
python -X utf8 -m unittest tests/test_skill_compatibility.py -v
```

Expected: FAIL because versions, updater copies, preflight text, and routing metadata are not yet updated.

- [ ] **Step 3: Add concise preflight instructions and bump versions**

Place a short `## 技能包更新预检` section near the start of each Skill. It must instruct the Agent to run `check --json`, continue silently for non-update statuses, render the four user choices for `update_available`, and never run `apply` without explicit confirmation. Do not duplicate the long update documentation inside Skill bodies.

Change only the audit Skill’s description to an English sentence no longer than 60 characters that covers Wiki audit/repair and Bundle updates. Update `EXPECTED_DESCRIPTIONS` accordingly.

- [ ] **Step 4: Copy and verify the updater**

Copy the completed Chinese-paper updater bytes to the other two script paths with a mechanical copy command, then assert byte equality in tests. Do not maintain separate hand-edited variants.

- [ ] **Step 5: Regenerate locks and root manifest**

Run:

```powershell
python -X utf8 tools/prepare_bundle_release.py --write --bundle-version 1.0.0 --published-at 2026-08-10T00:00:00+08:00 --update-level feature --summary "增加按需更新检查、统一备份和回滚" --change "增加每6小时一次的按需更新检查" --change "增加三个Skill统一备份、校验、更新和失败回滚" --change "增加本地修改检测、稍后提醒和忽略当前版本"
python -X utf8 tools/prepare_bundle_release.py --check
```

Expected: both commands exit `0`; generated locks report Bundle `1.0.0` and exact per-Skill versions.

- [ ] **Step 6: Run compatibility, updater, and Codex validators**

```powershell
python -X utf8 -m unittest tests/test_skill_compatibility.py -v
python -X utf8 -m unittest tests.test_bundle_updater -v
$validator = "$HOME\.codex\skills\.system\skill-creator\scripts\quick_validate.py"
python -X utf8 $validator chinese-law-paper-writing
python -X utf8 $validator legal-research-wiki
python -X utf8 $validator legal-wiki-audit-repair
```

Expected: all unittests PASS and each validator prints `Skill is valid!`.

- [ ] **Step 7: Commit Skill integration**

```powershell
git add bundle-release.json tests/test_skill_compatibility.py tests/test_bundle_updater.py chinese-law-paper-writing legal-research-wiki legal-wiki-audit-repair
git commit -m "feat: enable bundle updates in all legal skills"
```

---

### Task 7: Document Migration, Commands, and Safety Boundaries

**Files:**
- Modify: `README.md`
- Modify: `chinese-law-paper-writing/README.md`
- Modify: `legal-research-wiki/README.md`
- Modify: `legal-wiki-audit-repair/README.md`
- Modify: `.gitignore`
- Modify: `tests/test_skill_compatibility.py`

**Interfaces:**
- Consumes: final CLI commands and statuses from Tasks 2–6.
- Produces: user-facing install/update/recovery contract.

- [ ] **Step 1: Add failing documentation-contract tests**

Assert the root README contains:

```python
for phrase in (
    "每 6 小时",
    "检查法学技能更新",
    "稍后提醒",
    "忽略此版本",
    "一次性升级",
    "本地修改",
    "自动回滚",
    "新建一个 Agent 任务",
):
    self.assertIn(phrase, root_readme)
self.assertNotIn("兼容性测试 8/8", root_readme)
self.assertNotIn("脚本安全测试 9/9", root_readme)
```

Assert each Skill README links to the root update section and shows its new version.

- [ ] **Step 2: Run documentation tests and confirm failure**

```powershell
python -X utf8 -m unittest tests.test_skill_compatibility.SkillCompatibilityTests.test_installation_docs_use_real_skill_identifiers tests.test_skill_compatibility.SkillCompatibilityTests.test_documentation_has_no_known_stale_metadata_or_placeholders -v
```

Expected: FAIL on missing update guide and stale fixed test counts.

- [ ] **Step 3: Write the root update guide**

Add a root `## 自动更新` section covering:

- six-hour first-use checks and manual forced checks;
- the exact four prompt choices;
- three-Skill scope and no silent updates;
- Hermes Hub versus Codex/source-copy apply behavior;
- local-modification confirmation, backup path, rollback, and new-task activation;
- one-time manual upgrade for users who installed before Bundle `1.0.0`;
- no startup daemon, no user-research-file access, and GitHub/HTTPS trust boundary;
- commands for check, details, snooze, ignore, diff, and apply, using a resolved updater path rather than assuming a working directory.

Replace fixed test counts with the durable statement that compatibility, script-safety, and Bundle-updater suites must all pass.

- [ ] **Step 4: Update per-Skill README pointers and ignore runtime artifacts**

Each Skill README gets one short update paragraph linking to `../README.md#自动更新`. Add release staging and local updater-state fixture names to `.gitignore` only if repository tests create them; do not ignore `bundle-lock.json` or `bundle-release.json`.

- [ ] **Step 5: Run documentation and compatibility tests**

```powershell
python -X utf8 -m unittest tests/test_skill_compatibility.py -v
```

Expected: all tests PASS.

- [ ] **Step 6: Commit documentation**

```powershell
git add README.md .gitignore tests/test_skill_compatibility.py chinese-law-paper-writing/README.md legal-research-wiki/README.md legal-wiki-audit-repair/README.md
git commit -m "docs: explain legal skill bundle updates"
```

---

### Task 8: End-to-End Verification and Release Readiness

**Files:**
- Modify only if verification exposes a defect: files from Tasks 1–7.

**Interfaces:**
- Consumes: complete Bundle updater and repository documentation.
- Produces: verified release-ready `main` worktree; no global Skill installation and no push.

- [ ] **Step 1: Run all repository tests**

```powershell
python -X utf8 -m unittest tests/test_skill_compatibility.py -v
python -X utf8 -m unittest tests/test_script_safety.py -v
python -X utf8 -m unittest tests/test_bundle_updater.py -v
```

Expected: all tests PASS with no skipped updater safety cases.

- [ ] **Step 2: Validate every Skill package**

```powershell
$validator = "$HOME\.codex\skills\.system\skill-creator\scripts\quick_validate.py"
python -X utf8 $validator chinese-law-paper-writing
python -X utf8 $validator legal-research-wiki
python -X utf8 $validator legal-wiki-audit-repair
```

Expected: three `Skill is valid!` results.

- [ ] **Step 3: Verify the checked-in release metadata**

```powershell
python -X utf8 tools/prepare_bundle_release.py --check
```

Expected: exit `0` and a message identifying Bundle `1.0.0` as consistent.

- [ ] **Step 4: Run isolated end-to-end demonstrations**

Use a temporary Skills root, state root, local HTTP fixture, and generated old/new Bundle archives to demonstrate:

1. cached check without networking;
2. forced check returning `update_available` and cumulative history;
3. local modification returning `confirmation_required` without writes;
4. confirmed source-copy update producing a backup and three new versions;
5. injected failure restoring all three old versions.

Save only console output under the test runner’s temporary directory; do not install into `~/.codex/skills` or Hermes global directories.

- [ ] **Step 5: Run whitespace and repository checks**

```powershell
git diff --check
git status --short --branch
git log -8 --oneline --decorate
```

Expected: no whitespace errors; only intended implementation changes are present; commit history shows the design, release contract, checker, archive safety, transaction, Hermes adapter, Skill integration, and documentation commits.

- [ ] **Step 6: Commit any verification-only fix**

If verification required a correction, stage only the affected paths and commit:

```powershell
git commit -m "fix: close legal skill updater verification gaps"
```

If no correction was required, do not create an empty commit.

- [ ] **Step 7: Report completion without pushing**

Report exact test counts, Bundle/Skill versions, backup behavior, commit list, worktree status, and the fact that GitHub has not yet received the implementation. Ask separately before any push or installation into user-global Skill directories.
