## 1. Verification

- [x] 1.1 Acceptance tests for both deltas written before implementation (catalogue rows and writer, yaml-new = JSON laws, migration, device captures, reader/writer units, round-trip property, format table, CLI convert/audit/help, validation doors, anonymized messages); observed failing before implementation.
- [ ] 1.2 Independent Test/Challenge (high risk floor) challenges criteria and tests; findings recorded in review.md.

## 2. Change

- [ ] 2.1 Shared Junos JSON object stages in json_output/json_input; yaml-new reader and writer beside them; format table; dispatch through it; Format.YAML_NEW; validation door; CLI help.
- [ ] 2.2 Docs: user guide (yaml-new, migration, planned rename), API pages, README, CLI reference, ARCHITECTURE.md, convert contract, changelog fragment, backlog disposition.
- [ ] 2.3 Evidence: yaml byte-identical to base (catalogue and device corpus comparison), device-evidence checks, full checkpoint.

## 3. Review and evidence

- [ ] 3.1 Complete the risk-required fresh isolated review, or record why the assurance policy does not require it.
- [ ] 3.2 Capture `metrics.md` and `metrics.json` for the immutable base and code head.
- [ ] 3.3 Finalizer completes bounded spec application, evidence, and archive housekeeping without product edits.
