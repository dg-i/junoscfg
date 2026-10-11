## 1. Verification

- [x] 1.1 Regression test `tests/unit/audit/test_walker.py::TestAnEntryPathHoldsTheWholeKey::test_the_key_as_the_set_writer_writes_it`: fails at the merge base 87ac8f7 on its assertion, passes at cacbf73 (`agent-ready lane --base master` exit 0). Audit before/after over the 24 device renderings: occurrences differ in 16, rendered output in 0; head 194/194 changed entry paths equal a device `set`/`deactivate` line (110 after the pre-existing `rf_list` token), base 0/194.

## 2. Change

- [x] 2.1 `audit/walker.py` `_key_tokens` writes a keyworded key field's keyword (`key_is_positional`, the writer's rule) and a key choice's value (cacbf73). Towncrier fragment `changelog.d/+audit-key-keywords.bugfix.md`, reworded after review (F2); no version bump (the version is set at merge). Caps: 2 files, 30 lines.
- [x] 2.2 Full check at cacbf73: every check passed. Tests: 7,560 passed, 37 skipped, 18 xfailed.

## 3. Review and evidence

- [x] 3.1 Complete the risk-required fresh isolated review, or record why the assurance policy does not require it. The lightweight fresh-agent review the orchestrator required (C2) returned CHANGES REQUIRED, records only; F1 to F3 applied as records, F1 carried as NEW-R19 to follow-up 21b (`review.md`).
- [x] 3.2 Capture `metrics.md` and `metrics.json` for the immutable base and code head.
- [x] 3.3 Finalizer completes bounded spec application, evidence, and archive housekeeping without product edits.
