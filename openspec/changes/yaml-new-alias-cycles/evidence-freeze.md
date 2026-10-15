## Resolved instructions

instruction-integrity.md governs: the owner's PO-2/SC-1 ruling (cycles only, every
`find_non_json_value` door, bomb protection with value-free refusals, an unstated bound
chosen conservatively and recorded as a pending challenge, every alias-policy record
updated, additive changelog); PO-3/PO-4 backlog entries ride here (C1); the bound is SC-2
(C2); one exposed kernel name (C4); legacy `yaml` and C8 reported only (C5, C6).

## Requirements

- specs/conversion/junos-json-yaml: ADDED "A block shared through an alias is written out, a
  cycle and an alias bomb are refused"; MODIFIED "yaml-new output is the Junos JSON object"
  (writer refusals before the object stage) and "A YAML value JSON cannot hold is refused"
  (aliases leave its list).
- specs/validation/junos-json-yaml: MODIFIED "yaml-new validates as the JSON object it
  spells" (written out; cycle and bound invalid).
- Contradicted text, replaced by the owner's ruling: the interim refusal of "a mapping or
  list met a second time through a YAML alias, a cycle included" (SC-1).

## Evidence

- Base `87e14cd`. Door probe (private_test_data/makeover-work/yaml-new-alias-cycles/po2.py,
  output doors-base.txt): yaml-new reader, writer and validation refuse a shared block, a
  cycle and a bomb as kind `alias`; legacy `yaml` input raises RecursionError on a cycle in
  `_strip_meta_keys` and expands a bomb through every writer (yaml to yaml-new 1.5 s at
  10^5 values), C5.
- The yaml-new writer checks the document after `junos_json_object` and `_unshared`: a cyclic
  IR raises RecursionError (`_normalize_presence_flags`), a bomb IR expands exponentially
  (`_ensure_name_first`, `_unshared`) before any check.
- `ir_from_junos_json_object` returns the loaded mapping itself, so a shared document would
  give a shared IR, which `_coerce_scalar_leaves` mutates per schema context.
- Prototype (kernel_draft.py): cycle refused at `configuration.system.x`; nine-level bomb
  refused at `l1.3` in 1 ms, a 2^200-value bomb in 8 ms; 200,000 interfaces without aliases
  checked in 0.56 s, never refused; a four-reach block in a three-value file refused (the
  bound's conservative edge).
- Device comparison base record: base.json, 96 conversions.

## Non-goals

Legacy `yaml` input; scalar aliases and flat merge keys (accepted at base and after);
device claims; JSON input (never shared).

## Acceptance criteria

Every test the deltas name observed failing at the base where it states new behaviour, then
passing; cycle and alias bomb tested at each door (reader, writer, validation, CLI,
anonymized messages); device comparison 0 differences; independent Test/Challenge and a
fresh Reviewer record verdicts in review.md.

## Performance expectations

The check stays linear in the parsed document: at most one counting pass plus a walk of at
most twice its values; a document without aliases costs one extra pass over the base.

## Outstanding decisions

None blocking. SC-2 (the bound) is pending the owner with its interim action, as the owner's
ruling directs; C5 and C8 are reported.

## Execution and checkpoint

- Roles required: instruction-integrity.md Assurance (Builder, independent Test/Challenge,
  fresh Reviewer, Finalizer).
- Resume point: phase 4 tests (design.md and the decision record committed).

## Delta log

- Freeze established at the commit adding this file, on base `87e14cd`.

## Scope and completion

Outcome: yaml-new expands shared blocks, refuses cycles and expansions past the bound with
kind and path at every door, in linear time; every alias-policy record says so; PO-3 and
PO-4 are backlog entries. Exclusions above.
