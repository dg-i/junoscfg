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
