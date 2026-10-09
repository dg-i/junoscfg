## 1. Verification

- [x] 1.1 Run the existing `tests/test_convert_api.py` characterization suite,
  which covers every supported pair, identity normalization, XML-output
  rejection, validation, strict mode, anonymization, and path filtering.
- [x] 1.2 Confirm the focused suite passes unchanged before implementation.

## 2. Change

- [x] 2.1 Replace `_CONVERTERS` with an explicit supported-pair set and dispatch
  accepted pairs directly to `_pipeline_convert()`.
- [x] 2.2 Remove the twenty private format-pair wrapper functions without
  changing the public signature or supported-pair matrix.
- [x] 2.3 Run the focused conversion API and integration tests after the edit.
- [ ] 2.4 Run the locked full repository check.

## 3. Review and evidence

- [ ] 3.1 Complete the fresh-session review and write `review.md`.
- [ ] 3.2 Capture `metrics.md` and `metrics.json` for the immutable base and code head.
