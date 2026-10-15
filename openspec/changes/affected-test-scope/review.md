Fresh isolated Reviewer (separate agent, Claude Opus, no Builder reasoning), base
6498ec9c1fbfc29f3100cafa13e3fc0d7f0b5313, head 5adc8ae73673d6cd8999d6032c50ced44f4aa420.
Executed in its own detached worktree; no writes to the reviewed tree.

## Findings

1. **F1 (binding) Deletion selects less than an edit; importers are lost.**
   Spec "a tool is deleted … SHALL retain conservative broad coverage", "WHEN a
   test module changes THEN … the test modules importing it"; freeze criterion
   unknown/deleted tools. `select()` falls back to `tests/tooling/` or the nearest
   test directory for a missing `.py`, and `tooling_importers()` drops imports of a
   missing module. Executed: editing `tests/corpus/test_schema_data.py` selects three
   tooling importers, deleting it selects only `tests/corpus/` + reader tests (the
   importers would fail at import while the hook passes); editing
   `tools/schema_dependencies.py` selects `tests/`, deleting it `tests/tooling/`;
   deleting `tools/schema_content_worker.py` selects `tests/tooling/` although the root
   conftest names it. Not a regression against base, but inside the frozen criteria.
2. **F2 (binding) Real-tree selector assertions escape graph-changing edits.**
   Contract "A changed reader, or a deleted tests/tools module, also selects the
   selector's own repository-reader assertions". The rule reads only the post-change
   graph and covers only `TestRepositoryFilesATestReadsReceiveCoverage`. Executed:
   removing the ci.yml read from `test_type_policy.py` selects only that file while
   `…test_a_file_a_test_reads_selects_that_test[.github/workflows/ci.yml-expected0]`
   fails; adding `import tools.compare_device_outputs` to `tests/unit/cli/test_cli.py`
   leaves `test_real_execution_consumers_are_selected[compare_device_outputs-expected3]`
   failing unselected.
3. **F3 (binding) Root pytest configuration selects only tooling.** Spec "project
   configuration … SHALL retain full-suite selection". Executed: `pytest.ini`,
   `tox.ini`, `setup.cfg` and a root `conftest.py` select only `tests/tooling/`, while
   `reuse_blocker()` already lists them as alternate pytest configuration.
4. **F4 (contract wording binding; detection non-binding)** "an unknown loader
   selects the full suite" is untrue: subprocess `-m tools.X` / `"tools/X.py"` strings,
   `pytest.importorskip`, computed reads under `tools/`, and anchored paths assigned
   to attributes are undetected. Executed with a probe module; no instance in the
   current tree.
5. **F5 (non-binding, proposed)** Untracked files under `tests/`, `src/`, `tools/` are
   unbound inputs to ordinary evidence reuse (identity hashes tracked files only).
   Not executed: reuse was unreachable in a fresh root.
6. **F6 (non-binding, residue)** After ef769eb, `.gitignore` comment,
   `.pre-commit-config.yaml` markdownlint exclude and `pyproject.toml`
   `caps-report-only` still name the retired `openspec-*` skills.

The fixture fix (5adc8ae) weakens nothing: `-c maintenance.auto=false` applies only to
the fixture's own commit; the trace regression fails without it and passes with it.
Updater commit bd6c8a8 is exact updater output; `ci.yml` is unchanged across the range.
Focused selector/execution tests: 121 passed in 2.09s; all 22 cited test IDs collect.

## Already provided

- F5: `agent_ready_checks.verification.tracked()`/`identity()` are the shared
  authority; a guard belongs in `reuse_blocker` or upstream, not a second cache.
- F1: `reader_selection()` already serves path keys and handles deleted tool paths.

## Specification challenges

### Deletion narrower than edit

- Artifact: `tools/affected_tests.CONTRACT.md` "Deleted/unmapped tooling modules …
  select all tooling tests"; spec requirement "Tooling and shared inputs receive coverage".
- Counterexample: executed, F1.
- User impact: a deletion commit passes its hook while importers fail at import.
- Proposed correction: deletion selects at least what the module selected while it
  existed (importers and readers), with broad fallback when unknown.
- Decision: Accepted by the Builder as within the approved criterion (conservative
  deletions); no owner change of promise. Corrected with regressions, see below.

### Real-tree assertions depend on the whole graph

- Artifact: contract sentence on reader assertions; spec "Repository files a test
  reads receive coverage".
- Counterexample: executed, F2.
- User impact: a hook passes while the selector's own real-tree assertions fail.
- Proposed correction: any tests/tools Python change, including removal of a read
  or import, selects every real-tree selector assertion.
- Decision: Accepted by the Builder within the approved criterion; corrected below.

## Verdict

Do not merge yet: fix F1, F2, F3 and the F4 contract wording, each with a regression
observed failing first. F4 detection, F5 and F6 may go to the backlog. After
corrections: focused selector tests plus the fast set; a full rerun because the
selector is runtime-relevant for the hook.

## Scope dispositions and follow-up evidence

Owner decision 2026-10-15 (supersedes the Reviewer's backlog suggestions): fix F1–F6
in this change; none goes to the backlog. Builder corrections and their evidence are
in the evidence-freeze delta log; the follow-up review below covers them.

- F1, F2, F3, F4 wording: inside the frozen outcome; binding before archive.
- F4 detection, F5: independent hardening without a current instance; backlog.
- F6: residue of the retirement commit; backlog.
- SELECT-SCAN-001 (package-wide scanners) confirmed pre-existing.
- Not checked by the Reviewer: historical timings (raw logs needed) and a successful
  ordinary reuse (unreachable in a fresh root); evidence gaps for 3.2, not blockers.
