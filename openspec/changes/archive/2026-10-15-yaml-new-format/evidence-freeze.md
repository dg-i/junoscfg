## Resolved instructions

instruction-integrity.md governs: owner instruction 2026-10-15 over the backlog's naming
(C2) and input conveniences (C3); worktree and finalisation order from the owner (C1, C4);
declared-break entries record an additive change, patch bump (C5); convert contract wording
corrected (C6); one exposed table name (C7); JSON's `{}`/`true` to `[null]` kept for yaml-new
with the device question recorded (C8).

## Requirements

- specs/conversion/junos-json-yaml/spec.md: yaml-new output is the Junos JSON object; input
  reads as the JSON object it spells; non-JSON YAML values refused; one name-to-implementation
  table; migration from yaml.
- specs/validation/junos-json-yaml/spec.md: yaml-new validates as the JSON object it spells.
- No existing requirement is contradicted. conversion/writers ("a writer leaves the IR
  unchanged", set/structured/JSON/YAML) and conversion/format-detection stay as written;
  yaml-new inherits JSON writer purity through the shared adapter (tested by the existing
  purity test's writer doors, extended).

## Evidence

- Base 332523c6aa9576930ee7afe35226d5e4bdd2930d. Reproduced YAML-JSON-001 at base with
  private_test_data/makeover-work/yaml-new-format/measure_base.py: 484 shape/reader
  combinations, 388 identical, 57 key order only, 39 structural; of 40 YAML sources 2 read
  differently as JSON (`yaml-with-ansible-meta-keys`, `universal-statements-below-the-root`).
- probe_empty.py over tests/data/device/*/*/*.json.gz: the JSON writer rewrites 15 `{}` in the
  QFX5120 25.2R2-S1.5 junoscfg-oracle capture to `[null]` (e.g. `system services netconf ssh`,
  `protocols isis interface passive`); the vMX 23.2R2-S7.5 capture of the same source spells
  them `[null]`. Three `protect: true` to `"protect"` changes are reader annotation
  normalization (all readers), not the writer. JVD captures: no change.
- probe_alias.py: no YAML anchor in 513 yaml outputs (device captures and catalogue).
- Legacy yaml input with an unquoted date reaches the JSON writer as `datetime.date` and fails
  with TypeError (pinned in test_every_message as a withheld failure); yaml-new refuses it.

## Decisions (owner default: yaml-new is the identical object to Junos JSON)

D1 empty mappings and `true` flags: as JSON, `[null]`. D2 `junoscfg:unplaced`: as JSON writes
it. D3 no `_ansible_*`/`_meta_*` cleanup, no scalar leaf-list promotion on yaml-new input.
D4 YAML-only values refused (safe default; reversible). D5 detection keeps returning `yaml`.
D6 validation uses the JSON schema. D7 writer emits no anchors. D8 patch bump. D9 rename plan
and deprecation policy in docs/decisions/2026-10-15-yaml-new-before-renaming-yaml.md.

## Non-goals

No change to `yaml`, JSON output, detection or the anonymizer; no deprecation; no rename;
no new device claim; no YAML conveniences on yaml-new input; compare tool output set unchanged.

## Acceptance criteria

Every test id in both deltas, observed failing before implementation, then passing. `yaml`
output byte-identical to base over the device corpus (compare_device_outputs.py diff empty
for yaml and json) and over every catalogue shape/reader. Independent Test/Challenge and a
fresh Reviewer (high risk floor) record verdicts in review.md.

## Performance expectations

None, because conversion work is unchanged; yaml-new costs one JSON normalization plus a
YAML dump, as JSON plus YAML do today.

## Outstanding decisions

None blocking. Open device question (not an owner decision): does a QFX5120 on 25.2R2-S1.5
load `{"configuration":{"system":{"services":{"netconf":{"ssh":[null]}}}}}` with `load merge
json` as it loads `ssh {}`? Name the path only; never a whole configuration.

## Execution and checkpoint

- Roles required: instruction-integrity.md Assurance (Builder, independent Test/Challenge,
  fresh Reviewer, Finalizer).
- Resume point: phase 3 design.

## Delta log

- Freeze established at the commit adding this file, on base 332523c.
- Test/Challenge delta (report on 0813986): eight binding test gaps and one omitted criterion
  (validating a YAML-only value). Consistency: no requirement contradicted; validation/
  junos-json-yaml gains the non-JSON-value outcome, conversion/junos-json-yaml names the loader
  and whole-document scope, D4's check moves to `junoscfg.input.find_non_json_value` (kernel,
  shared with validation), the table becomes a dict read per call (rename rehearsal). Invalidated:
  none of the earlier evidence; reruns: focused tests, full suite in the commit hook (c84d07d),
  canonical full before review. PO-1 (relative JSON list output) recorded for the owner.
- Reviewer delta (verdict on c95e67f, Changes required): R1 migration of an unquoted date, R2
  cycles/aliases, R3 rename record. Consistency: requirements extended (writer refusal, alias
  kind, migration refusal); no earlier criterion contradicted. SC-1/PO-2 alias policy pending
  the owner with the interim "refuse a mapping or list reached through an alias" (scalar
  aliases and flat merge keys accepted; wording corrected after Reviewer N1); PO-3, PO-4
  pre-existing `yaml` behaviour.
  Invalidated: the c95e67f full checkpoint (runtime code changed). Reruns: focused, fast, full.

## Scope and completion

Outcome: `yaml-new` usable from library, CLI convert/audit and validation, equivalent to JSON,
with a tested migration and a prepared, documented rename. Exclusions: the rename itself,
deprecating `yaml`, MAKEOVER-13 reader unification for `yaml`/JSON (ARCH-C10 stays xfail).
