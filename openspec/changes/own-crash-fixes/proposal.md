## Why

Three defects in junoscfg's own code, reported by the owner on 2026-10-16 under the trusted-input
rule (docs/decisions/2026-10-15-configuration-input-is-trusted.md): (1) a `yaml` document with a
mapping key that is not a string (`64496: x`) crashes the meta-key cleanup with `AttributeError`
(and `convert -v` crashes jsonschema with `TypeError`); (2) JSON nested past about 450 levels
crashes junoscfg's own walks with `RecursionError` (`_normalize_annotations`, `dict_walker`); (3)
an absolute `--path` ending at a leaf drops the leaf's own tags (`deactivate`, `protect`,
comment), so the output loads the statement active: a silent change of meaning.

## What Changes

- One key rule at the one boundary: `junoscfg.input.find_non_json_value` refuses a mapping key
  that is not a string whatever `scalars` says, as yaml-new already does. Every stage after it
  (cleanup, annotation normalization, writers, schema lookup, jsonschema) needs string keys, and
  reading the key as its string would be wrong for YAML 1.1 words: the schema has a statement
  named `on`, which unquoted loads as `True`. The `yaml` reader and the `yaml` validator both
  refuse it with yaml-new's wording (`a YAML int key at configuration has no JSON spelling`).
- JSON and XML input take the same 64-level ceiling (decision
  2026-10-15-yaml-nests-at-most-64-levels): both readers call `find_non_json_value`, `a JSON
  value at ... is nested deeper than 64 levels`, and JSON validation reports it. Measured: a
  repeated XML element doubles its depth in the IR, so XML below lxml's 256 levels crashed the
  `yaml` writer (Test/Challenge SC2); set and structured are bounded by the schema; legacy `yaml`
  had the ceiling; past ~490 (PyYAML) and ~20,000 (`json.loads`) the parsers fail first.
- `display.filter_dict_by_path`, rebuilding an absolute selection, keeps the selected key's
  sibling annotation (`@<key>`), so a leaf or leaf-list keeps its tags in every writer.
  Containers and list entries already carry theirs inside the selected value.
- Not a break (`.openspec.yaml`); patch. No override, fallback, parameter or environment read.

## Capabilities

### New Capabilities

None, because each behaviour has a spec.

### Modified Capabilities

- `conversion/junos-json-yaml`: the `yaml` reader refuses a non-string key; JSON and XML input share the ceiling.
- `conversion/path-filtering`: an absolute selection keeps the selected statement's tags.
- `validation/junos-json-yaml`: `yaml` validation refuses a non-string key; JSON validation the depth.

## Non-goals

Relative selections (archived relative-selections drops a tag on the selected statement on
purpose; SC1 records the leaf case); tags of an ancestor on the path (reported as an owner
question); parser limits; `from_dict` handed a deep IR directly.

## Completion

No traceback for the three inputs at `convert` and `convert -v`; `--path system.host-name` writes
the leaf's tags as `--path system` does in set, structured, json, yaml and yaml-new, from every
input format; relative output and absolute output of containers and entries unchanged.
