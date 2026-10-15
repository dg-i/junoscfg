## 1. Verification

- [x] 1.1 Acceptance tests for both deltas written before implementation and observed failing at `930e123` and, after Test/Challenge, `f74fbb4` (59 failed for the intended reasons: the old bounds, no ceiling, `RecursionError` in the `yaml` reader, the new keywords): reuse rows the old bounds refused, the 64/65 boundary in lists, mappings and flags, alias chains, 400 and 5,000 deep, cycles at every door (kernel, yaml-new reader, writer wrapped and bare, validator, `validate_config`, CLI convert and `-v`, audit, anonymized messages; the `yaml` reader through library, CLI, detected YAML and audit), meta-key content unwalked, a deep sibling refused, JSON input to yaml-new.
- [x] 1.2 Independent Test/Challenge (high risk floor) challenges criteria and tests; findings TC1 to TC8 and challenges SC1 to SC4 recorded in review.md and resolved.

## 2. Change

- [x] 2.1 Kernel: `find_non_json_value(data, *, scalars=True, unwalked=())` walks written out with no size bound, refuses a cycle and the first value past 64 path steps; `NonJsonValue.where`. Doors: yaml-new reader, writer, validator messages; `yaml` reader checks with `scalars=False` and its meta-key prefixes before the cleanup; `unshared` docstring.
- [x] 2.2 Records: both spec deltas, conversion and validation guides, API page, input and convert contracts, developer guide, ARCHITECTURE.md, decision record 2026-10-15-yaml-nests-at-most-64-levels superseding 2026-10-15-yaml-new-expands-aliases-within-a-bound, changelog fragment.
- [x] 2.3 Evidence (private_test_data/makeover-work/yaml-depth-ceiling/): device corpus 0 of 96 conversions differ (tools/compare_device_outputs.py); catalogue 0 of 2,435 (every shape x reader x writer, yaml and yaml-new writers included); device yaml and yaml-new round trip 0 of 240; door probe doors-base.txt vs doors-head.txt.

## 3. Review and evidence

- [ ] 3.1 Complete the risk-required fresh isolated review, or record why the assurance policy does not require it.
- [ ] 3.2 Capture `metrics.md` and `metrics.json` for the immutable base and code head.
- [ ] 3.3 Finalizer completes bounded spec application, evidence, and archive housekeeping without product edits.
