## Findings

### Independent Test/Challenge (phase 4, STOP-T)

Fresh context-isolated agent run by the orchestrator on `c9f760f` (merge base
`a19e978`); report copied to `test-challenge.md`. The orchestrator relayed the
rulings of 2026-10-11: accept F1 and F3–F11 with the proposed tests, F1 fixed in
the implementation; F2 recorded as evidence-blocked with probe P6; F6 reworded
and one changed verdict pinned. Disposition, all in the phase-5 commit:

1. F1 (high), sibling split accepted `hold-time up 2000 down;`: fixed. The walk
   records a leaf read without its value (`_Reading.incomplete`);
   `structured_set_lines()` returns those lines as `incomplete` and
   `validate_structured()` reports each as an error. Contract row
   `a-sibling-without-its-value` (invalid on every door, the deprecated one
   included) and the `structured_set_lines` case. The set grammar's own
   acceptance of `set … hold-time down` (merged rule: `hold-time` takes a value)
   is a set-validation defect, recorded in `ledger.md` for change 17.
2. F2 (high), empty block: see the challenge below; spec and tests now say
   "reported, not silently dropped" and assert only the warning.
3. F3 (medium-high), a tagged one-liner detected as YAML: fixed at the owning
   layer, `display/format_detection.py` (`_opens_a_block`). Detection cases and
   a CLI case without `-i` for convert and audit.
4. F4 (medium), audit door: `audit unused` added to `TestABlockOnOneLine` with a
   one-line prefix-list.
5. F5 (medium): `xfail_on` rows use `raises=AssertionError`, and `cases()`
   asserts every name in `xfail_on` is a door.
6. F6 (medium): see the challenge below; `test_the_new_lexer_changes_a_verdict`
   pins `system { bogus-statement 1; }` invalid on the deprecated door.
7. F7 (medium): absolute `statements()` for a tagged entry, a protected block
   holding a quoted value with `;`, `{`, `#` and `/* */`, and a tagged bracket
   list; comment cases with an open quote, the device's `## Warning: …` line,
   and a quote inside a block comment.
8. F8 (medium-low): `Row.warnings`, checked on every door that takes the row
   (the CLI's `-v` now prints `Warning:` lines, and the deprecated validator
   reports the lexer's notes too); `test_no_deprecation_reaches_their_caller`
   runs the recommended doors with `DeprecationWarning` as an error.
9. F9 (low): `test_every_defined_class_has_a_recorded_line`.
10. F10 (low): a `;` with no statement (`;;`, `};`, a lone `;`) reads as
    nothing (`TestAnEmptyStatementReadsAsNothing`); `audit unused` added to the
    refusal test (exit 2).
11. F11 (low): the freeze's list of base passes corrected;
    `test_the_walk_and_the_grammar_come_from_it` shows both the walk and the
    grammar come from the `artifacts_dir` given. `tests/support/artifacts.py`
    gains `write_minimal_tree` because curly validation now reads the structure
    tree; `test_validate_auto_detect_structured` writes it, its assertion
    unchanged. The minimal set itself stays tree-less, which
    `TestArtifactsOption` relies on.

## Already provided

`display.artifacts_dir()` scopes the walk to the caller's artifacts; the
existing `diagnostic_sink` shape of `from_dict()` and `anonymize()` carries the
reader's warnings; `tools/device_differences.py` regenerates the device record.

## Specification challenges

### F1: a sibling split must not create an acceptance

- Artifact: `specs/validation/structured-validation/spec.md`, "Curly text is validated as the conversion walk reads it" (as committed at `c9f760f`).
- Counterexample: executed (Test/Challenge `tc_probe3.py`, `tc_counter_c5.py`): curly `hold-time up 2000 down;` splits into `set … hold-time up 2000` and `set … hold-time down`, both accepted by the set grammar; on the merge base `validate_structured` rejected it. `down` takes an unsignedInt (schema); no capture holds a value-less `down`.
- User impact: a curly configuration missing a value would validate.
- Proposed correction: a statement the walk cannot complete is invalid in curly validation, whatever the set grammar says.
- Decision: Accepted (orchestrator ruling relayed 2026-10-11 under the owner's unattended-run instruction): fixed in the implementation; requirement text, scenario "A sibling without its value", contract row and `structured_set_lines` case added.

### F2: an empty block's meaning has no device evidence

- Artifact: `specs/conversion/structured-input/spec.md`, "What yields no statement is reported, never written" (as committed at `c9f760f`), and the `an-empty-block` parameters.
- Counterexample: executed on the base (`tc_probe1.py`): `protocols { lldp; }` gives `set protocols lldp`, `protocols { lldp { } }` gives nothing; if the device loads `lldp { }` as `lldp;`, "never written" pins a wrong configuration.
- User impact: possibly a presence statement lost, now with a warning instead of silently.
- Proposed correction: device probe; until then assert only the report.
- Decision: Pending owner decision. Interim action: the requirement is reworded "reported, not silently dropped" and the warning claims nothing about the device; tests assert the warning only; EVIDENCE_BLOCKED on probe P6 in `private_test_data/makeover-probes.md` (`protocols { lldp { } }`, `system { services { ssh { } } }`, then `display set`). `makeover-probes.out` does not exist at phase 5. (owner intake 2026-10-11: merge with recorded interim action)

### F6: the deprecated doors do not keep every verdict

- Artifact: `specs/validation/structured-validation/spec.md`, "The validate package's structured doors are deprecated", and `specs/conversion/structured-input/spec.md` on `to_set()` ("give the output it gave before").
- Counterexample: executed (contract rows): `JunosValidator.validate_structured` changes its verdict on `a-block-on-one-line`, `a-brace-too-many` and `the-omitted-placeholder`, because it reads with the new lexer.
- User impact: none harmful; the spec misstated what changes.
- Proposed correction: state which verdicts change and pin one.
- Decision: Accepted (orchestrator ruling relayed 2026-10-11 under the owner's unattended-run instruction): both requirements now name the schema-free route kept and the verdicts that change; `test_the_new_lexer_changes_a_verdict` pins one.

## Verdict

Pending the fresh Reviewer (STOP-R).
