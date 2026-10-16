## Resolved instructions

`instruction-integrity.md`: owner request and approved design (2026-10-16, relayed), the
coordinator's rulings RC1–RC6, MSG1, MSG2 (C1 relaxed byte identity: set and curly identical,
JSON/yaml-new only toward the device's spelling), records owned by the parallel session
regenerated only through their tools (C2), `applies_to` replaced by the recorded name (C3),
risk floor high (C4), (P) rulings with interim defaults (C5), XML `-v` out of scope (C6).

## Requirements

- `specs/validation/device-captures/spec.md` (new): the capture law; undocumented statements;
  `$junos-` variables.
- `specs/schema-pipeline/conversion-hints/spec.md`: a rename keeps the device's element name;
  keyed entries are lists.
- `specs/validation/set-command-validation/spec.md`: every verb, whole lines.
- `specs/validation/junos-json-yaml/spec.md`: path-and-key messages; `{}` and `[null]`.

## Evidence

Measured on base `2d4904b` (`scratchpad/baseline.py`, `bm.py`; JSON-schema leaf errors by
deepest context): per capture and rendering, `-v` and field findings, e.g. QFX5120 curly 5 and
7, JSON 6 and 12, set 8 and 7, XML 1 (no XSD) and 6. Classes: undocumented statements (XML
`<undocumented>`; absent from all three dumps but `per-prefix-label` elsewhere and an
unrelated `shell`); Group E names reaching JSON (`end-range`, `ieee-802.3ad`); JSON input
never resolving `KEY_ALIASES` while XML does; `hello-padding-type` written in set output
(known-differences class `xml-element-name-leak`); isis-instance attribute-group array (mdr1);
`protect` lines rejected; `$junos-` pattern errors (bng1); hold-time `up` mandatory (mdr1,
device prints no warning: open); radius `secret`, event policy `then` mandatory (device warns:
expected). `{}` presence: the JSON schema already accepts it (no `-v` error traces to it).
Set and conf `-v` over whole captures cost about 85 s serial (Earley); the JSON doors and field
validation about 2 s.

## Non-goals

As the proposal: XML `-v`; hold-time; statements no committed capture shows; the rest of
`xml-element-name-leak` unless one rule covers it; no-op fixes.

## Acceptance criteria

Every `Tests:` id in the four deltas exists and passes; the new ones fail on base (recorded
in `review.md`). The capture law reports only recorded findings; the strict xfails fed by
`UNPLACED_IN_THE_EXAMPLE` pass and are retired; `grammar-corpus.json` and
`known-differences.json` shrink by the fixed lines through their tools. Conversion: set and
curly output byte-identical over every capture rendering and the set corpus; JSON, yaml-new
and yaml output differences listed and each toward the device's spelling or the one IR.
Independent Test/Challenge reads the acceptance tests before implementation.

## Performance expectations

The new default-tier law costs at most a few seconds; no budget raise expected (400 s cold,
200 s warm, 95 s no-schema, docs/VERIFICATION.md); measured at the full check. Whole-capture
grammar validation stays opt-in (`--device-grammar`).

## Outstanding decisions

None blocking; (P) rulings proceed on their interim defaults and are reported.

## Execution and checkpoint

- Roles required: Builder, independent Test/Challenge, fresh Reviewer (coordinator).
- Resume point: phase 4 (type bug: no design phase).

## Delta log

- Freeze established: proposal `88c62e1`, deltas and this record in the next commit.

## Scope and completion

Outcome: the validators accept every statement the committed captures hold, by fixes at the
owning layer (schema model, kernel names, validators), with a law that keeps it so. Frozen
criteria above; exclusions are the non-goals. Independent findings go to the coordinator as
pending owner decisions, not into this change.
