---
status: accepted
scope: ["src/junoscfg/input.py", "src/junoscfg/convert/input/json_input.py", "src/junoscfg/convert/input/yaml_input.py", "src/junoscfg/convert/output/json_output.py", "src/junoscfg/validate/json_yaml_validator.py"]
enforced-by: tests
review-by: 2027-04-15
---

# YAML nests at most 64 levels; aliases expand unbounded

## Context

Record 2026-10-15-yaml-new-expands-aliases-within-a-bound let yaml-new expand shared blocks
within two interim bounds: at most twice the parsed values, no deeper than the parsed
document. Both guarded against alias bombs, and both refused harmless files, such as a block
anchored beside `configuration` and aliased under it. The owner ruled on 2026-10-15, relayed
in the batch brief: "I do not want to fix PyYAML problems; if this is a genuine junoscfg
problem fix it, if not leave it. This applies to the yaml safeguards we have discussed as
well." An alias bomb is a property of YAML aliases and PyYAML. junoscfg's own recursive
stages crashing with `RecursionError` on a cycle or very deep nesting is a junoscfg problem,
in yaml-new's writer and in the `yaml` reader's meta-key cleanup alike.

## Decision

This record supersedes 2026-10-15-yaml-new-expands-aliases-within-a-bound.
`junoscfg.input.find_non_json_value` walks a document written out, every reuse of a block
included, with no size bound. It refuses a mapping or list reached inside itself (kind
`cycle`) and the first value more than 64 path steps below the document's root (kind `value`,
"is nested deeper than 64 levels"), each at its path and never with a value. The yaml-new
reader, writer (on the IR and on the object it writes) and validation call it; the `yaml`
reader calls it with `scalars=False`, so it refuses only a cycle and depth, outside the
`_ansible_*`/`_meta_*` keys it drops unwalked. 64 is the owner's figure. Measured at base `adb6fb7`: the
device corpus nests 17 levels, the shape catalogue 15, and the schema's deepest path 26
counting `configuration` and list indexes. Scalar aliases and merge keys are expanded by
PyYAML while loading (SC-B), left as they are and not backlogged.

## Consequences

junoscfg assumes its YAML input is not hostile. An alias bomb is expanded at every door and
can exhaust time and memory, so a caller handling untrusted YAML bounds it before calling
junoscfg. Any reuse of a block reads and writes. No junoscfg stage meets nesting deeper than
65 levels from a YAML door, so a cycle or deep alias chain is refused rather than crashing;
text nested past about 490 levels still fails inside PyYAML's loader first (left by the rule). A document
nesting deeper than 64 levels is refused, although no Junos configuration does. Raising the
ceiling is additive. JSON input keeps its own recursion (C6 of change yaml-depth-ceiling).
