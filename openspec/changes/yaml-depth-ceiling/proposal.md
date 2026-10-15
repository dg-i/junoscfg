## Why

The owner ruled on 2026-10-15 (relayed in the batch brief): "I do not want to fix PyYAML
problems; if this is a genuine junoscfg problem fix it, if not leave it." yaml-new's two
interim alias bounds (SC-2 size, SC-A parsed depth) guard against alias bombs, a property
of YAML aliases and PyYAML, and refuse harmless files (a top-level anchor aliased under
`configuration`). What remains a junoscfg problem: its own recursive stages crash with
`RecursionError` on a cycle or on very deep nesting, at yaml-new's writer and in the legacy
`yaml` reader (`_strip_meta_keys`, C5).

## What Changes

- Removed: the size bound (SC-2; SC-C moot). junoscfg assumes its YAML input is not
  hostile; a caller handling untrusted YAML bounds it before calling junoscfg.
- Replaced: the parsed-depth bound (SC-A) by a fixed ceiling. The expanded document may
  nest 64 levels (path steps from its root); a deeper value is refused as kind `value` at
  its path, "is nested deeper than 64 levels", at every yaml-new door (reader, writer,
  `validate_config`) and in the legacy `yaml` reader. Measured: device corpus 17 levels,
  shape catalogue 15, the schema's deepest path 25 plus the configuration wrapper.
- Kept: the cycle refusal (kind `cycle`), now also in the legacy `yaml` reader.
- `find_non_json_value(data, *, scalars=True)`: the `yaml` reader passes `scalars=False`
  (its IR holds YAML's dates); no new name. Valid legacy `yaml` output is byte-identical.
- Records: specs, guides, contracts, API page, developer guide, ARCHITECTURE.md, a new
  decision record superseding 2026-10-15-yaml-new-expands-aliases-within-a-bound, changelog.
- Not a break (`.openspec.yaml`): patch.

## Capabilities

### New Capabilities

None, because the yaml-new capabilities exist.

### Modified Capabilities

- `conversion/junos-json-yaml`: the alias requirement, the format-table requirement.
- `validation/junos-json-yaml`: the yaml-new validation requirement.

## Non-goals

SC-B (PyYAML expands scalar aliases and merge chains) and alias-bomb expansion in either
format: left, not backlogged. `yaml` validation (no junoscfg recursion). JSON input depth
(C6) and non-string keys in `yaml` input (C5 of the preflight): reported. Device claims.
