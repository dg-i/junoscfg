## Findings

Fresh Reviewer: pending (dispatched by the coordinator after STOP-R).

## Already provided

The set reader's own meta-command walk existed; it moved, read only, into `junoscfg.display`
as `meta_target`, and both the reader and the validator use it. The tag notes reuse the
structured writer's note mechanism and the `Below` wrapper; the before/after comparison is
`tools/compare_device_outputs.py`.

## Specification challenges

### S-1: the conversion-hints delta claimed the grammar takes the `=`, `+` and `-` literals

- Artifact: `specs/schema-pipeline/conversion-hints/spec.md`; strict xfails at `4944ea0`.
- Counterexample: executed. At base `-v` refuses `then community = JUNOSCFG-C1` (device D2
  takes it) and accepts `then community eq_literal JUNOSCFG-C1`.
- User impact: a device line and junoscfg's own set output fail `-v`.
- Proposed correction: fix in this change (`grammar_generator.py` wrote the rule-name escape
  as the keyword), with negatives for the escapes.
- Decision: accepted, owner ruling 2026-10-17 (F1): fixed here; the xfails became passing
  tests; the delta holds as written, with a scenario for the literals.

### S-2: `delete` and `activate` under the verb rule without device evidence (C5)

- Artifact: the verb requirement (now `specs/validation/raw-set-input/spec.md`); the docstrings
  of `tests/unit/validate/test_set_validator.py::TestEveryVerbIsValidated`.
- Counterexample: proposed probe. A `delete` of one leaf-list value may be accepted by a
  device in configure mode; the set reader refuses it at base and now.
- User impact: none for a device export, which holds no `delete` line.
- Proposed correction: keep the one rule; cite the device only for `deactivate` and
  `protect`; ask the device (device questions 1 to 3).
- Decision: accepted, coordinator disposition 2026-10-17 and owner rule (set input is a device
  export; `delete` and `activate` stay as they are): docstrings corrected; questions recorded.

### S-3: the hold-time class claimed more than D1 showed

- Artifact: `tests/data/device/expected-findings.json`, class `mandatory-commit-refuses`.
- Counterexample: the recorded finding sits in group `GR-EDGE-INTF-MH`, which no
  `apply-groups` names; D1 probed an interface.
- User impact: the record's reason overstated the evidence.
- Proposed correction: word the class as D1 showed it; ask the device (question 5).
- Decision: accepted, coordinator disposition S6: reworded.

### S-4: a verb on a scalar leaf's value is refused (C4)

- Artifact: `instruction-integrity.md` C4; rows `a-leaf-value-*`.
- Counterexample: none found; the A2 caret sits where the statement ends.
- User impact: none expected.
- Proposed correction: confirm with one probe line (question 4).
- Decision: accepted as it stands, coordinator disposition N1.

### S-5: tags above a relative path are dropped with the note (C6)

- Artifact: `specs/conversion/selection-tags/spec.md`, relative requirement.
- Counterexample: the device's own relative curly (`C3`) prints the ancestor's tag as a
  `## inactive:` comment that does not load; dropping it is equivalent.
- User impact: junoscfg's note goes to stderr.
- Proposed correction: none.
- Decision: accepted as it stands, coordinator disposition N2.

### S-6: a whole-list tag the device takes (new evidence, Builder, phase 5)

- Artifact: the ruling to apply the verb rule in the set reader (S7); the approved entry-keys
  requirement "A meta attribute addressed to an entire list SHALL survive set output".
- Counterexample: executed evidence, `private_test_data/deactivate6.txt` (an earlier owner
  probe): the device took `deactivate forwarding-options port-mirroring family inet output
  routing-instance` and printed it back; D5 shows it refusing `protect policy-options
  policy-statement`. The first list carries the XSD flag `homogeneous` (`h`), the second not.
  Refusing every bare list keyword would refuse a device line.
- User impact: an import of a device export holding such a line.
- Proposed correction (implemented, interim): the walk tags a homogeneous list whole and
  refuses another list's bare keyword (3,440 homogeneous of 21,507 lists). The rule rests on
  two lists; questions 6 and 7 test it. The entry-keys requirement is modified to match; the
  static-route and route-filter whole-list shapes went.
- Decision: Pending owner decision. Interim: the safe reading above, which keeps every device
  line known to junoscfg valid.

## Verdict

Pending the fresh Reviewer.

## Scope dispositions and follow-up evidence

Test/Challenge report (`private_test_data/makeover-work/device-probe-fixes/tc/test-challenge.md`),
coordinator dispositions and owner rulings of 2026-10-17:

| ID | Disposition | Evidence |
|---|---|---|
| M1 | fixed: every `probes/**/*.json` checked; prompt, banners, commit and change attributes, time of day, home paths and host-name statements refused; every value held to the synthetic vocabulary; the raw session's two prompt names searched under `tests/data/` when the session is on the machine | `TestTheProbeRecordIsSanitized` (4 tests) |
| M2 / S-1 | fixed (F1) | `TestASymbolKeywordIsWrittenAsItself`, shipped-grammar rows |
| S1 | fixed: relative set and structured text equal the untagged configuration's | `test_a_relative_selection_notes_every_tag_it_drops` |
| S2 | fixed: a per-value tag of a selected leaf-list gives one note per writer; the anonymized note is asserted whole | `test_a_relative_leaf_list_selection_notes_a_value_tag`, `test_an_anonymized_relative_note_quotes_nothing` |
| S3 | fixed: the groups copies, negatives for `chassis debugger-on-*`, `_shape` refuses a flag with children | `test_xsd_fixes.py`, `test_shipped_artifacts.py::test_rejected` |
| S4 | fixed: rows for a hidden-list container, flag-spelled values, a group's value, `groups`; every-door row `deactivate interfaces`; `deactivate groups` (tag dropped by the writers) to the backlog | `test_meta_path.py`, `test_every_door.py`, BACKLOG WHOLE-LIST-TAGS-001 |
| S5 / S-2 | docstrings corrected; device questions 1 to 3 | `test_set_validator.py` |
| S6 / S-3 | reworded | `expected-findings.json` |
| S7 | the set reader refuses a list's bare keyword by the shared walk (homogeneous lists aside, S-6); the remaining path, a whole-list tag from JSON or curly input written as a set line `-v` refuses, is outside a cohesive fix (a new writer rule with no device evidence) and is pinned by strict xfails and BACKLOG WHOLE-LIST-TAGS-001 | `test_scalar_meta_targets.py`, `test_every_door.py` |
| S8 | resolved: F1 and F2 are not backlog items; the xfails and the IDs went | `test_device_probes.py` |
| F2 | owner rule 2026-10-17: measured, not taken. The widened grammar touched 12,416 containers the XSD marks `oneliner` (447 names), grew the grammar from 1.83 MB to 2.32 MB and its compile from 9.5 s to 11.7 s, in about 25 lines of generator code; instead `-v` names several statements on one line unsupported (about 25 lines in the validator, no grammar change) and conversion reads them | `test_several_statements_on_one_line_are_named_unsupported`, decision record |
| N3 | modelled as the record shows: `system dump-on-panic` is an empty container | `_UNDOCUMENTED` |
| N4 | fixed: the keyword JSON gives no diagnostic or warning | `test_the_keyword_json_reads_as_the_element_json` |
| N5 | fixed: the set text of an ancestor selection is asserted whole, each tag after the statements below it | `test_an_absolute_selection_keeps_its_ancestors_tags` |
| N6 | fixed: commit-check names give the field warning | `test_a_statement_commit_check_misses_is_a_field_warning` |
| N7 | fixed: one note per output, counting each tag of each value; a comment is no tag | `test_one_note_counts_every_tag_of_every_value` |
| N8 | added; the curly doors take a whole-list tag: strict xfail, WHOLE-LIST-TAGS-001 | `test_every_door.py` |
| N9 | fixed: the lists fixture lives in `tests/support/artifacts.py` | `make_lists_artifacts` |
| N10 | no action | |

### Device questions for the next probe

Paths only; each runs in `configure private`, never committed.

1. `set policy-options community JUNOSCFG-C1 members 64496:1`, `... members 64496:2`, then
   `delete policy-options community JUNOSCFG-C1 members 64496:2`: taken or refused?
2. `set system apply-groups JUNOSCFG-G` (with the group defined), then `delete system
   apply-groups JUNOSCFG-G`: taken or refused?
3. `delete policy-options policy-statement` with one policy defined: taken or refused?
4. `deactivate routing-options static route 198.51.100.0/24 description JUNOSCFG-PROBE` (a
   scalar leaf's value after a verb): refused as A2 was?
5. `set groups JUNOSCFG-G interfaces <*> hold-time down 0` without any `apply-groups`, then
   `commit check`: passes or fails?
6. Whole-list tags on lists the XSD does not mark homogeneous: `deactivate system login user`
   and `deactivate routing-options static route` (with entries defined): refused as D5 was?
7. Whole-list tags on homogeneous lists: `deactivate system name-server` and `deactivate
   firewall family inet filter F term T from source-prefix-list`: taken, and how does display
   set, JSON and XML print them?
8. `set interfaces ge-0/0/1 hold-time up 0 down 0`, then `show interfaces ge-0/0/1 | display
   set`: two lines, as the captures print `hold-time up 2000` and `hold-time down 0`?
9. `system dump-on-panic`: `show system dump-on-panic | display json`, `{}` or `[null]`?
10. A per-value tag from JSON: `load merge json` of `"community": ["64496:1", "64496:2"],
    "@community": [null, {"inactive": true}]` under the probe route: taken, and printed how?
