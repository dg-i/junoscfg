# Phase 1 — Intent

## Outcome

`openspec/changes/<slug>/proposal.md` approved: why, what changes, the
capabilities it touches, and the non-goals, ten to thirty lines; and the lane
fields the gate reads in `.openspec.yaml` beside it. Precision here is cheaper
than rounds later.

## Process

1. `openspec new change <slug>` creates the folder and its `.openspec.yaml`
   under the `agent-ready` schema; `openspec instructions proposal --change
   <slug>` prints the template.
2. Write Why and What Changes, then Capabilities: each as
   `<domain>/<capability>`, the domain a key of `[tool.template.domains]`, and
   an existing capability by its exact path under `openspec/specs/`.
3. Add the lane fields to `.openspec.yaml`, where OpenSpec keeps
   `skip_specs`: `type`, `zone`, `domains`, and `removes`, which may read
   "none, because ..." and never stays empty on the standard lane. The fix
   lane's metadata carries no `removes`. Non-goals are prose in the proposal.
4. In beta and release, a change touching a named surface adds a
   `declared-break` entry per surface there, with `why` the break is necessary
   and the `migration`: `declared-break: {api: {why: ..., migration: ...}}`,
   one key per surface. It takes the red approval column whatever the zone.
   A proposal that touches what a decision record governs cites the record's
   id, so a superseded or expiring decision is met here and not in the index.
5. A refactor, a stage-up or a bootstrap that changes no behaviour sets
   `skip_specs: true` in `.openspec.yaml`; never invent a requirement to
   satisfy validation. A bug, a feature or a pivot never sets it: a fix in a
   domain with no spec writes the first requirement for the behaviour it pins,
   and `agent-ready lane` refuses the flag on those types.
6. `openspec validate <slug>` passes, and `agent-ready fields` reports no
   unanswered field in `.openspec.yaml`.

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

## Approval

The human approves the proposal: the pull request review where the repository
has them, the commit where it has none.
