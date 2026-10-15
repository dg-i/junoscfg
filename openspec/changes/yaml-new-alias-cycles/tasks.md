## 1. Verification

- [x] 1.1 Acceptance tests for both deltas written before implementation and observed failing at `87e14cd` (shared blocks, cycles, size and depth bounds with exact paths, counting rows, downstream sharing over every writer plain and anonymized, every door: kernel, reader, writer, validator, `validate_config`, CLI convert, `-v`, audit, anonymized messages); bomb rows guarded by a timer so an unbounded expansion fails instead of hanging.
- [x] 1.2 Independent Test/Challenge (high risk floor) challenges criteria and tests; findings TC1 to TC10 and challenges SC-A to SC-C recorded in review.md and resolved or pending the owner.

## 2. Change

- [x] 2.1 Kernel: `find_non_json_value` walks shared blocks written out, refuses a cycle and an alias past twice the parsed values or the parsed depth, returns `NonJsonValue`; tach expose. Reader reads written out (`junoscfg.convert.ir.unshared`); writer checks the IR before the object stage; object stage copies with `unshared`; validator message. Mutations (no size bound, 2P+1, no depth bound, global seen-set, containers only, innermost path, reader sharing, object-stage deepcopy) each fail the tests.
- [x] 2.2 Records of the alias policy: both specs (deltas), conversion and validation guides, API page, input and convert contracts, developer guide, ARCHITECTURE.md, decision record 2026-10-15-yaml-new-expands-aliases-within-a-bound; changelog fragment (additive); backlog entries YAML-DATE-001 (PO-3) and YAML-BREAKS-001 (PO-4).
- [x] 2.3 Evidence: device corpus 0 of 96 conversions differ (tools/compare_device_outputs.py); door probe base vs head in private_test_data/makeover-work/yaml-new-alias-cycles/doors-{base,head}.txt.

## 3. Review and evidence

- [ ] 3.1 Complete the risk-required fresh isolated review, or record why the assurance policy does not require it.
- [ ] 3.2 Capture `metrics.md` and `metrics.json` for the immutable base and code head.
- [ ] 3.3 Finalizer completes bounded spec application, evidence, and archive housekeeping without product edits.
