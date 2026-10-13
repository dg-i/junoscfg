<!-- Maintained by the agent-ready template. Local edits can conflict with updates.
See docs/how-to/template-ownership.md before editing; review every update diff. -->

# Phase 6 — Specs

## Outcome

Every capability directory sits under the directory of its domain, named
exactly as the domain's key in `[tool.template.domains]`, and `agent-ready
specs` and `agent-ready reconcile` pass or carry a baseline with an expiry.
The copy already configured OpenSpec: `openspec/config.yaml` names the
template's schema, `agent-ready`, whose artefacts and templates sit under
`openspec/schemas/`, and `openspec/specs/` and `openspec/changes/archive/`
exist. There is no index file: `openspec list --specs` is the inventory, one
line per capability with its requirement count. OpenSpec's telemetry is off,
`OPENSPEC_TELEMETRY=0` in the shell that runs it, as the shipped CI sets it.

A domain's spec is `openspec/specs/<domain>/spec.md`; above its cap it splits
into `openspec/specs/<domain>/<capability>/spec.md`. OpenSpec refuses a
capability directory with no requirement in it, so a directory there is a spec,
never a placeholder, and an empty domain directory is nothing at all.

## Greenfield

Write an initial spec per domain from the interview: a Purpose someone wrote,
requirements with EARS criteria, each naming at least one acceptance test id.
Lite spec is the default. `openspec validate --specs` and `agent-ready reconcile`
pass.

## Brownfield

On a brownfield repository this phase usually writes nothing: the
configuration arrived with the copy, and the first spec arrives with the
change that needs it. Reference canonical executable specs and generated
relationships without copying their values. Write requirements for promises
that need change history. Do not backfill specs for existing behaviour. Specs
arrive per change, as deltas whose reviewed main-spec edits are applied before
merge using a disposable OpenSpec archive. Post-merge archive uses
`--skip-specs`.

Backfilling looks productive and is not: a spec written from code says what the
code does, which the code already said, and it will be wrong in exactly the
places where the code is wrong. The behaviour that matters is pinned in phase 3,
by tests, which is the form that fails when it stops being true.

The exception is a domain about to be changed substantially. There, write the
spec for the part being changed, as part of that change rather than here.

A repository that already carries OpenSpec specs keeps them and moves them: with
no live change open, `git mv` each capability under the directory of its
domain, a capability named like a domain becoming that domain's own `spec.md`.
Keep the existing `openspec/config.yaml` and set its `schema` to `agent-ready`.
Archived changes keep their old delta paths; they are history and are never
applied again. Requirements written before the `Tests:` line name no test:
`agent-ready reconcile --write-baseline` records them under a `reconcile` gate
in warn mode with an expiry, and each gains its test id on first touch. A capability that fits no domain, or spans two, is evidence
about the domain table, not a filing problem: ask question 4, and where the
human has not decided, leave it flat and record it with `agent-ready specs
--write-baseline` under a `specs` gate in warn mode with an expiry. Its deltas
take every domain owner until it moves, which the rendered `CODEOWNERS` says.

Install the spec tool's own skills and commands only if the human wants them:
they add always-loaded descriptions that `agent-ready budget` counts, and they
land outside the skill source tree, so list their glob under `vendored-skills`
in `pyproject.toml` for the mirror check to leave them to their upstream.

## Questions you must ask

1. Which domain is changing next? That is where a spec earns its cost.
2. Is there existing written specification, anywhere, that should become the
   starting point rather than being rediscovered?
3. Does any domain boundary from phase 1 look wrong now that you see it as a
   spec tree?
4. For each capability that fits no domain: whose owners should review a change
   to that behaviour? That names the domain. A capability nobody claims stays
   flat, under the baseline, with a date.

## Approval

The human approves the capability placement and every baseline entry with its
expiry. Question 3 can send you back to phase 1; that is cheaper now than after
the specs exist. Stop here: the next phase is a new session, and `agent-ready status` resumes it.
