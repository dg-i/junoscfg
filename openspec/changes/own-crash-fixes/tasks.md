## 1. Verification

- [ ] 1.1 Regression tests written before implementation and observed failing at base for the defect each pins (red run: `private_test_data/makeover-work/own-crash-fixes/red-run.txt`); guards of unchanged behaviour (relative leaf output, tagged entry and container, keys under a meta key) pass at base and head.
- [ ] 1.2 Independent Test/Challenge (high risk floor); findings recorded in review.md and resolved.

## 2. Change

- [ ] 2.1 Key rule: `find_non_json_value` refuses a key that is not a string whatever `scalars`; the `yaml` reader and `yaml` validation refuse it with yaml-new's wording.
- [ ] 2.2 JSON depth: the JSON reader refuses a value past 64 levels through `find_non_json_value`, labelled JSON.
- [ ] 2.3 Leaf tags: `display.filter_dict_by_path` keeps the selected key's sibling annotation in an absolute selection.
- [ ] 2.4 Records: contracts, decision 2026-10-15-yaml-nests-at-most-64-levels, ARCHITECTURE.md, guides, API page, changelog fragment.
- [ ] 2.5 Evidence: depth matrix and selection probe at head against base; performance of the JSON reader on the largest capture.
- [ ] 2.6 Canonical full checkpoint on a committed snapshot.

## 3. Review and evidence

- [ ] 3.1 Complete the risk-required fresh isolated review, or record why the assurance policy does not require it.
- [ ] 3.2 Capture `metrics.md` and `metrics.json` for the immutable base and code head.
- [ ] 3.3 Finalizer completes bounded spec application, evidence, and archive housekeeping without product edits.
