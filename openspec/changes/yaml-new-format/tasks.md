## 1. Verification

- [x] 1.1 Acceptance tests for both deltas written before implementation (catalogue rows and writer, yaml-new = JSON laws, migration, device captures, reader/writer units, round-trip property, format table, CLI convert/audit/help, validation doors, anonymized messages); observed failing before implementation.
- [x] 1.2 Independent Test/Challenge (high risk floor) challenges criteria and tests; findings recorded in review.md.

## 2. Change

- [x] 2.1 Shared Junos JSON object stages in json_output/json_input; yaml-new reader and writer beside them; format table; dispatch through it; Format.YAML_NEW; validation door; CLI help.
- [x] 2.2 Docs: user guide (yaml-new, migration, planned rename), API pages, README, CLI reference, ARCHITECTURE.md, convert contract, changelog fragment, backlog disposition.
- [x] 2.3 Evidence: yaml byte-identical to base (catalogue 1,936 conversions and device corpus 96, 0 differ); device-evidence checks pass in the suite; canonical full checkpoint recorded in review.md before review.

## 3. Review and evidence

- [x] 3.1 Complete the risk-required fresh isolated review, or record why the assurance policy does not require it. Fresh Reviewer: Changes required on c95e67f (R1–R3), correction review on a55c960 (N1 wording), Merge after 84aa719; review.md.
- [x] 3.2 Capture `metrics.md` and `metrics.json` for the immutable base and code head.
- [x] 3.3 Finalizer completes bounded spec application, evidence, and archive housekeeping without product edits.
