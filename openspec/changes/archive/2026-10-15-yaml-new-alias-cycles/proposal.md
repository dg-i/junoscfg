## Why

yaml-new refuses any mapping or list reached through a YAML alias (interim SC-1), so a
hand-written file that shares a block is refused although JSON can hold it written out.
Owner ruling 2026-10-15 on PO-2/SC-1: refuse cycles only, keep alias-bomb protection.

## What Changes

- `junoscfg.input.find_non_json_value` walks a shared mapping or list at every place it is
  reached; it refuses a cycle (kind `cycle`) and an expansion past a bound (kind `alias`),
  each with its path and never its value, in time linear in the parsed document. It returns
  `NonJsonValue(kind, path, reason)`, a new kernel name.
- Interim bounds (SC-2, SC-A, pending the owner): written out, the document may hold at most
  twice the values it holds as parsed, and nest no deeper than its parsed depth.
- The yaml-new reader expands an accepted document to a tree; the yaml-new writer checks the
  IR before its object stage; `validate_config` judges the expanded object. The JSON
  object stage copies a shared IR written out, as JSON output already spells it.
- Additive (`.openspec.yaml`): only previously refused input is accepted; message wording
  for refusals changes. Records of the alias policy updated (specs, guides, contracts,
  ARCHITECTURE.md, a decision record). Backlog entries for PO-3 and PO-4 (owner ruling).

## Capabilities

### New Capabilities

None, because the yaml-new capabilities exist.

### Modified Capabilities

- `conversion/junos-json-yaml`: the refusal and writer requirements.
- `validation/junos-json-yaml`: the yaml-new validation requirement.

## Non-goals

Legacy `yaml` input (C5); amplification inside PyYAML by scalar aliases and merge chains
(SC-B); device claims.
