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
| Context expansion: private_test_data/identifier-key-fields-device-checks-3.out, -4.md (filtered, prompts and pre-existing device lines masked) | phase 4: shapes for the device-truth fixture and the three unprobed round-4 predictions; no device value copied |
| Context expansion: src/junoscfg/__init__.py, src/junoscfg/anonymize/rules/__init__.py, src/junoscfg/anonymize/config.py | phase 4: the public doors the acceptance tests drive (`convert_config`, `validate_*`, `Rule`, `AnonymizeConfig`) |
| Context expansion: tests/test_schema_data.py, tests/schema_data.py, tests/test_round_trip_validates.py, tests/test_xsd_parser.py, tests/test_schema_generator.py, tests/test_json_yaml_validator.py, tests/test_cli_validate.py, tests/test_audit/test_types.py, tests/test_audit/test_regressions.py, tests/test_anonymize/test_walker.py | phase 4: existing classes and fixtures the new tests extend |
| Context expansion: examples/router1.*, tests/data/set_corpus.txt | phase 4: the `name`-keyed byte-identity pins |
| Context expansion: .venv agent_ready_checks/lane.py | phase 4: whether the merge-base check applies to the standard lane (it is the fix lane's) |
| Context expansion: src/junoscfg/audit/engine.py, src/junoscfg/audit/registry.py, src/junoscfg/audit/data/unused-types.yaml | phase 5: how a reference is matched, to tell `as-list X` from `as-list-group X` |
| Context expansion: src/junoscfg/anonymize/rules/sensitive_word.py, src/junoscfg/anonymize/rules/__init__.py | phase 5: why an enum key reached a substring rule |
| Context expansion: tests/test_set_corpus.py, tests/test_jvd_corpus.py, tests/conftest.py | phase 5: corpus and dump tiers run against the change |
| Context expansion: master's src and artifacts (git archive into the scratchpad) | phase 5: measured that master's own generator does not reproduce the shipped JSON and YAML schemas |
| Owner-directed addition: evidence hierarchy in docs/architecture/developer-guide.md and conversion-bugfix-guide.md | relayed mid phase 5; ARCHITECTURE.md and settle-a-schema-question.md checked, no contradicting sentence |
| Owner-directed addition: device round 4 (R, S, T) captures and tests, key keyword on either side | relayed mid phase 5 |
| Addition beyond the proposal: `entry_key_names()` in `junoscfg.display` | phase 5, accepted by the owner: the flattened key-name set eight sites need; derived only from `entry_keys()` |
| Addition beyond the proposal: `_fix_groups` gives `group` a `name` key child and clears `is_presence` | phase 5, accepted by the owner as required by the regeneration: the anonymizer offers group names through the tree's `name` leaf, and master's generator makes `groups` a presence node, which the shipped schema was not |
| Addition beyond the proposal: anonymize walker passes enum values unchanged | phase 5: required by `test_an_enum_key_passes_unchanged`; anonymizer-bugs row 4 |
| Owner-directed addition: "Junos correctness" defined in ARCHITECTURE.md §1, "Evidence hierarchy" in §8 (with §3 aligned), pointer in AGENTS.md | written by the orchestrator at the owner's direct request before phase 6; AGENTS.md kept at its 100-line cap |
| Context expansion: master's src and artifacts (git archive 588d16a into the scratchpad) | phase 6: before/after runs of the reader, writer, validators, schemas and grammar |
| Context expansion: private_test_data/schemas/25.2R2-S1.5_qfx5120.xsd | phase 6: `maxOccurs` census (385 numeric declarations above 1) behind finding 1; no value copied |
| Context expansion: private_test_data/jvd, private_test_data/captures | phase 6: structured-to-set corpus pass on both trees (unplaced 69,768 to 68,227; other field diagnostics 521 to 11,984); set-output diff of 124 files |
| Context expansion: tests/test_set_corpus.py, tests/test_jvd_corpus.py, tests/jvd_data.py, tests/test_device_truth.py | phase 6: the OVER_REJECTED edit, the field-warning budget, the corpus loader and the `.conf` rerooting used for the four-door check |
| Context expansion: src/junoscfg/convert/__init__.py, src/junoscfg/__init__.py | phase 6: `convert_config_result`, the door that carries field diagnostics |
| Context expansion: ~/src/ansible-collection-junos-config (read-only, symlinked into a scratchpad namespace) | phase 6: 33 passed against this checkout from a throwaway virtualenv; the collection tree untouched |

Machine evidence and per-field provenance: [metrics.json](metrics.json).
