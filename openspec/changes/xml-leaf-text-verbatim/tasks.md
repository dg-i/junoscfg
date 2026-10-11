## 1. Verification

- [x] 1.1 Acceptance tests in `tests/unit/display/test_to_yaml.py::TestALeafKeepsItsText`: `test_spaces_around_a_value_are_kept` (a single leaf, a leaf list, an entry key), `test_whitespace_alone_is_a_value_only_where_the_tree_takes_one` (a value leaf takes `" "`; a pretty-printed flag, container and element outside the tree read as their empty spelling), `test_every_door_writes_the_devices_line` (`xml_to_dict`, `xml_to_yaml`, `convert_config` to JSON, YAML, set and structured, `junoscfg convert -i xml -e set`). All three fail on the merge base `13719d9`.
- [x] 1.2 Independent Test/Challenge: not run; `economy` below the high-risk floor omits it (evidence freeze, Execution and checkpoint).

## 2. Change

- [x] 2.1 `src/junoscfg/display/to_yaml.py` `_xml_leaf`: the text is the value as written; whitespace-only text is a value only on a tree value leaf.
- [x] 2.2 Changelog fragment `changelog.d/+xml-leaf-text-verbatim.bugfix.md`; no version bump (the orchestrator bumps at merge).
- [ ] 2.3 Sequenced by the orchestrator after change 8: remove class `xml-value-whitespace-lost` from `tools/device_differences.py` and regenerate `tests/data/device/known-differences.json` (serialized path).

## 3. Review and evidence

Pre-review checkpoint: `uv run --locked --group dev --with griffe --with tach --with towncrier --with vulture agent-ready check --set full` at 5f93b36: every step passed except the application tests, 7,561 passed / 37 skipped / 18 xfailed / 2 failed; the two failures are the device law for the two XML captures, the four `xml-value-whitespace-lost` lines "recorded but gone", closed by task 2.3.

- [x] 3.1 Complete the risk-required fresh isolated review, or record why the assurance policy does not require it: not required, `economy` below the high-risk floor (`review.md`).
- [ ] 3.2 Capture `metrics.md` and `metrics.json` for the immutable base and code head: captured for base 13719d9 and code head 5f93b36; recapture after task 2.3 moves the code head.
- [ ] 3.3 Finalizer completes bounded spec application, evidence, and archive housekeeping without product edits.
