<!-- Complete at the end of phase 2. Later instructions or evidence require a delta consistency check before affected work continues. -->

## Historical freeze (source 5ae3ad7; current execution baseline below)

- Standard lane, type `bug`, zone `conversion` (yellow), domains `conversion` and `validation` (C7: cross-domain, high-risk floor).
- Owner intake 2026-10-11 (`builder-brief.md`): unattended, no questions (C1), no version bump on the branch, never push, nothing from `private_test_data/` in a tracked file.
- The spec `conversion/diagnostics` and `docs/guide/cli.md` already promise that field-validation warnings are reported; the code is the defect (C2).
- The pinned message moves to the reworded one; severity stays warning (C3).
- No commit-check option (C4); no field validation inside the schema-validation doors (C5).
- No path shared with a live Builder (C6): `docs/architecture/developer-guide.md` and `docs/guide/cli.md` are #7's and stay untouched (cli.md already says warnings are printed); `files.txt` checked against #7, #8, #9 after phase 2: no overlap.

## Requirements

- MODIFIED `conversion/diagnostics` "The caller owns diagnostic rendering": warnings are carried whether or not errors were found; `strict` raises on errors only.
- ADDED `conversion/diagnostics` "A missing mandatory statement is reported as a commit-time warning".
- Delta: `openspec/changes/diagnostics-load-vs-commit/specs/conversion/diagnostics/spec.md`.

## Evidence

- Base `40173ba`. `private_test_data/makeover-work/diagnostics-load-vs-commit/repro.py` (output `repro-base.out`): `set access profile PROF-1 radius-server 192.168.50.10 timeout 10` alone gives no diagnostic, strict or not, and `junoscfg convert` prints nothing on stderr (with `--strict` too); with `set chassis dump-on-panic` added, the result carries the UNPLACED error and `Missing mandatory field 'secret'`. Owning code: `src/junoscfg/convert/__init__.py::_convert`, `if not result.valid:` guards `(*result.errors, *result.warnings)`.
- `src/junoscfg/convert/field_validator.py::_check_mandatory` is the only producer of `FieldValidationResult.warnings`; the path it reports is built of schema names only (`_walk` appends a key only after `schema_child` places it), so in an anonymized run the warning quotes no value.
- Device evidence for the load half: `tests/data/device/synthetic/vmx-23.2R2-S7.5/junoscfg-oracle.set.gz` (vMX, 23.2R2-S7.5) and `tests/data/device/synthetic/qfx5120-25.2R2-S1.5/junoscfg-oracle.set.gz` (QFX5120, 25.2R2-S1.5) hold `set access profile PROF-1 radius-server 192.168.50.10 timeout 10` with no `secret` for that profile's server; `tests/data/device/synthetic/vmx-23.2R2-S7.5/synthetic-probes.set.gz` (vMX, 23.2R2-S7.5) holds `set access radius-server 192.168.50.10` alone. Captures are loaded with `load override` and never committed (`tests/data/device/README.md`). The commit half rests on the schema model's `mandatory` flag (`m` in the tree), the next rank of the evidence hierarchy.
- Blast radius (`probe_mandatory.py`, output `probe_mandatory.out`, base): mandatory warnings per rendering: both oracle captures `access.profile.radius-server.secret` x1 in all four renderings, plus `interfaces.interface-range.member-range.to` x2 in their JSON renderings (the JSON reader keeps `end-range`: NEW-B8, row 13, not this change); `synthetic-probes` `event-options.policy.then` and `access.radius-server.secret` in all four; JVD `mdr1_acx7509` `groups.interfaces.hold-time.up` in all four; none in `bng1_mx304` or `services-leaf1_qfx5130-48c`. Of these renderings only `synthetic-probes` (4) and `mdr1_acx7509.xml` are valid today, so only their conversions gain diagnostics; every rendering with a mandatory warning changes its message text.
- Base comparison recorded from the base tree at `40173ba`: `base.json` (96 conversions), `base-anon.json` (1,152 with each rule and all rules); head is compared in phase 5.
- Observation, not changed here: the JVD `mdr1_acx7509` warning sits inside `groups GR-EDGE-INTF-MH interfaces <*> hold-time down 0` (a group whose `<*>` entry has `down` and no `up`). Whether Junos checks a mandatory statement in a group as written or only in the configuration the group is inherited into is a device question; the wording "required at commit" is the schema model's and is kept for groups too.

## Non-goals

- A commit-check option or strict level escalating mandatory warnings.
- Field validation inside `validate_set`, `validate_config` or `junoscfg convert -v`.
- Mandatory checks inside `groups` (device question above).
- The JSON reader's `end-range` alias (NEW-B8, row 13).

## Acceptance criteria

- `tests/unit/convert/test_conversion_diagnostics.py::TestAFieldWarningNeedsNoError::test_every_door_reports_it` (set, structured, JSON, YAML, XML x strict off and on; through `convert_config_result` and `pipeline_result`), `::test_an_error_beside_it_changes_nothing`, `::test_the_cli_prints_it` (`junoscfg convert` with and without `--strict`: stderr carries the warning, exit 0): each fails on `40173ba`.
- `tests/unit/convert/test_field_validator.py::TestMandatoryValidation::test_the_message_names_the_commit_boundary` fails on `40173ba`; the pin `RADIUS_SECRET` of `TestTheExampleConfigurationValidates` follows the new wording.
- Device checks 2 to 5 of the how-to stay green; the before/after comparison: every difference is a new or reworded mandatory warning (DEV-V3, NEW-B7), output unchanged.
- Independent Test/Challenge work after phase 4 (STOP-T) and a fresh Reviewer after phase 5 (STOP-R), required by the high-risk floor.

## Performance expectations

None, because the validation already runs; only which of its results are carried changes.

## Outstanding decisions

None, because all material decisions are resolved (C1–C7); the group question is a non-goal recorded above.

## Execution and checkpoint

- Assurance preference: economy
- Risk floor: high (cross-domain: conversion and validation, instruction-integrity C7)
- Roles required: Builder; independent Test/Challenge (STOP-T); fresh Reviewer at least as capable as the Builder (STOP-R); Finalizer
- Resume point: phase 4 (phase 3 not required for type `bug`); last valid evidence: this freeze and `repro-base.out`

## Delta log

<!-- Append source, change, consistency result, invalidated work, and rerun required. -->

- Freeze established at the phase-2 commit on branch `change/diagnostics-load-vs-commit` (base `40173ba`); approved under the owner's unattended-run instruction of 2026-10-11.
- Phase 4, 2026-10-11: the acceptance tests of the "warning without an error" scenario use the vMX's own line `set access radius-server 192.168.50.10` (`synthetic-probes.set.gz`) instead of the oracle's `access profile PROF-1 radius-server 192.168.50.10 timeout 10`: every writer drops `timeout` there (`set ... radius-server 192.168.50.10 10`), the mission's device-oracle defect 3, owned by ledger row 10 (DEV-3). The field-validator test keeps the oracle line (it asserts no output). Requirements and criteria unchanged; spec scenario text updated to name the line. No rerun beyond the phase-4 tests.

## Current execution baseline — migration 2026-10-12

- Base `13b2cc73fd42fb44d1c69121b73d9b9fa61677cd`, template/check revisions and effective amendments as current preflight. Historical 96/1,152 comparisons above remain historical, never new-base proof. Current-base comparisons and red tests replace execution evidence before STOP-T.
- Approved qualified warning: `Missing mandatory field 'secret': may be required at commit; the configuration loads without it`. Warning severity stays warning; warnings propagate regardless of errors; strict raises only on errors; output/stdout and exit behavior unchanged.
- P15 owner counterevidence: unapplied down-only hold-time group commits successfully; applying it without up fails; up0 succeeds. This invalidates unconditional wording, not mandatory evaluation. Group evaluation, commit-check feature, validation doors and JSON end-range aliases remain non-goals. Approved tests change the qualified wording only.
- Named acceptance: `TestAFieldWarningNeedsNoError::{test_every_door_reports_it,test_an_error_beside_it_changes_nothing,test_the_cli_prints_it}` in `tests/unit/convert/test_conversion_diagnostics.py`; `TestMandatoryValidation::test_the_message_names_the_commit_boundary` in `tests/unit/convert/test_field_validator.py`. Oracle warning pin follows qualified text without weakened assertions.
- Exact planned product paths/dependencies/changelog/generated records are in `.openspec.yaml`; no added dependencies or generated-record edits. Reviewed main spec is applied only after review; change remains parked during migration.
- Current verification: focused named tests (zero collection errors), device/anonymizer base comparisons before runtime edits; after implementation owning tests/device checks, supported fast plus configured ordinary coverage command. No canonical full or real schema now; final 25.2R2-S1.5 schema deferred to whole makeover end.
- Risk high (cross-domain); assurance economy; roles independent Test/Challenge and fresh Reviewer at least as capable as Builder. Resume STOP-T awaiting root admission/independent challenge. No material outstanding owner decision.
- Delta consistency: current base/instructions invalidate old execution proof and unconditional warning text. Intent, severity, strict/output criteria and non-goals remain; rerun current codemap, gates, named acceptance and baseline comparisons. Historical source/bundle/logs retained.
- Actual current-base STOP-T evidence: all 14 named acceptance cases failed, zero collection/errors/skips (`current-red.xml`); current baseline 96 plain conversions and 1,152 anonymizer combinations recorded before runtime changes (`current-base.json`, `current-base-anon.json`). Provenance/hashes in private `migration-evidence.json`; product `src/` diff against exact base is empty. Historical records remain unchanged.

## Admission delta — 2026-10-12

Independent `roles/test-challenge.md` finds STOP-T adequate, with no blocking challenge. Root accepts exact criteria without expansion in private `codex-resumption/diagnostics-root-admission-ruling.json`; independent actual 14 red and scoped preservation probes are in private `independent-tc-20261012/`. Root installed diagnostics-only admission at checkpoint `9f03046ea0c17811025ce46b29bd576c84ba245d`, assessment SHA-256 `d3a63feeb6d51b6a717f9bf0463dc233b012f7ea807728032cf503f23567ba4c`; local/shared inventory parse equal. Root master operator-record commit `0e65a5f` changes no product base. Builder preserves this record and declares its exact operator path alongside the unchanged eight product paths for the planned-path gate. No other branch/change is admitted. Metadata now ready; this is execution admission, not success evidence. No criteria/test corrections or historical evidence invalidation. Next incomplete phase: implementation, then supported fast/ordinary verification and independent final-source preservation probes, then fresh review.

## Implementation evidence — before review

Owning focused tests: 177 passed, one existing strict xfail. Required device checks: 4,456 passed, five existing strict xfails. Current-base comparisons: 64/96 plain and 768/1,152 anonymizer records change diagnostics only; every output and exception class is identical. The only changes are newly propagated missing-mandatory warnings or the exact approved qualified suffix. Private `implementation-comparison.json` contains exhaustive key-level assertions, counts and SHA bindings; raw/XML and head records are retained. No group/alias/validation-door expansion. Product implementation complete; next phase verification plus independent final-source controls, then STOP-R/fresh review. Contract compacted to its enforced 21-line reorganization target without losing any checked invariant/precedent; duplicate interface metadata remains owned by code/tach.

## Operator-only ancestry delta — 2026-10-12

Current comparison base is `0e65a5f8a4a7fc2d2199e0f2398aceb5f822690d`, replacing the runtime-identical `13b2cc73` base. Root's only base delta is the exact operator assessment already preserved by this branch. Direct Git object equality proves source, tests, capture, lock/config, tools and installed skill inputs unchanged between bases; implemented source/tests/docs/fragment likewise unchanged across rebase from `4dd292c` to `5fb8b278`. Private `operator-only-rebase-proof.json` binds every equality. Thus the retained 96/1,152 base/head comparisons and focused/device results remain applicable, with original execution identities preserved. Earlier fast on `4dd292c` passed before this delta arrived; current fast/ordinary evidence is still required before STOP-R. No acceptance/scope change, no new source test rerun solely for operator ancestry, and no real schemas/canonical full. Next independent final-source controls and supported serial fast/ordinary verification.
