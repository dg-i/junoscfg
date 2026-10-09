## 1. Verification

- [x] 1.1 Run `tests/test_to_yaml.py`, `tests/test_convert_roundtrip.py`, and
  the JSON-to-YAML integration tests before implementation.
- [x] 1.2 Confirm both public XML-output doors raise `NotImplementedError` and
  public JSON-to-YAML conversion remains lossless.

## 2. Change

- [ ] 2.1 Remove `json_to_yaml()` and route its useful characterization tests
  through `convert_config()`.
- [ ] 2.2 Remove `xml_output.py` and preserve the package-door exception in
  `convert.output.from_dict()`.
- [ ] 2.3 Remove stale module documentation and add the changelog fragment.
- [ ] 2.4 Run focused tests and the locked full repository check.

## 3. Review and evidence

- [ ] 3.1 Complete the fresh-session review and write `review.md`.
- [ ] 3.2 Capture `metrics.md` and `metrics.json` for the immutable base and code head.
