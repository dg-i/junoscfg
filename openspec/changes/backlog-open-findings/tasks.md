## 1. Verification (one per docs-plan QA item)

- [x] 1.1 Links: `uv run --locked --group docs mkdocs build --strict` reports no warning outside `BACKLOG.md`; every warning beyond master's 48 is a `BACKLOG.md` link outside `docs/`, and `ls` finds each new target
- [x] 1.2 Commands and examples: `run-probes.sh` at the change head gives the results the entries state, and the same output as `probes-716a9d1.txt` apart from the HEAD line
- [x] 1.3 Referenced paths: `ls` on every path and `git grep -n` on every test name the new text names
- [x] 1.4 Terminology: `tr '\n' ' ' < docs/BACKLOG.md | grep -o "Owner ruling *2026-10-16: backlog" | wc -l` counts the eleven new entries and the four extensions (15); each new entry has IDs, Status, Finding and impact, a Reproducer or Evidence, Proposed direction and Source change
- [x] 1.5 Coverage: `grep -n` per brief ID finds each pending item once; P1, P2, P3, A5 and R2-A2 appear only in the non-goals
- [x] 1.6 Privacy: the diff names `private_test_data/device-probe-2026-10-16/README.md` by path and quotes no `private_test_data` content; every value is synthetic
- [x] 1.7 Rendered output: `pre-commit run markdownlint --files docs/BACKLOG.md changelog.d/+backlog-open-findings.doc.md` passes

## 2. Change

- [x] 2.1 Eleven new entries in `docs/BACKLOG.md` after YAML-BREAKS-001
- [x] 2.2 YAML-BREAKS-001, DEVICE-EVIDENCE, MAKEOVER-19 and XML-INPUT extended
- [x] 2.3 Changelog fragment `changelog.d/+backlog-open-findings.doc.md`

## 3. Review and evidence

- [x] 3.1 Fresh isolated review recorded in `review.md`
- [x] 3.2 One full checkpoint passes: `uv run --locked --group dev --with griffe --with tach --with towncrier --with vulture agent-ready check --set full`
- [x] 3.3 Capture `metrics.md` and `metrics.json` for the immutable base and head
- [ ] 3.4 Archive, patch bump, merge and tag without pushing

## Evidence

- Baseline at 716a9d1: `mkdocs build --strict` exit 1, 48 warnings, all `BACKLOG.md` links outside `docs/` (`private_test_data/makeover-work/backlog-open-findings/mkdocs-base.txt`); reproducers in `probes-716a9d1.txt` beside it. The new entries do not exist yet, so 1.4 and 1.5 find nothing.
- 2.1 to 2.3 at 30368ba: eleven entries RELATIVE-TAGS-001 to VERB-PREFIX-001 after YAML-BREAKS-001; one bullet each in YAML-BREAKS-001, DEVICE-EVIDENCE, MAKEOVER-19 (B2 fits its "a fix can report success without mutation"), XML-INPUT (it owns XML input; XML-QUALIFICATION owns the device matrix); the fragment.
- 1.1 at 30368ba: exit 1, 63 warnings; `diff` against the baseline adds 15, every one `Doc file 'BACKLOG.md' contains a link '../openspec/changes/archive/2026-10-16-{own-crash-fixes,device-validation}/review.md'`; `ls` finds both targets; no warning names another file; the new `guide/validation.md#xml` link resolves (`id="xml"` in the built page). Output: `mkdocs-head.txt`.
- 1.2 at 30368ba: `probes-head.txt` equals `probes-716a9d1.txt` except the HEAD line; each result matches its entry.
- 1.3 at 30368ba: `ls` finds every repository path the diff names (21 paths); `pytest --collect-only` collects all ten cited test node IDs (50 tests, no error); `git grep` finds `_message`, `_property_names`, `_takes_one_value`, `_UNDOCUMENTED`, `deactivate-inside-an-entry-key` and `junoscfg.display.artifacts_dir`.
- 1.4 at 30368ba: 15; the per-entry field check finds every field once in each of the eleven entries.
- 1.5 at 30368ba: own-crash-fixes SC1, A1, A2, A3, C3, SC3, TC7 and device-validation A3, SC2, R2-A1, R2-A3, SC3, SC1, A7, D4, P4, D1, D5, B1, B2, B3 each appear once (slug-qualified); D2 and D3 each in their entry; P1, P2, P3, A5 and R2-A2 appear nowhere in the diff.
- 1.6 at 30368ba: the only `private_test_data` path in the diff is the probe README (eight IDs lines); no file content is quoted; values are synthetic (`r1`, `sw1`, `a.example`, `64496:1`, `ge-0/0/x`); the JVD names `ap1_mx304`, `mdr1_acx7509` and `GR-EDGE-INTF-MH` are already in tracked files.
- 1.7 at 30368ba: markdownlint passed on both files (pre-commit, also in the commit hook).
- Pre-review full checkpoint at 7d95e00: canonical command, "every check passed". The schema-25.2 tiers were selected ("audited execution boundary missing or changed" in a fresh worktree) and passed after `tools.schema_verification prepare` with the three dumps as physical files (hard links) in the worktree's `private_test_data/schemas/`. Earlier attempts stopped at the expensive tiers: runtime unprepared, then the symlinked dumps refused ("path escapes application"). Console: `private_test_data/makeover-work/backlog-open-findings/full-check-3.console.txt`. Task 3.2 stays open for the canonical run before merge.
- 3.1: Reviewer verdict Merge after fixes on `3ec85f0...d97390d` (`review.md`); B1 and A1 to A4 fixed in the review-fix commit; A5 recorded as a pending owner decision. After the fixes: markdownlint passes, the strict MkDocs warnings are unchanged (63, same kind), the five-position key probe repeats A2's result.
- 3.2 at 284dafc: canonical command, "every check passed", 2 min 45 s (schema-25.2 tiers selected and passed). Console: `private_test_data/makeover-work/backlog-open-findings/full-check-4.txt`.
- 3.3: `agent-ready metrics backlog-open-findings --base-sha 3ec85f0… --head-sha 284dafc…` (full IDs in `metrics.json`); base 3ec85f0 is the activation commit, so the diff holds only this change.
