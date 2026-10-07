## 1. Tests

- [x] 1.1 The six existing `test_password_rule.py` failures become passes on
  3.10, 3.11 and 3.12 without being touched. They were always correct; the code
  was wrong.
- [x] 1.2 Add `TestCryptIndependence`: no `crypt` import may reappear anywhere
  in the package, and the transform output is byte-for-byte fixed for a fixed
  salt.

## 2. Implementation

- [x] 2.1 Delete the `crypt` branch from `_make_crypt_hash()`; the deterministic
  body becomes the only path.
- [x] 2.2 Revert `datetime.UTC` to `timezone.utc` in `artifact_builder.py`.
- [x] 2.3 `requires-python = ">=3.10"`; classifiers list 3.10 to 3.14. `ruff
  target-version` and `mypy python_version` follow, the first via
  `agent-ready render levers`, which derives it.
- [x] 2.4 Scope `agent-ready-checks` to `python_version >= '3.11'` in the dev
  group so development tooling stops setting the published floor.
- [x] 2.5 Drop `[tool.deptry.per_rule_ignores] DEP001 = ["crypt"]`, now unneeded.
- [x] 2.6 Bump to 0.6.1 and add the changelog fragment.

## 3. Verification

- [x] 3.1 Full suite on 3.10, 3.11, 3.12, 3.13 and 3.14: **1397 passed** on each.
- [x] 3.2 Anonymizer output identical on all five interpreters, verified by
  hashing the result of a three-password fixture.
