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
reader and, since change own-crash-fixes, its validation call it with `scalars=False`, so
they refuse only a cycle, depth and a mapping key that is not a string, outside the
`_ansible*`/`_meta_*` keys left unwalked (`META_KEY_PREFIXES`). The `json` and `xml` readers
and JSON validation call it too since that change (owner request 2026-10-16): JSON past about
450 levels, and XML whose repeated elements double its depth, crashed junoscfg's own walks or
the PyYAML dump they feed with `RecursionError`. 64 is the owner's figure. Measured at base `adb6fb7`: the
device corpus nests 17 levels, the shape catalogue 15, and the schema's deepest path 26
counting `configuration` and list indexes. Scalar aliases and merge keys are expanded by
PyYAML while loading (SC-B), left as they are and not backlogged.

## Consequences

junoscfg assumes its YAML input is not hostile, a case of the project-wide rule
2026-10-15-configuration-input-is-trusted. An alias bomb is expanded at every door and
can exhaust time and memory, so a caller handling untrusted YAML bounds it before calling
junoscfg. Any reuse of a block reads and writes. No junoscfg stage meets nesting deeper than
65 levels from a YAML door, so a cycle or deep alias chain is refused rather than crashing;
text nested past about 490 levels still fails inside PyYAML's loader first (left by the rule). A document
nesting deeper than 64 levels is refused, although no Junos configuration does. Raising the
ceiling is additive. JSON and XML input share the ceiling since change own-crash-fixes, which closes C6 of change
yaml-depth-ceiling; text `json.loads` (past about 20,000 levels) or lxml (past 256) cannot
parse fails in the parser, left by the rule.
