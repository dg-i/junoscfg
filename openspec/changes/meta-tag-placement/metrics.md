<!-- Use this as the structure for your output file. Fill in the sections. -->
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
| workflow telemetry by phase and model | UNMEASURED |
| residue-arm firings, and additions a fixer made beyond the proposal | UNMEASURED |
| requirement-to-test reconcile result | UNMEASURED |
| pre-commit wall-clock, total and per hook | UNMEASURED |
| Context expansion: src/junoscfg/display/set_converter.py, config_store.py, constants.py, to_yaml.py | kernel modules the defects live in; display lies under no domain's paths |
| Context expansion: src/junoscfg/convert/output/dict_walker.py, structured_output.py | the structured writer; the slice listed modules below the cut |
| Context expansion: src/junoscfg/validate/grammar_generator.py | checked whether carrying a flag changes the grammar (it renames variants only) |
| Context expansion: private_test_data/anon/, anaon.conf, jvd/ | device layout evidence; the anonymized dumps carry an older junoscfg's layout |

Machine evidence and per-field provenance: [metrics.json](metrics.json).
