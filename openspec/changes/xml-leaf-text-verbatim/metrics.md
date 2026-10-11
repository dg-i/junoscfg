| Field | Value |
|---|---|
| tokens per phase, prefix and work | UNMEASURED |
| distinct files read per phase, by artefact type | UNMEASURED |
| agent-review findings by severity, and how many survived human review | UNMEASURED |
| human artefacts read and human minutes per phase | UNMEASURED |
| wall-clock from intent to merge | UNMEASURED |
| lines added and removed | {"added": 87, "binary_files": 0, "files": 3, "removed": 2} |
| dependency count | UNMEASURED |
| residue-arm firings, and additions a fixer made beyond the proposal | UNMEASURED |
| requirement-to-test reconcile result | UNMEASURED |
| pre-commit wall-clock, total and per hook | UNMEASURED |
| direct declared runtime dependencies | {"base": 6, "delta": 0, "head": 6} |
| total root-lock packages | {"base": 63, "delta": 0, "head": 63} |
| runtime tokens | UNMEASURED |
| runtime files read | UNMEASURED |
| runtime retries | UNMEASURED |
| runtime phase span | UNMEASURED |
| workflow telemetry by phase and model | UNMEASURED |
| Context expansion: src/junoscfg/display/to_yaml.py | the owning XML walker; `display/` is in no `[tool.template.domains]` entry, so the conversion-domain slice does not list it |
| Context expansion: tests/unit/display/test_to_yaml.py | the walker's unit tests, where the regression test belongs (`tests/CONTRACT.md`) |
| Context expansion: tests/corpus/test_device_renderings.py, tools/device_differences.py, tests/data/device/known-differences.json | the device law and the class the fix removes |
| Device-law measurement | the device law's recorded lines for XML input fall by 4 once task 2.3 regenerates the record (class `xml-value-whitespace-lost`, vMX and QFX5120 `junoscfg-oracle.xml`); before/after comparison over `tests/data/device/manifest.json`: 96 of 1,152 conversions differ, all explained by DEV-17 |

Machine evidence and per-field provenance: [metrics.json](metrics.json).
