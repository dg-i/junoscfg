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
| Context expansion: tests/test_integration.py (lines 128–165) | phase-6 review: the only other `assert … <` in `tests/` is a line-count ratio, which keeps row 5's "only committed bound" claim true |
| Context expansion: tests/conftest.py (`schema_dump`, `find_xsd_source`) | phase-6 review: the schema tier parametrises over every dump in one run (finding 6) |
| Context expansion: src/junoscfg/validate/set_validator.py (head), src/junoscfg/validate/data/ listing, git log of set_validator.py | phase-6 review: the grammar's runtime path missing from the tier table (finding 2) |
| Context expansion: openspec/changes/identifier-key-fields/review.md, metrics.md, tasks.md (figures only) | phase-6 review: rerun "three High findings after a green full check", "five probe rounds", tasks 4.4 and 5.6 |
| Context expansion: docs/how-to/capture-change-metrics.md, pyproject.toml `[tool.template]`, `[tool.template.domains.*]`, `[tool.template.zones.anonymize]` | phase-6 review: the "v0.7.8" figure (unproven, finding 8) and task 1.21 |
| Context expansion: src/junoscfg/display/__init__.py (`__all__`), tests/test_field_validator.py, tests/test_xsd_parser.py, tests/test_anonymize/test_walker.py, test_ip_rule.py, test_integration.py, tests/test_characterization.py, tests/test_set_input.py (cited classes) | phase-6 review: quoting the assertion behind every contract invariant and the five meta-command ids |

Machine evidence and per-field provenance: [metrics.json](metrics.json).
