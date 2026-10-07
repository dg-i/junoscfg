## 1. Tests

- [x] 1.1 The change is itself test infrastructure. Verified three ways:
  discovery by `private_test_data/*.xsd`, discovery by `JUNOSCFG_XSD_SOURCE`,
  and the no-XSD path running 1413 tests with a warning instead of skipping
  1414.
- [x] 1.2 Verified regeneration end to end in a throwaway copy of the tree, so
  the real 14 MB artifacts were never overwritten by a toy schema.

## 2. Implementation

- [x] 2.1 Add `find_xsd_source()`: environment variable, then the newest
  `*.xsd` in `private_test_data/`.
- [x] 2.2 Replace `pytest.skip()` with `warnings.warn()` so the suite still
  runs, and say in the message what to do.
- [x] 2.3 Document the home and the capture command in the directory's README.
