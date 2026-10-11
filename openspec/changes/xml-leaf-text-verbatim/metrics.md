| Field | Value |
|---|---|
| tokens per phase, prefix and work | UNMEASURED |
| distinct files read per phase, by artefact type | UNMEASURED |
| agent-review findings by severity, and how many survived human review | UNMEASURED |
| human artefacts read and human minutes per phase | UNMEASURED |
| wall-clock from intent to merge | UNMEASURED |
| lines added and removed | {"added": 91, "binary_files": 0, "files": 5, "removed": 28} |
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
| Device-law measurement | Generated record: 716 to 712 lines, exactly four `xml-value-whitespace-lost` removals, zero additions. Exact base/head comparison: 8/96 plain and 96/1,152 total conversions change, all DEV-17 trailing-space restoration in the two XML captures; 24 YAML quoting cases verified by parsed values; zero diagnostic, field-validation or exception deltas. Source: tasks.md Current phase-5 completion evidence and private integration-summary.json; base `3ba9300a8a3d7d1bef713a8f202103ebc34e2c9b`, head `53c31f841576447857f6ff6332f8b3bd8a773e7e`. |

| Capture scope | Five product paths at base `3ba9300a8a3d7d1bef713a8f202103ebc34e2c9b` / code-full head `53c31f841576447857f6ff6332f8b3bd8a773e7e`; later main-spec commit `b45ce0631c9d8b2408fe4f0576ad9eb95c561b28` adds 46 lines separately. Evidence records excluded. |
| Runtime cost | UNMEASURED |

Machine evidence and per-field provenance: [metrics.json](metrics.json).
