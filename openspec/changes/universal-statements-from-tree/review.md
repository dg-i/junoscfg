## Findings

### Independent Test/Challenge (phase 4, STOP-T)

Report: `test-challenge.md` (fresh isolated role, at `b18c652` against base `dd7c8c4`). Rulings relayed by the orchestrator, with what the Builder did:

| Finding | Ruling | Disposition |
|---|---|---|
| 1 High: no test compares each door's universal statements with the device's own JSON; the JSON door's nested scalar | Accept; ARCH-C10 stays with change 13, pinned as a named carry-forward | `tests/corpus/test_device_renderings.py::TestEveryDoorReadsTheDevicesUniversalStatements::test_every_door_reads_the_devices_universal_statements` over every capture × conf, set, XML (GR-OMIT skipped for conf, class `omitted-curly`); `tests/unit/convert/test_convert_api.py::TestLeafListPromotion::test_a_nested_json_scalar_universal_leaf_list_is_a_list`, strict xfail naming change 13 |
| 2 High: the tripwire does not trip at runtime | Accept | `tests/unit/display/test_universal_statements.py::TestTheFloorIsForATreeThatDeclaresNone::test_conversion_never_answers_from_the_floor` poisons the floor and runs both catalogue rows through every reader, writer and strict validation (door exception in `tools/check_test_doors.py`, keyed to that file) |
| 3 High: `replace` rests on junoscfg's own output | No device evidence; keep the base's acceptance, mark the JSON/XML shape EVIDENCE_BLOCKED on P8, tag the test ids, record the specification challenge, add the consumer YAML test | `replace` cases carry `P8` in their ids (`...[replace-P8]`, `test_replace_is_clean_p8`); challenge S1 below; `TestApplyFlagsSpellingsAreKept::test_the_consumers_apply_flags_spelling_is_kept` |
| 4 High/Medium: the old scalar spelling is not pinned | Accept: read or reported, never dropped | `TestApplyFlagsSpellingsAreKept::test_the_old_scalar_spelling_is_not_lost` (top and `system` × JSON, YAML, XML); field validation reports a value on a container node (`'apply-flags' holding a value`) |
| 5 Medium: wrong helpers pass the helper tests | Accept all | `schema_child(system, "interfaces")` and `schema_child(None, "system")` are None; a fifth flagged `apply-x` and an unflagged `apply-flags`; `test_a_nodes_own_statement_wins_in_every_reader` (every door, a `system`-level `apply-macro` leaf); `test_the_tree_is_authoritative` covers the generator |
| 6 Medium: Group-H deletions covered for set output only | Pin the curly writer at the head (the same 96 lines) in a test or a measurement; wait for `base-jvd.json` before claiming C4 | measurement recorded in `evidence-freeze.md` and `metrics.md` |
| 7 Low: bare and doubled `apply-flags`; name-scan blind spots | Pin bare `set system apply-flags` as reported or rejected; leave `apply-flags omit replace` untested and ledgered; extend the scan to `startswith("apply-")` and f-strings | `test_an_apply_statement_is_rejected[apply-flags-needs-a-flag]`; the doubled form ledgered; the scan reads a prefix of a name and an f-string's literal part (`test_the_scan_sees_each_retired_reading`) |

### Fresh Reviewer (phase 6, STOP-R)

Pending.

## Specification challenges

### S1: `apply-flags replace` is modelled without device evidence

- Artifact: delta `specs/schema-pipeline/universal-statements/spec.md`, requirement "apply-flags is the container the device writes", and the floor in `src/junoscfg/display/constants.py`.
- Counterexample: proposed probe (P8 in `private_test_data/makeover-probes.md`), not executed. The only source of `apply-flags replace` is the downstream collection's example, which junoscfg itself generated (Test/Challenge finding 3). No capture shows that a device accepts `replace` or how it writes it in JSON or XML.
- User impact: if the device writes `replace` in some other shape, JSON and YAML output of a set or curly `apply-flags replace` would not load as written. If the device rejects `replace`, the grammar accepts a line that the device refuses. Both were already true on the base, which accepted it as a leaf value.
- Proposed correction: answer P8. Keep `replace` as a flag if the device prints it so; otherwise drop it from the fix and the floor, and reject it.
- Decision: Pending owner decision. Interim action: the base's acceptance is kept. `replace` is the second presence flag beside `omit`, so the grammar and the consumer's configuration keep validating. Its JSON/XML shape is EVIDENCE_BLOCKED on P8, and its tests carry `P8` in their ids, so they can be reverted alone (owner intake 2026-10-11: merge with recorded interim action).

## Verdict

Pending.
