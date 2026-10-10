## 1. Verification

- [x] 1.1 Baseline: `ledger-before.txt` (2,055 node ids on master 1972f21), `coverage-before.txt` (branch 90.60 %), timing 186 s (`pytest --durations`).
- [x] 1.2 The proof: `check_ledger.py` accounts for every baseline node (kept, mapped by `ledger/*.tsv`, or dropped with a reason); the coverage floor `fail_under = 90.60` in `pyproject.toml`; the owner waived the test gates for this change (2026-10-10).

## 2. Change

- [x] 2.1 Product: `display.build_from_artifact` and `forget_loaded_artifacts`; the set grammar and JSON/YAML schemas through them.
- [x] 2.2 pytest-cov, the `test` group, strict markers and config, the coverage gate in the full set.
- [x] 2.3 Layout: `tests/{unit,contract,corpus,tooling,support}`, `tests/CONTRACT.md`, `tests/support/paths.py`.
- [x] 2.4 Areas: display/input, convert readers, convert formats (format matrix), validate (every door, shipped artifacts), anonymize (every rule), audit/edityaml, cli, characterization.
- [x] 2.5 Doors: exports in convert, validate, anonymize, audit and edityaml; `tach.toml` expose; `tools/check_test_doors.py` and its exceptions.
- [x] 2.6 Workflow: `tools/affected_tests.py`, the pre-commit hooks, CI from the lock with the coverage gate, nightly corpus, publish after checks.
- [x] 2.7 Documents: AGENTS.md Verification and Version Management, the developer guide's Testing Architecture, work-with-agents, the bug-fix guide, ARCHITECTURE.md; test ids in specs and contracts rewritten from the ledger.
- [x] 2.8 Patch bump; changelog fragment.

## 3. Review and evidence

- [x] 3.1 Review: the owner chose a lightweight record without the phase gates; each area agent's report was reviewed by the coordinator before its commit.
- [ ] 3.2 Final full check and timings recorded below.
