## 1. Verification

- [x] 1.1 Run `tests/test_to_yaml.py`, `tests/test_convert_roundtrip.py`, and
  the JSON-to-YAML integration tests before implementation.
- [x] 1.2 Confirm both public XML-output doors raise `NotImplementedError` and
  public JSON-to-YAML conversion remains lossless.

## 2. Change

- [x] 2.1 Remove `json_to_yaml()` and route its useful characterization tests
  through `convert_config()`.
- [x] 2.2 Remove `xml_output.py` and preserve the package-door exception in
  `convert.output.from_dict()`.
- [x] 2.3 Remove stale module documentation, record the owner-approved
  production-consumer compatibility boundary, ban the retired imports, and add
  the changelog fragment.

  Evidence after review correction: 166 focused conversion tests passed. The
  production collection's 33 tests passed against this checkout, whose four
  top-level imports this change preserves.
- [x] 2.4 Run focused tests and the locked full repository check.

  Passed at `e8a7e3a`: 1,627 repository tests passed and 72 skipped; all 33
  production collection tests and the explicit-base lane gate also passed.

## 3. Review and evidence

- [x] 3.1 Complete the fresh-session review and write `review.md`.
- [ ] 3.2 Capture `metrics.md` and `metrics.json` for the immutable base and code head.
