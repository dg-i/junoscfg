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
| requirement-to-test reconcile result | Pass: four requirements map to four existing test IDs |
| pre-commit wall-clock, total and per hook | UNMEASURED |

Machine evidence and per-field provenance: [metrics.json](metrics.json).

| Context expansion: tools/device_differences.py | Distinguish device-law classifier from record/diff tool; no edit |
| Context expansion: src/junoscfg/anonymize/CONTRACT.md | Public configuration type used by preserved optional record modes; no behavior edit |
| Context expansion: src/junoscfg/CONTRACT.md | Public conversion door; no surface edit |
| Batch id | nightly-makeover T4 |
| Batch review mode | isolated fresh review after implementation |
| Batch check executions | UNMEASURED |
| Batch integration-only findings | UNMEASURED |
| Batch escaped regressions | UNMEASURED |

| Prepared acceptance | 4 deliberate failures, missing shared tool; private reference 4 passed; not implementation evidence |
| Phase checkpoint | Phase 4 PREPARED / PARKED, root admission required before phase 5 |
