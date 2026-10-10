## Why

The identifier-key-fields experiment showed agents reconstructing junoscfg's operative rules
from chat history: expensive test tiers are documented but never selected from the paths a
change touches, the invariants it settled are absent from the contracts read before an edit,
device evidence arrived as a chat stream, and the no-partial-application rule for metadata
verbs is tested but not traceable from its requirement.

## What Changes

- `docs/architecture/developer-guide.md`, "When to use each tier": the complete path-to-risk
  mapping with exact commands (XSD, schema model, fixes, artifact builder; set reader, grammar,
  field validator; cross-format IR, readers, writers; anonymization; entry lookup or a
  schema-wide walk) and the workflow-economy rule. Every existing mapping stays.
- `docs/how-to/solo-review.md`: a change crossing more than one of schema parser, artifacts,
  conversion, grammar, validation or anonymization always gets an independent adversarial
  corpus review, green gates notwithstanding.
- `src/junoscfg/{display,validate,convert,anonymize}/CONTRACT.md`: one settled invariant each,
  naming its public regression test, inside the 30-line cap.
- `docs/how-to/settle-a-schema-question.md`: the sanitized device-evidence form, carried by the
  generic evidence freeze.
- `conversion/entry-keys`: the kept-whole requirement names `deactivate`, `activate`, `protect`
  and `delete` on a partial or surplus key path and its five existing tests; traceability only,
  applied by the finalizer in phase 7 from the reviewed `main-spec-edit.md`.
- This change's telemetry is recorded in the workflow-telemetry format (`schema_version: 1`)
  that `docs/how-to/capture-change-metrics.md` describes and imported by `agent-ready metrics`.

No override, fallback, parameter or environment read is added.

## Capabilities

### Modified Capabilities

- `conversion/entry-keys`: "A statement the reader cannot complete is kept whole" gains the
  metadata-verb clause and test ids; behaviour is unchanged, so `skip_specs: true` stands.

## Non-goals

- Product code, generated artifacts, test behaviour, `pyproject.toml`, template-managed skill
  files, a second telemetry collector, device-probe timing (no router work here).
- The guide's stderr and "safe fallback" sentences (C7) and the Hypothesis mismatch (C6).
- Merge, tag, archive, publish, release.

## Impact

Readers: agents and contributors choosing gates before review, reading a contract before an
edit, or settling a device question. Sources: `ARCHITECTURE.md`, `tests/` for every cited id,
`tests/conftest.py` for the tier flags. Gates: `agent-ready reconcile`, `caps`, `lane`, strict
MkDocs, markdownlint, the one full checkpoint.
