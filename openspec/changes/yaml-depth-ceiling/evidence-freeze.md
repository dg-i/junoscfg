## Resolved instructions

instruction-integrity.md governs: the owner rule relayed in the brief ("I do not want to fix
PyYAML problems; if this is a genuine junoscfg problem fix it, if not leave it") and the
rulings on SC-2 (removed), SC-A (a fixed 64-level ceiling at reader, writer and
`validate_config`), the cycle refusal (kept), SC-B (left, not backlogged), SC-C (moot) and
C5 (the `yaml` reader refuses a cycle and depth past 64; valid output byte-identical). The
old decision record is superseded (C1); the format-table requirement is modified (C2);
`yaml` validation is unchanged (C3); C5, C6, C7 are reported, C8 left to the owner.

## Requirements

- specs/conversion/junos-json-yaml: REMOVED "A block shared through an alias is written out, a
  cycle and an alias bomb are refused"; ADDED "... a cycle and nesting past 64 levels are
  refused"; MODIFIED "yaml-new output is the Junos JSON object", "A YAML value JSON cannot
  hold is refused", "Each format name selects its implementation through one table".
- specs/validation/junos-json-yaml: MODIFIED "yaml-new validates as the JSON object it
  spells" (ceiling, no bounds).
- Contradicted text, replaced by the rulings: the size bound ("more than twice the values"),
  the parsed-depth bound ("deeper than the parsed document's deepest value"), "Both bounds are
  interim", and "`yaml` SHALL keep its reader ... unchanged".

## Evidence

- Base `adb6fb7`. Depth (measure_depth.py, schema_depth.py in
  private_test_data/makeover-work/yaml-depth-ceiling/): deepest value over 72 device
  conversions to json, yaml-new and yaml: 17 path steps (bng1_mx304, vMX 23.2R2-S7.5); over
  1,461 catalogue conversions: 15 (14 json and yaml-new); the schema tree's deepest path,
  counting an index step for each list, is 25 steps below `configuration`
  (`groups.group.logical-systems.routing-instances.instance.bridge-domains.domain.protocols.
  igmp-snooping.vlan.qualified-vlan.interface.static.group.source.name`), 26 with it. 64 is
  more than twice every figure.
- Door probe (doors.py, doors-base.txt): yaml-new refuses a top-level anchor aliased under
  `configuration` (SC-A) and `NESTED_ONCE`; small and large bombs refused (SC-2); legacy
  `yaml` input raises `RecursionError` on a cycle and on the alias chain, hangs past 20 s on
  the 10^9 bomb; alias-free text 70 levels deep converts at every door.
- Thresholds (thresholds2.py): alias-free text past about 490 levels fails inside PyYAML's
  loader (`yaml/scanner.py`) at every door before junoscfg runs; PyYAML's dumper fails past
  about 330; JSON input about 500 deep fails in the yaml-new writer's walk (`input.py:visit`),
  about 2,000 deep in `_normalize_annotations` (C6).
- Base records for the byte-identity comparison: device corpus base.json (96 conversions,
  tools/compare_device_outputs.py), catalogue-base.json (2,435 shape x reader x writer
  conversions, yaml and yaml-new writers included), device-yaml-base.json (240: every device
  rendering written as yaml and yaml-new, read back by that reader into every writer).

## Non-goals

SC-B and alias-bomb expansion in yaml-new and `yaml`; `yaml` validation; JSON input depth
(C6); non-string keys in `yaml` input (C5); device claims; the input-trust rule beyond YAML (C8).

## Acceptance criteria

Every test the deltas name observed failing at base where it states new behaviour, then
passing; cycle and 65-level rows at each door (kernel, yaml-new reader, writer, validator,
`validate_config`, CLI convert, `-v`, audit, anonymized messages; the `yaml` reader through
library, CLI convert and audit); the rows the old bounds refused now read; device corpus,
device yaml round trip and catalogue: 0 differences base vs head; independent
Test/Challenge and a fresh Reviewer record verdicts in review.md.

## Performance expectations

One recursive walk, never deeper than 65 levels; no counting pass. A document without
aliases costs the same walk as at base; an alias bomb costs its expansion (accepted).

## Outstanding decisions

None blocking. C5, C6, C7, C8 are reported.

## Execution and checkpoint

- Roles required: instruction-integrity.md Assurance (Builder, independent Test/Challenge,
  fresh Reviewer, Finalizer).
- Resume point: phase 3 design.

## Delta log

- Freeze established at the commit adding this file, on base `adb6fb7`.

## Scope and completion

Outcome: yaml-new expands any reuse of a block, refuses a cycle and a value nested deeper
than 64 levels at every door; the `yaml` reader refuses both instead of crashing; every
record of the alias policy says so and states that YAML input is assumed not hostile.
