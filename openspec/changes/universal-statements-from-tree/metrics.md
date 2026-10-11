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
| workflow telemetry by phase and model | UNMEASURED |
| residue-arm firings, and additions a fixer made beyond the proposal | UNMEASURED |
| requirement-to-test reconcile result | UNMEASURED |
| pre-commit wall-clock, total and per hook | UNMEASURED |
| regeneration on the base (`junoscfg schema generate` from `25.2R2-S1.5_qfx5120.xsd`) | dd7c8c4: structure tree, grammar and both JSON schemas byte-identical to the committed artifacts (3 min 33 s) |
| output measurement over `tests/data` (`outputs.py`, 236 conversions) | 18 differ, each explained: 12 `apply-flags omit` placed from set/curly (12 `UNPLACED` warnings removed, none added), 6 XML to JSON/YAML nested single-group `apply-groups` now a list as the device writes it |
| output measurement over the JVD clone (`outputs.py --jvd`, 4,605 conversions) | 11 differ, all curly output: nested two-group `apply-groups` written `[ A B ]`; set, JSON and diagnostics identical; curly round-trip differences 51 lines on base and head alike |
| curly writer probe (`tc_probe_via_structured.py`) | base 96 lines, head the same 96 lines |
| device door probe (`tc_probe_doors.py`) | base 28 differences from the device's JSON, head 0 |
| regeneration at the head | structure tree changes `apply-flags` only; grammar its alternative and `apply_flags`; a second regeneration byte-identical |
| timing, median of 3 (largest JVD file curly to set/JSON; 40,000-line set list to set/curly) | base 4.94/5.27/1.44/1.67 s; head 5.01/5.35/1.52/1.75 s (after caching a tree's universal statements; 5.38/5.73/1.93/2.17 s before) |
| schema tier / JVD tier | 34 passed, 2 skipped / 8 passed |
| Context expansion: src/junoscfg/display/constants.py, src/junoscfg/display/to_yaml.py | the helper and the XML reader, kernel modules outside the slice |
| Context expansion: src/junoscfg/convert/input/set_input.py, src/junoscfg/convert/input/normalization.py | readers that resolve a child by key |
| Context expansion: src/junoscfg/convert/output/dict_walker.py, structured_output.py, json_output.py | writers that resolve a child by key; the Group-H helpers' one consumer |
| Context expansion: src/junoscfg/validate/xsd_fixes.py | the apply-statements fix |
| Context expansion: src/junoscfg/convert/field_validator.py, src/junoscfg/validate/schema_generator.py, tools/check_test_doors.py, tests/data/name-keyed.lark | consumers of the tuple; the tripwire's door exception; the pinned grammar |

Machine evidence and per-field provenance: [metrics.json](metrics.json).
