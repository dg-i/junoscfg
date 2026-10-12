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

Machine evidence and per-field provenance: [metrics.json](metrics.json).

| Context expansion: src/junoscfg/input.py | Shared lexical boundary outside conversion/validation domain slice |
| Context expansion: src/junoscfg/cli.py | Verify convert/import/validation/audit caller failure codes; no edits |
| Context expansion: src/junoscfg/__init__.py | Verify named conversion and validation doors; no edits |
| Context expansion: src/junoscfg/audit/__init__.py | Confirm audit consumes parsed IR; no edits |
| Phase 4 focused acceptance | Initial 41 failed/7 passed; independent-door expansion 77 failed/7 passed on unchanged runtime base |
| Phase 4 operational exception | Root-authorized SKIP=affected-tests only for deliberate red acceptance commit; other hooks required |
| Context expansion: docs/api/input.md | Root-approved documentation extension for new shared helper and actual existing exports |
| Context expansion: mkdocs.yml | Root-approved exact new input API nav entry; no edit yet |
| Phase 5 focused verification | 350 passed in0.75s including84 frozen acceptance; original diagnostic failure preserved and approved stronger assertion passes |
| Phase 5 preservation comparison | 0/96 plain and0/1152 per-rule outputs/diagnostics/exception records changed from detachedbbc125eb |
| Context expansion: tests/contract/test_every_message.py | Root-approved correction only of obsolete plain unsupported-command quotation fragment; all privacy/exit scans retained |
| Context expansion: tach.toml | Root-approved expose declaration only for already-approved shared helper; no module/layer/dependency changes |
