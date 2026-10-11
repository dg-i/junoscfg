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
| Context expansion: src/junoscfg/display/to_yaml.py | the owning XML walker; `display/` is in no `[tool.template.domains]` entry, so the conversion-domain slice does not list it |
| Context expansion: tests/unit/display/test_to_yaml.py | the walker's unit tests, where the regression test belongs (`tests/CONTRACT.md`) |
| Context expansion: tests/corpus/test_device_renderings.py, tools/device_differences.py, tests/data/device/known-differences.json | the device law and the class the fix removes |

Machine evidence and per-field provenance: [metrics.json](metrics.json).
