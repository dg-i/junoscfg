## Resolved instructions

instruction-integrity.md governs: the owner request of 2026-10-16 (three defects, one change,
C1); the trusted-input rule (fix junoscfg's own crash or wrong output, no guards against
hostile input, no parser work-arounds); the Builder's choice of the key rule, with the two
tests that walked non-string keys changing with it (C2); ancestor tags reported, not acted on
(C3); the shared readiness inventory (C4).

## Requirements

- specs/conversion/junos-json-yaml: ADDED "A `yaml` key that is not a string is refused",
  ADDED "JSON input nests at most 64 levels"; MODIFIED "Each format name selects its
  implementation through one table" (the `yaml` reader's refusals now include a key) and "A
  block shared through an alias is written out, a cycle and nesting past 64 levels are
  refused" (a key is no longer named by its kind inside a path; test list).
- specs/validation/junos-json-yaml: ADDED "yaml validation refuses what the yaml reader refuses".
- specs/conversion/path-filtering: ADDED "An absolute selection keeps the tags of the selected
  statement".
- Contradicted text: junos-json-yaml "(a key that is not a string named by its kind)";
  decision 2026-10-15-yaml-nests-at-most-64-levels "JSON input keeps its own recursion (C6 of
  change yaml-depth-ceiling)"; test `TestJunosYamlWriter::test_json_input_past_64_levels_is_refused_as_yaml_new`
  ("JSON input nesting past 64 levels converts to JSON as before").

## Evidence

Base `2d4904b`, probes in the session scratchpad and
`private_test_data/makeover-work/own-crash-fixes/`:

- Key: `convert -i yaml -e set` of `configuration: {system: {host-name: r1}, 64496: x}` raises
  `AttributeError` in `_strip_meta_keys`; `convert -v -i yaml` and `validate_config(format="yaml")`
  raise `TypeError` inside jsonschema; `audit unused -i yaml` raises `AttributeError`; yaml-new
  refuses with "Invalid input: a YAML int key at configuration has no JSON spelling". An
  unquoted `on:` key crashes `yaml` with `AttributeError` on `bool`; the schema tree holds one
  statement name YAML 1.1 loads as a non-string, `on` (10,459 names checked).
- Depth (`depth.py`, `a` nested N times under `configuration`, every reader x every writer,
  plus validation): JSON: `yaml` output fails from 450 (PyYAML's representer fed junoscfg's deep
  IR), set and structured from 600 (`dict_walker`), every writer at 1,600
  (`_normalize_annotations`); `audit unused -i json` at 1,600 (`_normalize_annotations`); JSON
  validation never crashes (invalid). `yaml`/yaml-new: refused below 490, PyYAML's composer fails
  at 600 (left by the rule). set and structured: no failure at 1,600 (the schema bounds
  placement). XML: converts at 70; lxml refuses with `InputError` from 300 (limit 256), so no
  junoscfg walk meets more than 256 levels from XML. `json.loads` itself fails past ~20,000.
- Leaf tags: `--path system.host-name` drops `@host-name` (inactive, protect) in set,
  structured, json, yaml, yaml-new; `--path system.domain-search` drops `@domain-search`;
  `--path system.syslog` (container, `@` inside) and `--path interfaces.interface` (entry `@`
  inside) keep their tags. Cause: `display.filter_dict_by_path` rebuilds `{key: value}` and
  leaves the sibling `@key` behind. Relative leaf selections at base: set `set r1`, structured
  `r1;`, json `"r1"` (no tag).
- Ancestor tags (C3): `deactivate system`, `--path system.host-name` writes the leaf active in
  every writer (not acted on).
- Device-corpus selections (`probe_selections.py`, every mapping-key path to depth 5 over the
  six JSON captures, five writers, absolute and relative): base recorded in `probe-base.json`.

## Non-goals

Relative selections (SC1 records the leaf case); ancestor tags on the path; parser limits
(PyYAML ~490, `json.loads` ~20,000, lxml 256); `from_dict` handed a deep IR directly.

## Acceptance criteria

- Every test id in the three deltas exists, failed at base for the defect it pins (or, for a
  guard of unchanged behaviour, passes at base and head), and passes at head.
- `probe_selections.py` at head against base: absolute outputs differ only for selections
  whose last key has a sibling `@key` in the IR, each difference adding exactly that tag;
  every relative output identical.
- The depth matrix at head: no `RecursionError` from junoscfg code for JSON at any depth
  `json.loads` parses; the other rows unchanged.
- Existing tests pass, the two C2 tests and `test_json_input_past_64_levels_is_refused_as_yaml_new`
  updated as the deltas say.
- Independent Test/Challenge (high risk floor) recorded in review.md before implementation is
  final; the fresh Reviewer dispatched by the coordinator after the full check.

## Performance expectations

The JSON reader walks the parsed document once more, as yaml-new's reader does; measured on the
largest device capture at head against base and recorded; no other stage changes cost.

## Outstanding decisions

None blocking. C3 (ancestor tags) is reported to the owner as a pending decision.

## Execution and checkpoint

- Roles required: Builder; independent Test/Challenge; fresh Reviewer (coordinator);
  Finalizer (instruction-integrity.md, Assurance).
- Resume point: phase 4, tests first, observed failing at base `2d4904b`.

## Delta log

- Freeze established: proposal `0d5dc84`, deltas and codemap `291f427`.
- Tests `5c513a9` (red run `red-run.txt`, every new test failing for its defect, guards
  passing): two test ids kept rather than renamed so the main specs' `Tests:` lines still
  resolve (`test_without_scalars_only_a_cycle_or_depth_is_refused` keeps only string keys,
  keys move to `test_without_scalars_a_key_that_is_not_a_string_is_refused`;
  `test_a_key_that_is_not_a_string_is_named_by_its_kind` now pins the refusal). No criterion
  changes.
- Implementation: the relative guard failed for set (`set r1` became `set r1`, `deactivate`,
  `protect`): the acceptance criterion "every relative output identical" conflicts with the
  approved relative requirement. Recorded as SC1 (review.md), pending owner decision; interim
  action fixed by that requirement; the guard became
  `test_a_relative_leaf_selection_writes_its_tags_as_a_container_does` and the delta says so.
  `test_a_relative_yaml_new_selection_is_measured_as_written` reads its 67-level IR from XML,
  since the JSON reader now refuses it (its assertion unchanged).
- Probes at head: absolute outputs differ in 25 of 2,875 selections, each adding exactly the
  last key's sibling annotation (21 object outputs verified structurally,
  `verify_tag_only.py`; set and structured add the `deactivate` of the `l3vpn` flag);
  relative outputs differ in 2 (SC1). Depth matrix: JSON refused with ValueError at every
  depth past 64 in every writer, every other row unchanged (`depth-base.txt`,
  `depth-head.txt`). JSON reader on the largest capture (220 KB): `to_dict` 2.8 to 4.2 ms,
  json to set 9.3 to 10.5 ms (`perf.txt`).
- Test/Challenge delta (review.md 1 to 13): criteria widened within the outcome, not beyond
  it. SC2 (measured RecursionError from XML, owner instruction "fix them under the same rule
  if so") brings the XML reader under the 64-level rule, and SC3 brings JSON validation in
  line with yaml and yaml-new validation; the non-goals "XML depth below lxml's 256" and
  "JSON validation" are withdrawn. The selected-statement requirement names flags and a
  list's own comment (device corpus). Invalidated: the implementation commit's evidence and
  the probes; reruns: tests (red against base `red-run-2.txt`), probes, full check.

## Scope and completion

Outcome: no traceback for a non-string `yaml` key or deeply nested JSON at any conversion,
validation or audit door, and an absolute leaf or leaf-list selection that loads with the
meaning its parent selection gives it. Exclusions as Non-goals. Applicable existing
requirements: conversion/path-filtering (relative selections unchanged), junos-json-yaml (the
64-level rule), validation/junos-json-yaml.
