## Resolved instructions

`instruction-integrity.md` C1 (type `refactor`), C2 (assurance values unchanged, record moved).

## Requirements

None: `skip_specs: true`.

## Evidence

- `docs/how-to/run-a-batch-of-changes.md` (v0.20.2): serialized list, schema tier commands, Assurance section.
- No reader of `[tool.template.batch]` or `[tool.template.assurance]` in `agent-ready-checks` 0.15.11 (source search); the skill reads them at phase 0 and in `batches.md`.
- `tomllib` parses the edited tables (inline table of the tier, arrays spanning lines).
- No code-map slice: no module under `src/` is touched.

## Non-goals

As in `proposal.md`.

## Acceptance criteria

`tomllib` reads the values; `mkdocs build --strict` shows the page in the nav with no "not in nav" notice for it; the one full checkpoint passes; `fields`, `caps`, `lane` pass.

## Performance expectations

None, because no runtime code changes.

## Outstanding decisions

None, because the owner named the values in rules 1, 3 and 8 and asked for no questions.

## Execution and checkpoint

- Assurance preference: economy
- Risk floor: normal
- Roles required: Builder; Finalizer (no Reviewer or Test/Challenge required)
- Resume point: phase 5 verification

## Delta log

- Freeze established with the proposal.
