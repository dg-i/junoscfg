## Resolved instructions

`instruction-integrity.md`: the owner rulings of 2026-10-17 relayed by the coordinator (one
change; rulings 1 to 3f), precedence over the approved path-filtering and conversion-hints
text (C1, C2), the tests that change with the rulings (C3), a leaf's value counted with a
leaf-list's (C4), one rule for every verb (C5), ancestors' tags in relative output noted (C6),
the verb decision shared with the set reader through `display` (C7), hard-linked XSD dumps
(C8), the verification invitation deferred (C9). Risk floor high.

## Requirements

- `specs/validation/set-command-validation/spec.md`: what a verb line may name.
- `specs/conversion/selection-tags/spec.md` (new): absolute selections keep the tags of the
  selected statement and along their path; relative selections note each tag they cannot
  write, never a bare verb.
- `specs/conversion/path-filtering/spec.md`: the relative requirement points at
  selection-tags; the absolute tag requirement moves there.
- `specs/conversion/writers/spec.md`: a per-value leaf-list tag is noted (added).
- `specs/validation/device-captures/spec.md`: the hold-time class; the probe's undocumented
  statements; the sanitized probe record (added).
- `specs/schema-pipeline/conversion-hints/spec.md`: the keyword alias is permanent.

## Evidence

Device probe (QFX5120, 25.2R2-S1.5, 2026-10-16, `configure private`, never committed; raw
session in `private_test_data/device-probe-2026-10-16/`, never committed). Frozen in the
brief's form; the committed record is `tests/data/device/probes/qfx5120-25.2R2-S1.5/2026-10-16.json`
(phase 4), sanitized as `docs/how-to/settle-a-schema-question.md` rule 5 asks.

- Hierarchy and questions: `interfaces ge-0/0/1 hold-time` (D1); `routing-options static route
  198.51.100.0/24` with its ancestors deactivated, its leaf tagged and one community value
  (C3, SC1, A2); `snmp name`, `interface-range ... ether-options speed`, `then community = + -`
  in junoscfg's JSON (D2); the keyword JSON `802.3ad`, `to` (D3); grpc `clear-text`, `system`
  and `chassis` undocumented flags (D4, P4); a verb before a list's name (D5).
- Observation: as the brief lists (D1 commit check fails without `up`; C3 ancestors' tags
  printed in set, JSON, XML and curly; SC1 bare verbs and `edit` of a leaf refused; A2 the
  per-value `deactivate` refused, JSON has no per-value annotation; D2 and D3 loaded, device
  names `system-name`, `ethernet-1g`, `*-literal`; the QFX refuses set `ether-options speed
  1g`; D4 and P4 accepted, inside `<undocumented>` in XML; D5 refused).
- Interpretation: junoscfg's validator, path filter and relative writers disagree with the
  device as the brief's reproductions show; reproduced at `ec62908` with
  `junoscfg convert -i set -e set -v` (D5 "Validation: OK"; A2 "Validation: OK" then
  "Metadata commands cannot target scalar-leaf values", exit 2), `--path system.host-name`
  under `deactivate system` (only `set system host-name r1`), `--path system.syslog
  --relative` (set: `set file f any any` and a bare `deactivate`; structured: the note; json:
  the value with its `@`), and `-v` of the five undocumented statements (five "Invalid
  syntax"). Inputs in `private_test_data/makeover-work/device-probe-fixes/`.
- Unknowns: whether a device loads a per-value leaf-list tag from JSON; a `delete` of one
  leaf-list value; NAT rule renames (no node in the shipped schema).
- Measured at base: the grammar cannot tell a list's name from a leaf's value. A prototype that
  judged a verb line by its parse tree rejected device lines (`deactivate interfaces ge-0/0/1
  unit 200`, `protect interfaces lo0`, `deactivate vlans V999`: the grammar's `VALUE`
  alternatives win the parse). The set reader's walk on an empty configuration places all 28
  distinct verb lines of the committed captures, raises for a leaf's value and tags a bare list
  keyword as a whole list. Blast radius of the tightening: 21,507 list nodes (a verb line
  stopping at one's keyword) and 203,244 leaf and leaf-list nodes (a verb line naming a value)
  of the shipped tree; every committed capture verb line stays valid.
- Before/after comparison base: `tools/compare_device_outputs.py record` at `ec62908`, 96
  conversions, `private_test_data/makeover-work/device-probe-fixes/base.json`.

## Non-goals

As the proposal: the QFX refusing set `ether-options speed 1g`; bracket lists in set input;
per-value tags loaded from JSON; a `delete` of one leaf-list value; the reader's whole-list
tag; comments in relative output; the NAT rename.

## Acceptance criteria

Every `Tests:` id in the six deltas exists and passes; each test of a changed behaviour fails
on base (red run recorded in `review.md`); the probe tests of behaviour base already has
(the renames, the keyword JSON, the probe renderings of tagged routes) pass on base as evidence. Every verb line of every committed capture validates
(`tests/corpus/test_set_corpus.py::TestEveryCaptureValidatesAsSet`). The before/after
comparison over the 96 conversions shows no change, or only changes each naming the ID it
closes. `grammar-corpus.json` records no rejection of `set chassis dump-on-panic`;
`expected-findings.json` holds the hold-time finding in its new class; `known-differences.json`
changes only through its tool. Independent Test/Challenge reads the acceptance tests before
implementation; a fresh Reviewer reads the frozen evidence and the diff.

## Performance expectations

The validator walks the structure tree only for a non-`set` line (28 distinct lines in all the
captures); the tree is loaded once per process. The probe tests read one small JSON record. No
budget in `docs/VERIFICATION.md` is raised; measured at the full check.

## Outstanding decisions

None, because the rulings settle every material choice; C4 and C5 are open to challenge.

## Execution and checkpoint

- Roles required: Builder; independent Test/Challenge; fresh Reviewer (coordinator), as
  `instruction-integrity.md` records.
- Resume point: STOP-T (independent Test/Challenge of the phase-4 tests), then phase 5.

## Delta log

- Freeze established: proposal and preflight at `560cccd`; deltas and this freeze at `ae34f5a`.
- Phase 4 (acceptance tests): the probe tests found two more false rejections of lines the
  device took, outside the brief: `set interfaces ge-0/0/1 hold-time up 0 down 0` (the grammar
  takes one `hold-time` leaf a line) and `then community = | + | - JUNOSCFG-C1` (the grammar
  generator writes the key keyword `=` as `eq_literal`, `src/junoscfg/validate/grammar_generator.py`
  lines 193 and 627). Interim, a safe reversible action: strict xfail rows naming
  SET-COMPACT-LEAVES-001 and SET-LITERAL-KEYWORDS-001, recorded for the backlog; scope ruling
  asked at STOP-T. No completed work is invalidated.

## Scope and completion

Outcome: junoscfg validates verb lines, writes `--path` selections and models the probed
statements as the QFX5120 does, and the records say what the probe proved. Frozen criteria
and exclusions as above. Applicable existing requirements: the device-capture law, the
path-filtering and writers requirements, every-door validation.
