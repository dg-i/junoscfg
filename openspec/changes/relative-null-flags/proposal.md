## Why

`--path --relative` JSON output of a selected list keeps the IR's `{}`/`true` flags, and a
selected empty container is written `{}`, where absolute output writes `[null]`: the object
stage normalizes mappings only (yaml-new-format review B7). Owner ruling 2026-10-15 on PO-1:
fix it as its own change.

## What Changes

- The JSON writer's object stage spells a relative selection as the value under its last
  path key: `{}`/`true` flags become `[null]` in a selected list or as the selection itself,
  and list entries put `name` first, as absolute output does. yaml-new follows (same object).
- User-visible effect: relative `json` and `yaml-new` output text changes for those
  selections only. Not a break (`.openspec.yaml`): `{}`, `true` and `[null]` load as the
  same configuration, and `[null]` is what absolute output already writes.

## Capabilities

### New Capabilities

None, because path filtering already exists as a capability.

### Modified Capabilities

- `conversion/path-filtering`: relative JSON and yaml-new output spell the selection as
  absolute output does at that path.

## Non-goals

Schema-context scalar-leaf coercion of relative selections (instruction-integrity C5); any
device claim (C8); set, structured and `yaml` output; absolute output.

## Completion

Outcome and acceptance: a regression test observed failing at `ea18fab` passes; existing
path-filtering and yaml-new tests pass; device comparison differs only where explained.
