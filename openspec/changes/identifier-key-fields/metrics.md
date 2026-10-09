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
| Context expansion: src/junoscfg/convert/output/dict_walker.py | `_emit_flat_entry`, `_emit_oneliner` and the `community-name` branch: today's one-line set rendering the writer requirement pins |
| Context expansion: src/junoscfg/display/to_yaml.py, src/junoscfg/convert/input/xml_input.py, src/junoscfg/convert/input/__init__.py, src/junoscfg/convert/input/normalization.py, src/junoscfg/convert/input/structured_input.py | the XML reader's array heuristics and the schema-backed normalization boundary the lone-entry wrap can use |
| Context expansion: src/junoscfg/display/CONTRACT.md, src/junoscfg/convert/CONTRACT.md, src/junoscfg/display/__init__.py | invariants for the XML walker and the exports the change removes |
| Context expansion: src/junoscfg/validate/xsd_extractor.py, private_test_data/schemas/25.2R2-S1.5_qfx5120.xsd, private_test_data/schemas/23.2R2-S7.5_vmx.xsd | reproducing the declared-order, second-choice and `oneliner-plus` measurements; no value copied |
| Context expansion: src/junoscfg/anonymize/rules/ip.py, src/junoscfg/anonymize/rules/community.py | rules keyed on the synthesised `name` path and type the anonymization delta replaces |
| Context expansion: docs/decisions/2026-10-09-scope-compatibility-to-production-consumer.md | the bans precedent and the secondary-door exemption for the two removed names |
| Context expansion: openspec/specs/conversion/raw-set-input/spec.md, openspec/specs/validation/raw-set-input/spec.md | checked for requirements the delta contradicts; none |
| Context expansion: tests/test_device_truth.py, tests/test_to_yaml.py, tests/test_anonymize/test_integration.py, tests/test_set_validator.py, tests/test_cli.py | capture-pair convention and existing classes the new test ids extend |
| Context expansion: change/entry-keys-from-the-tree openspec deltas (git show) | superseded requirements folded in: the two `community` lists |
| Context expansion: private_test_data/identifier-key-fields-device-checks.md, .out, .out2 | device probe results; prompts, hostnames and timestamps not copied |
| Context expansion: private_test_data/identifier-key-fields-device-checks-2.md, -3.md, -2.out (filtered, prompts masked) | round 2 and 3 probe plans and the rejected `route-filter ... next-policy` line; prompts, hostnames, timestamps and pre-existing device lines not copied |
| Context expansion: private_test_data/anonymizer-bugs.md | the owner's row 1 to decide; rows added; gitignored, not committed |
| Context expansion: src/junoscfg/validate/data/junos-structure-tree.json.gz | measured that no list node's own `tr` is an IP or `unreadable` type, so the synthesised `name` leaf's inherited type carried nothing |
| Context expansion: src/junoscfg/anonymize/rules/password.py, src/junoscfg/anonymize/rules/community.py, src/junoscfg/anonymize/rules/group.py, src/junoscfg/validate/schema_node.py | which rules read `tr` or match on a `name` path; grep only |
| Context expansion: tests/test_grammar_generator.py | `TestFlattenedRenderingsTakeARunOfValues` builds `flat-entry::values-only` and retires with `fe` |

Machine evidence and per-field provenance: [metrics.json](metrics.json).
