## 1. Verification

- [x] 1.1 Add the specified acceptance test proving the renderer receives the
  filtered IR for wrapped, relative, and missing paths.
- [x] 1.2 Run it before implementation and confirm it fails on the missing
  pipeline path API.

## 2. Change

- [x] 2.1 Filter the IR inside `pipeline()` before `from_dict()`.
- [x] 2.2 Pass `convert_config()` path options into the pipeline and remove its
  rendered-output filter dispatcher.
- [x] 2.3 Update contracts, API documentation, and changelog.
- [x] 2.4 Run focused tests and the locked full repository check.
  Checkpoint: `a4324d6` — 1,609 passed, 18 skipped; every check passed.

## 3. Review and evidence

- [x] 3.1 Complete the fresh-session review and write `review.md`.
- [x] 3.2 Capture `metrics.md` and `metrics.json` for the immutable base and code head.
