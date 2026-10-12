## 1. Verification

- [x] 1.1 Add acceptance tests for tooling/data inputs, deleted targets, hook invocation and selection deduplication. Before implementation, `uv run --locked --group dev pytest -q tests/tooling/test_affected_tests.py` reported 12 failed, 26 passed in 0.76s; failures exactly cover the missing requirements. Evidence: /tmp/selection-red.log.

## 2. Change

- [x] 2.1 Repair selection and hook; update test contract and changelog. Focused command `uv run --locked --group dev pytest -q tests/tooling/test_affected_tests.py`: 38 passed in 0.71s (/tmp/selection-green.log). Codemap check and requirement reconciliation pass.

## 3. Review and evidence

- [ ] 3.0 Parent coordinates activation, readiness and canonical full checkpoint at committed candidate before review.

- [ ] 3.1 Complete the risk-required fresh isolated review, or record why the assurance policy does not require it.
- [ ] 3.2 Capture `metrics.md` and `metrics.json` for the immutable base and code head.
- [ ] 3.3 Finalizer completes bounded spec application, evidence, and archive housekeeping without product edits.

## Checkpoint

Phase 5 implementation complete; next parent-coordinated readiness and canonical full checkpoint, then fresh isolated review. Expected-red checkpoint 0b2e8d3 skipped only affected-tests hook; all other hooks passed. Implementation commit runs all hooks normally.
