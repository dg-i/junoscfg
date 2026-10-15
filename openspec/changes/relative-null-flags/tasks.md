## 1. Verification

- [x] 1.1 Acceptance tests for the path-filtering delta written before implementation and observed failing at `ea18fab` (14 failed; purity rows pass there by design): every selection shape, annotations, scenario literals, set-input groups, anonymized, bare-selection writer purity.
- [x] 1.2 Independent Test/Challenge (high risk floor) challenges criteria and tests; findings TC1 to TC13 and S1 to S4 recorded and resolved in review.md.

## 2. Change

- [x] 2.1 `junos_json_object` spells a relative selection as the value under its last path key (one rule replacing the selected-`true` special case); `from_dict` docstring; changelog fragment. Mutations (no relative pass, no copy, name-first on mappings only, annotations normalized) each fail the tests.
- [x] 2.2 Evidence: device corpus 0 of 96 conversions differ (tools/compare_device_outputs.py); relative probe over the device JSON captures 20 of 1,002 selections mismatched absolute output at base, 0 at head (private_test_data/makeover-work/relative-null-flags/probe_relative.py).

## 3. Review and evidence

- [ ] 3.1 Complete the risk-required fresh isolated review, or record why the assurance policy does not require it.
- [ ] 3.2 Capture `metrics.md` and `metrics.json` for the immutable base and code head.
- [ ] 3.3 Finalizer completes bounded spec application, evidence, and archive housekeeping without product edits.
