## 1. Verification

- [x] 1.1 Regression test `tests/unit/convert/test_field_validator.py::TestPatternValidation::test_a_literal_bracket_in_a_posix_bracket_expression`: it fails at the merge base 50b0a10 on its warning assertion and passes at a2edf23 (`agent-ready lane --base master` exit 0). Evidence: all 263 shipped patterns keep their `re` program, and none warns. Device-evidence checks: 3,664 passed, 5 xfailed. Before/after: 0 of 96 conversions differ. Base stderr carries the FutureWarning once; head stderr has none (PROC-F1).

## 2. Change

- [x] 2.1 `_posix_to_python_re` translates each bracket expression as a whole: a POSIX class becomes its ranges and a literal `[` is escaped (f84532d, a2edf23). Towncrier fragment `changelog.d/+posix-bracket-escape.bugfix.md`; no version bump (the version is set at merge). Caps: 2 files, 30 lines.
- [x] 2.2 Full check at a2edf23: every check passed. Tests: 7,559 passed, 37 skipped, 18 xfailed. Coverage 92.95 %.

## 3. Review and evidence

- [x] 3.1 Complete the risk-required fresh isolated review, or record why the assurance policy does not require it. The lightweight fresh-agent review the orchestrator required (C2) returned APPROVE. F1 and F2 were applied to the proposal as records only, and F3 was deferred to ledger follow-up T5 (`review.md`).
- [x] 3.2 Capture `metrics.md` and `metrics.json` for the immutable base and code head.
- [ ] 3.3 Finalizer completes bounded spec application, evidence, and archive housekeeping without product edits.
