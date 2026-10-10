## 1. Verification

- [x] 1.1 Acceptance tests: `TestXmlAndStructuredInputAgreeOnTheIr::test_an_inactive_leaf_reaches_one_ir` and `::test_an_inactive_unit_and_leaf_reach_one_ir` (XML, JSON, set, structured), `tests/test_to_yaml.py::TestInactiveLeaf` (whole and partly inactive leaf-list, presence flag), `tests/test_cli.py::TestInactiveXmlLeaf`; all five fail before the fix, and only the XML door differs.
- [x] 1.2 Independent Test/Challenge on these tests, run with change B's at the end (owner answer 3): `test-challenge.md`; findings and interim actions in `review.md`.

## 2. Change

- [x] 2.1 `src/junoscfg/display/to_yaml.py`: an inactive leaf is its plain value plus the sibling `@<name>`; a leaf-list tagged on every value takes one `@<name>`; a partly tagged one raises `ValueError`.
- [x] 2.2 Patch bump to 0.15.1 in `pyproject.toml`, `src/junoscfg/__init__.py`, `tests/test_cli.py`; changelog fragment.

## 3. Review and evidence

- [x] 3.1 Complete the risk-required fresh isolated review, or record why the assurance policy does not require it: fresh Reviewer (`review.md`), two re-reviews; verdict mergeable at 406137f.

Pre-review checkpoint: `uv run --locked --group dev --with griffe --with tach --with towncrier --with vulture agent-ready check --set full` at 406137f: every check passed, 1,937 passed / 45 skipped / 3 xfailed.
- [x] 3.2 Capture `metrics.md` and `metrics.json` for the immutable base and code head.
- [x] 3.3 Finalizer completes bounded spec application, evidence, and archive housekeeping without product edits.
