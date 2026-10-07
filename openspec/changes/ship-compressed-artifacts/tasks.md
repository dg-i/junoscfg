## 1. Tests

- [x] 1.1 The compressed form is preferred, the plain one still found, a
  missing one is None.
- [x] 1.2 The writer compresses by suffix and leaves a plain name plain.
- [x] 1.3 A schema tree loads from either form.
- [x] 1.4 Every bundled artifact is gzipped, and the set stays under 6 MB — a
  plain file slipping back in is visible.
- [x] 1.5 Two seen to fail under mutation: not preferring `.gz`, and not
  compressing on write.

## 2. Implementation

- [x] 2.1 `find_artifact`, `read_artifact_text`, `open_artifact_write`.
- [x] 2.2 Seven readers and six writers routed through them.
- [x] 2.3 The shipped artifacts compressed in place.
- [x] 2.4 `tach.toml` expose list, which both gates demanded.

## 3. Verification

- [x] 3.1 `src/junoscfg` 38 MB to 5.2 MB; artifacts 34.5 MB to 2.1 MB.
- [x] 3.2 Structure tree loads in 0.19s; `convert` on the example 0.9s.
- [x] 3.3 A plain artifact directory still validates through `--artifacts`.
- [x] 3.4 Set, structured and JSON validation and conversion all unchanged on
  the shipped set. The 15 JSON field errors on `examples/router1.json` are
  identical at the previous commit, so not from this.
- [x] 3.5 1,497 tests pass, from 1,489. `tach check` clean.
- [x] 3.6 The Ansible collection's 33 tests pass, filters byte-identical to
  junoscfg 0.6.8.
