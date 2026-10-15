## Context

`find_non_json_value` (kernel, `src/junoscfg/input.py`) is shared by the yaml-new reader
(`junos_yaml_to_dict`), writer (`dict_to_junos_yaml`) and validation
(`JsonYamlValidator.validate_yaml_as_json`). It makes two passes: an iterative count of the
parsed values and depth (`_as_parsed`), then a recursive walk (`_Walk`) charging copies
against a budget and the parsed depth. The `yaml` reader (`yaml_to_dict`) calls no check;
`_strip_meta_keys` recurses over whatever PyYAML built. PyYAML's composer recurses, so text
nested past about 490 levels fails inside `yaml.safe_load` at every door before junoscfg runs.

## Reuse ladder

| Candidate | Coverage | Gap | Maintenance signal, lookup date | Verdict |
|---|---|---|---|---|
| `find_non_json_value` (this repository) | the written-out walk, kinds, value-free paths, cycle detection | its two bounds; it checks JSON scalar types, which `yaml` input does not have | in-tree, 2026-10-15 | Extend: drop the counting pass and budget, add the fixed ceiling and a `scalars` switch |
| Standard library (catch `RecursionError`) | stops any crash | names no path, depends on the interpreter's limit and stack, also catches PyYAML's own failure (which the owner rule leaves) | stdlib | Reject |
| PyYAML options | none: no depth or alias limit in PyYAML 6 | | not looked up online (no web access in this session) | Reject |

## Decisions

1. **Rule.** A mapping or list reached again is a copy, walked at each place. One reached
   inside itself (on the open path) is refused as `cycle` where it is reached again. A value
   more than 64 path steps below the walked root is refused as kind `value`, reason "is
   nested deeper than 64 levels", at its own path (65 steps). In document order, the cycle
   test first. No size bound and no counting pass.
2. **Depth.** Path steps from the root the door walks: the loaded document for both readers
   and validation, `{"configuration": ir}` or the bare selection for the writer, so the
   number in a message is the number of steps in the path it prints. The walk stops before
   descending past 64, so it recurses at most 65 levels and every later recursive stage
   (`unshared`, the object stage, the dumper, `_strip_meta_keys`) meets the same bound.
3. **API.** `find_non_json_value(data, *, scalars=True, unwalked=()) -> NonJsonValue |
   None`. With `scalars=False` only cycles and depth are refused: the `yaml` reader's IR
   holds dates and other YAML scalars, and its non-string keys are outside the rulings (C5
   of the preflight). `unwalked` names key prefixes whose values the caller drops without
   walking; the `yaml` reader passes its `_ansible`/`_meta_` prefixes, so the check covers
   exactly what its own recursion walks (Test/Challenge SC1). No new exposed name. `NonJsonValue` gains a `where` property ("at P", "at
   the top level") so the three message builders stop repeating it.
4. **Doors.** yaml-new reader, writer and validation keep their call and message shape. The
   `yaml` reader checks after its mapping test and before `_strip_meta_keys`, and raises
   `ValueError("Invalid input: a YAML {kind} {where} {reason}")`, the yaml-new reader's
   wording, so a cycle reads "has no JSON spelling" in both: the IR is the JSON dict.
   `yaml` validation is unchanged (no junoscfg recursion; jsonschema judges the object).
5. **Records.** The superseding decision record, both guides, the API page, both contracts,
   the developer guide and ARCHITECTURE.md state the ceiling, the cycle refusal, and that
   junoscfg assumes its YAML input is not hostile; a caller handling untrusted YAML bounds it.

## Risks

- An alias bomb expands at every door, in the check walk and after it (accepted by the
  rulings, documented).
- Documents deeper than 64 levels that converted before are refused; none is a Junos
  configuration (schema 26, corpus 17, catalogue 15). A `yaml` file with such a value used
  as free-form data under an unknown key is refused instead of dropped.
- JSON input past 64 levels written as yaml-new is refused by the writer; written as JSON it
  is not, since the JSON writer is not a YAML door (C6 reports JSON input's own recursion).
- Text past about 490 levels still fails in PyYAML's loader, as at base (owner rule: left).
