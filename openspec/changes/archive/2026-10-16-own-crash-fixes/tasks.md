## 1. Verification

- [x] 1.1 Regression tests written before implementation and observed failing at base for the defect each pins (`tc/red-full.txt` from `5c513a9`; final tests against base `red-run-2.txt`: 183 failed for their defects); guards (tagged entry and container, keys under a meta key, YAML scalar values, the `yaml` writer's keys) pass at base and head.
- [x] 1.2 Independent Test/Challenge (high risk floor); findings TC1 to TC10 and SC1 to SC4 recorded in review.md and resolved (SC1 pending owner decision with its interim action).

## 2. Change

- [x] 2.1 Key rule: `find_non_json_value` refuses a key that is not a string whatever `scalars`; the `yaml` reader and `yaml` validation refuse it with yaml-new's wording.
- [x] 2.2 Depth: the JSON and XML readers and JSON validation refuse a value past 64 levels through `find_non_json_value`, labelled JSON or XML.
- [x] 2.3 Leaf tags: `display.filter_dict_by_path` keeps the selected key's sibling annotation in an absolute selection.
- [x] 2.4 Records: contracts, decision 2026-10-15-yaml-nests-at-most-64-levels, ARCHITECTURE.md, guides, API page, changelog fragment.
- [x] 2.5 Evidence (`private_test_data/makeover-work/own-crash-fixes/`): `probe_selections.py` at head against base, 5,750 outputs: 25 absolute outputs differ, each adding exactly the last key's sibling annotation (21 object outputs verified by `verify_tag_only.py`), 2 relative set outputs (SC1); depth matrix (`depth-base.txt`, `depth-head2.txt`): JSON and XML refused with ValueError past 64 levels in every writer, no RecursionError; repeated XML refused (`xml-list-depth-head.txt`); reader cost on the largest capture (`perf.txt`): JSON `to_dict` 2.8 to 4.2 ms, XML 16 to 18 ms.

## 3. Review and evidence

- [x] 3.1 Complete the risk-required fresh isolated review, or record why the assurance policy does not require it. Fresh Reviewer: Merge after fixes on `8846937` (B1 binding, records; A1 to A6 advisory); resolved in `0cc3649`; review.md.
- [x] 3.2 Capture `metrics.md` and `metrics.json` for the immutable base and code head (`4dc114ee7dfb959e29a89d24897fce9443e18549`..`0cc36491ea3b6c1fdcd74b5b6454a4a4edf707bc`).
- [x] 3.3 Finalizer completes bounded spec application, evidence, and archive housekeeping without product edits. Main specs applied at `03626e7` before the merge `2593859`; metrics `3eef597`; archived with `--skip-specs`; released v0.28.23.
