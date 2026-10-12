## 1. Verification

- [x] 1.1 Add acceptance tests for tooling/data inputs, deleted targets, hook invocation and selection deduplication. Before implementation, `uv run --locked --group dev pytest -q tests/tooling/test_affected_tests.py` reported 12 failed, 26 passed in 0.76s; failures exactly cover the missing requirements. Evidence: /tmp/selection-red.log.

## 2. Change

- [ ] 2.1 Repair selection and hook; update test contract and changelog; pass focused tests.
- [ ] 2.2 Parent coordinates activation, readiness and canonical full checkpoint at committed candidate before review.

## 3. Review and evidence

- [ ] 3.1 Complete the risk-required fresh isolated review, or record why the assurance policy does not require it.
- [ ] 3.2 Capture `metrics.md` and `metrics.json` for the immutable base and code head.
- [ ] 3.3 Finalizer completes bounded spec application, evidence, and archive housekeeping without product edits.

## Checkpoint

Phase 4 complete. Owner's approved plan covers acceptance criteria; independent challenge omitted under frozen economy/normal-risk policy. Phase 5 next. The expected-red test checkpoint skips only affected-tests hook; all other commit hooks run, and phase 5 reruns focused tests and full checkpoint.
