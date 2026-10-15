## 1. Verification

- [x] 1.1 Regression tests written before implementation and observed failing at `1370b2c` and, after Test/Challenge, `7f9921c` (64 failed for the intended reasons): coercion of a selected mapping, list and leaf; hidden list names in set and structured (`interfaces`, `interfaces.interface`, `dynamic-tunnel`, `groups.group`); `groups` as the list of groups; selected lists in set and structured; `null` selected relative; annotation selections (`@`, `@leaf`) in json, yaml-new, set and structured; dotted keys at the end of a path and within it, the exact key first; the kept-statements key; writer purity under `below=`; `from_dict(wrap=False)`; anonymized rows; the device-corpus law (`TestRelativeSelections`, depth 4).
- [x] 1.2 Independent Test/Challenge (high risk floor); findings TC1 to TC11 and challenges SC1 to SC5 recorded in review.md and resolved.

## 2. Change

- [x] 2.1 Pipeline: `_path_keys` resolves a dotted path against the keys present (exact key first, the shortest join that resolves); a missing key gives no output, a `null` value is selected; every writer receives the IR along the path and, relative, `below=` the path's keys. Writers: json and yaml-new write the Junos JSON object's value at the path (`groups` steps over its unwrapped wrapper); yaml the IR's value; set and structured walk the absolute IR through `Below`, which strips `path_words` (hidden list names, annotation keys and `junoscfg:unplaced` have none) from every path; structured drops an empty path's statement and notes a dropped tag of the selected statement itself; set joins words without a trailing space. `from_dict(wrap=False)` unchanged.
- [x] 2.2 Records: spec delta, conversion and CLI guides, convert contract, changelog fragment.
- [x] 2.3 Evidence (private_test_data/makeover-work/relative-selections/): absolute output unchanged, device corpus 0 of 96 (tools/compare_device_outputs.py) and catalogue 0 of 2,435; the corpus law holds at depth 5 over every capture (575 selections, law5-head.txt); probe_all.py against display's text filters: json, yaml-new and yaml now equal the absolute value for all 2,875 selections (base: 2 annotation differences), the remaining set and structured differences are the text filters' own (hidden words, one-line blocks); ten mutations of the final code each fail the tests (mutations.txt).
- [x] 2.4 Canonical full checkpoint `uv run --locked --group dev --with griffe --with tach --with towncrier --with vulture agent-ready check --set full --base d3ed627` at HEAD `ab46c510f1433c8c5f22d27b5c48a37203099b85`: every check passed, exit 0, 350 s; suite 13,492 passed, 22 xfailed, 37 skipped (10 workers, 83 s); coverage 93.11 %; schema-25.2 qualification and generation selected by `src/junoscfg/convert/__init__.py`, both exit 0 (physical dumps, runtime prepared).

## 3. Review and evidence

- [ ] 3.1 Complete the risk-required fresh isolated review, or record why the assurance policy does not require it.
- [ ] 3.2 Capture `metrics.md` and `metrics.json` for the immutable base and code head.
- [ ] 3.3 Finalizer completes bounded spec application, evidence, and archive housekeeping without product edits.
