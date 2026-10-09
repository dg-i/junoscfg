<!-- Capture before merge/archive with explicit base and code-head SHAs. Evidence and per-field sources live in adjacent metrics.json. A field without evidence stays UNMEASURED. -->

| Field | Value |
|---|---|
| tokens per phase, prefix and work | UNMEASURED |
| distinct files read per phase, by artefact type | UNMEASURED |
| agent-review findings by severity, and how many survived human review | UNMEASURED |
| human artefacts read and human minutes per phase | UNMEASURED |
| wall-clock from intent to merge | UNMEASURED |
| lines added and removed | UNMEASURED |
| dependency count | UNMEASURED |
| direct declared runtime dependencies | UNMEASURED |
| total root-lock packages | UNMEASURED |
| runtime tokens | UNMEASURED |
| runtime files read | UNMEASURED |
| runtime retries | UNMEASURED |
| runtime phase span | UNMEASURED |
| residue-arm firings, and additions a fixer made beyond the proposal | UNMEASURED |
| requirement-to-test reconcile result | UNMEASURED |
| pre-commit wall-clock, total and per hook | UNMEASURED |
| Context expansion: src/junoscfg/validate/xsd_parser.py | owns the root cause, `_build_from_complex_type`; below the slice's cut |
| Context expansion: src/junoscfg/display/constants.py | `ENTRY_KEY_OVERRIDES`, `get_flat_entry_config`, `_FLAT_ENTRY_KEYS`: the kernel the helper joins |
| Context expansion: src/junoscfg/validate/xsd_fixes.py | `_fix_flat_entry_keys` mapping the retired `fe.k` and `values-only` |
| Context expansion: src/junoscfg/convert/input/set_input.py | the named-list, childless and `apply-groups` branches the no-silent-loss requirements name |
| Context expansion: src/junoscfg/validate/schema_generator.py | `_entry_keys` and the deliberate absence of `required` (specification challenge) |
| Context expansion: src/junoscfg/audit/walker.py | `_entry_key_field` fallback chain and enum-leaf skip |
| Context expansion: src/junoscfg/anonymize/walker.py | the synthesized `name` leaf |
| Context expansion: tests/conftest.py | which dump `--regen-schema` rebuilds the bundled tree from (the 25.2 train) |
| Context expansion: tests/test_set_input.py, tests/test_audit/test_walker.py, tests/test_grammar_generator.py, tests/test_device_truth.py | existing test classes the delta's test ids extend |
| Context expansion: openspec/specs/validation/set-command-validation/spec.md | the MODIFIED requirement repeats it whole |
| Context expansion: private_test_data/bugreport.txt | required behaviour and acceptance list; not committed, no value copied |

Machine evidence and per-field provenance: [metrics.json](metrics.json).
