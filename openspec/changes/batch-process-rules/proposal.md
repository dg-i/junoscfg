## Why

On 2026-10-11 the owner asked for the process speed-ups of the nightly makeover to be kept in
the repository's own instructions, and for the 45–90-minute JVD corpus tier to give way to
oracle checks over the committed device evidence. Today these rules live only in gitignored
briefs and the developer guide still sends set-reader changes to `--jvd`.

## What Changes

- New how-to `docs/how-to/run-a-batch-of-changes.md` (reader: the orchestrator and Builders of
  a batch; task: run several changes in parallel worktrees and verify each against device
  evidence). It carries rules 1–8 of the owner's task: serialized paths, the oracle checks with
  their source ((a) `tests/data/device/` or (b) `examples/junoscfg-oracle.*`) and exact
  commands per check, the `--schema` tier, worktrees, merge-time versioning, the lessons every
  change keeps, ledger and probe conventions, and the assurance preference.
- `AGENTS.md`: one Verification sentence and one "Where things are" row link the page.
- `docs/architecture/developer-guide.md` Testing Architecture and `docs/how-to/solo-review.md`
  (the Reviewer's report): the JVD tier leaves per-change evidence; the oracle checks replace it.
- New decision record (via `agent-ready scaffold decision`): the JVD tier is retired from the
  instructions and per-change verification, its code removal is the follow-up change
  `retire-jvd-tier`; cites the owner's request and its cost.
- The before/after comparison over the device captures, with the owner's method (delta of
  2026-10-11), and synthetic adversarial rows for changes that touch lexing.

## Capabilities

### New Capabilities

### Modified Capabilities

None: documents only, `skip_specs: true`.

## Non-goals

- The `--jvd` option, its tests and the nightly CI job: removed in the follow-up change `retire-jvd-tier` (owner, 2026-10-11 delta); no test is retired here.
- `mkdocs.yml` nav and the `pyproject.toml` settings (`[tool.template.batch]`, the assurance
  `record`) are the batch's next change, `batch-process-config` (lane gate, preflight C1, C2).
- Missing oracle tests (checks 1, 3, 5, 6) are test-only follow-ups T1–T4 in the ledger.
- Upstream-owned skill files are not edited; gaps go to `template-follow-ups.md`.

## Impact

Documents only. Every later change reads AGENTS.md and the how-to, so a wrong command there
costs every change; the QA runs each documented command once at the checked head.
