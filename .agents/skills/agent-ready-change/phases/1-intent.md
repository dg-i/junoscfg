# Phase 1 — Intent

## Outcome

With the phase-0 instruction record committed,
`openspec/changes/<slug>/proposal.md` approved:
why, what changes, the
capabilities it touches, and the non-goals, ten to thirty lines; and the lane
fields the gate reads in `.openspec.yaml` beside it. The initial `metrics.md`
evidence ledger exists, with unavailable values still `UNMEASURED`. Precision
here is cheaper than rounds later.

## Process

1. Re-read `instruction-integrity.md` and verify its owner-decision batch is
   resolved. Run `git status --short`; do not continue while governed changes
   sit outside `HEAD`.
2. Run `npx --yes @fission-ai/openspec@1.13.0 instructions proposal --change
   <slug>` to print the template created by phase 0.
3. Write Why and What Changes, then Capabilities: each as
   `<domain>/<capability>`, the domain a key of `[tool.template.domains]`, and
   an existing capability by its exact path under `openspec/specs/`.
4. Add the lane fields to `.openspec.yaml`, where OpenSpec keeps
   `skip_specs`: `type`, `zone`, `domains`, `removes`, and the phase-0
   `assurance`, which may read
   "none, because ..." and never stays empty on the standard lane. The fix
   lane's metadata carries no `removes`. Non-goals are prose in the proposal.
5. In beta and release, a change touching a named surface adds a
   `declared-break` entry per surface there, with `why` the break is necessary
   and the `migration`: `declared-break: {api: {why: ..., migration: ...}}`,
   one key per surface. It takes the red approval column whatever the zone.
   A proposal that touches what a decision record governs cites the record's
   id, so a superseded or expiring decision is met here and not in the index.
6. A refactor, a stage-up, a bootstrap, or a docs change that changes no
   behaviour sets
   `skip_specs: true` in `.openspec.yaml`; never invent a requirement to
   satisfy validation. A bug, a feature or a pivot never sets it; `uv run
   --locked --group dev agent-ready lane` refuses the flag on those types. Type
   `fix` uses the separate fix route and sets it true.
7. Run `npx --yes @fission-ai/openspec@1.13.0 instructions metrics --change
   <slug>` and create `metrics.md` from its table with every unavailable value
   `UNMEASURED`. This is the evidence ledger later phases append to; phase 7
   captures the final values and adjacent JSON.
8. `npx --yes @fission-ai/openspec@1.13.0 validate <slug>` passes. Before
   committing the changed records, run `uv run --locked --group dev agent-ready
   fields` and `uv run --locked --group dev agent-ready caps`; correct their
   diagnostics in the same working round. Commit the proposal, metadata, and ledger
   before phase 2 so every later gate reads the intended branch snapshot.
   Record phase 2 as the resume point; the Builder progresses automatically.

The human writes or approves the proposal; you draft from the human's intent
and ask about what you cannot derive. Types `stage-up`, `pivot`, and `spike`
read their body under `types/` before anything else is written.

## Stage

Alpha specifies the thinnest slice that answers the concept question, with
non-goals you propose, and one option rather than "both": an open choice goes
to a spike, never into the proposal as an abstraction. A feature that only
adds is a question back to the human. In beta and release a removal needs the
deprecation requirement first, and every break is declared here.

## Questions you must ask

1. What does this change remove? "Nothing" is an answer that needs a reason.
   A rejected alternative is not a non-goal: a road taken and abandoned goes
   in `design.md` or the decision record with the measurement that rejected
   it; a non-goal is what the change leaves alone.
2. Which domain owns the behaviour that changes, and does its spec exist?
3. Is this a fix inside the fix-lane caps, or a bug that needs the standard
   lane?
4. Does this change add an override, a fallback, a parameter or an
   environment read? Then name the resource it redirects, the file, the
   table, the directory, and search this repository for every place that
   resolves it: by its name, constant and concept words, and for the
   `__file__`-relative and bundled-resource loads that carry none of them.
   State the search in the proposal and list every reader it found under
   What Changes. In alpha the list reads "none", because a change there adds
   one choice and no option; an override wanted in alpha is a stage question
   for the human, not a search skipped.
5. For type `docs`, who is the reader, what task must the document let them
   complete, and which existing source is authoritative for every claim?

## Approval

The human approves the proposal: the pull request review where the repository
has them, the commit where it has none.
