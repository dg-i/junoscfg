## 1. Verification

- [x] 1.1 Acceptance tests in `tests/unit/convert/test_convert_roundtrip.py::TestNoWriterChangesTheIrItIsGiven`: `test_a_hand_built_ir_is_left_unchanged` (four spellings x four writers; the four JSON parameters fail on the merge base `d1e804e`, the twelve others are the family's guard rows and pass on both sides) and `test_a_read_ir_is_left_unchanged` (every catalogue source, every writer in turn; the four sources whose IR holds a `{}` presence flag fail on the merge base).
- [ ] 1.2 Independent Test/Challenge on these tests (`balanced`, behavioural change): `test-challenge.md`; findings, rulings and interim actions in `review.md`.

## 2. Change

- [ ] 2.1 `src/junoscfg/convert/output/json_output.py`: `dict_to_json` normalizes its own copy of the IR; output unchanged, `_native_groups` included. `src/junoscfg/convert/CONTRACT.md`: the invariant and its test.
- [ ] 2.2 Changelog fragment; patch bump 0.16.1 in `pyproject.toml`, `src/junoscfg/__init__.py`, and `uv.lock` if required.

## 3. Review and evidence

- [ ] 3.1 Complete the risk-required fresh isolated review, or record why the assurance policy does not require it.
- [ ] 3.2 Capture `metrics.md` and `metrics.json` for the immutable base and code head.
- [ ] 3.3 Finalizer completes bounded spec application, evidence, and archive housekeeping without product edits.
