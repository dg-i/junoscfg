## 1. Verification

- [x] 1.1 Add acceptance tests for tooling/data inputs, deleted targets, hook invocation and selection deduplication. Before implementation, `uv run --locked --group dev pytest -q tests/tooling/test_affected_tests.py` reported 12 failed, 26 passed in 0.76s; failures exactly cover the missing requirements. Evidence: /tmp/selection-red.log.

## 2. Change

- [x] 2.1 Repair selection and hook; update test contract and changelog. Focused command `uv run --locked --group dev pytest -q tests/tooling/test_affected_tests.py`: 38 passed in 0.71s (/tmp/selection-green.log). Codemap check and requirement reconciliation pass.

## 3. Review and evidence

- [x] 3.0 Parent coordinates activation, readiness and canonical full checkpoint at committed candidate before review.

- [x] 3.1 Complete the risk-required fresh isolated review, or record why the assurance policy does not require it.
- [ ] 3.2 Capture `metrics.md` and `metrics.json` for the immutable base and code head.
- [ ] 3.3 Finalizer completes bounded spec application, evidence, and archive housekeeping without product edits.

## Checkpoint

Implementation and fresh review approved. Canonical full checkpoint passed at 51e91f69d9ef5f3fe25527bb904a77cf0c4bd1eb; 10439 passed, 13 skipped, 20 xfailed. Main specification applied exactly from reviewed delta. Next: native metrics and archive-ready handoff.
