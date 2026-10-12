## Why
Set metadata silently discards trailing scalar-leaf tokens and tags the broader leaf, with zero diagnostics even in strict conversion (private report.md and remaining-report.md in leaf-list-deactivation-current).
## What Changes
**BREAKING**: refuse those targets with a value-free ValueError in _apply_meta before annotation; bare whole-leaf commands, keyed entries and quoted keys remain supported.
One parameterized unit regression covers evidenced apply-groups/members targets and surplus host-name tokens across shared metadata verbs; source plus test stays within two files/thirty lines.
Device P9/device-probe.out and deactivate5.txt prove only per-value deactivate rejection; other scalar/verb refusals are toolkit IR limitations. Failure remains explicit refusal, never broadened output.
## Capabilities
conversion metadata correctness; fix lane, skip_specs: true, no delta or new capability, dependency, override or environment reader. Required news records the refusal; independent TC and fresh review are mandatory.
## Non-goals
No broad reader/metadata refactor, new device semantics, absent-target repair, schema generation or XML work. Remove the unsupported command and retain set lines; whole-leaf targeting is an alternative only if intentionally requested.
