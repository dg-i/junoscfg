## Why

`--path --relative` writes a selection without the schema context its path gives
(relative-null-flags review, owner ruling 2026-10-15 "do what you deem best", relayed):
relative JSON keeps `"class": ["super-user"]` where absolute writes `"super-user"` (a);
relative `set` of a selected list prints a Python repr, structured writes nothing (b); a
selected YAML `null` writes nothing, absolute too (c); `--path system.@` writes
`{"inactive": [null]}` (d); a key holding a dot (`classifiers.ieee-802.1`, `rib.inet.0`)
cannot be selected (e). Measured on the device corpus at base: relative set and structured
also spell 64 and 110 mapping selections wrongly (`set interface et-0/0/2 ...` under
`interfaces`; Junos hides that list name).

## What Changes

- One rule: a relative selection is written as the absolute output writes it, without its
  path. The pipeline hands every writer the path-wrapped IR and the path (`from_dict(...,
  below=keys)`): json and yaml-new write the absolute object's value at the path, yaml the
  IR's, set and structured the absolute statements with the path's words removed
  (`DictWalker` strips them; list names the schema hides and annotation keys have none).
- A path whose value is `null` selects it (absolute and relative); only a missing key gives
  no output.
- A dotted key resolves against the keys present, the exact key first: no new syntax.
- `from_dict(value, wrap=False)` (secondary door) is unchanged.
- Not a break (`.openspec.yaml`): every changed output was wrong or empty; patch.

## Capabilities

### New Capabilities

None, because path filtering exists.

### Modified Capabilities

- `conversion/path-filtering`: the pipeline requirement, the relative-spelling requirement.

## Non-goals

`from_dict(wrap=False)` semantics; the display text filters (`filter_set_by_path` and
siblings); absolute output except a selected `null`; device claims (C8 of relative-null-flags).
