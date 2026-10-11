<!-- Complete at the end of phase 2. Later instructions or evidence require a delta consistency check before affected work continues. -->

## Resolved instructions

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
