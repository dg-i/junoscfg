## 1. Verification

- [x] 1.1 Add the specified acceptance test proving the renderer receives the
  filtered IR for wrapped, relative, and missing paths.
- [x] 1.2 Run it before implementation and confirm it fails on the missing
  pipeline path API.

## 2. Change

- [ ] 2.1 Filter the IR inside `pipeline()` before `from_dict()`.
- [ ] 2.2 Pass `convert_config()` path options into the pipeline and remove its
  rendered-output filter dispatcher.
- [ ] 2.3 Update contracts, API documentation, and changelog.
- [ ] 2.4 Run focused tests and the locked full repository check.

## 3. Review and evidence

- [ ] 3.1 Complete the fresh-session review and write `review.md`.
- [ ] 3.2 Capture `metrics.md` and `metrics.json` for the immutable base and code head.
