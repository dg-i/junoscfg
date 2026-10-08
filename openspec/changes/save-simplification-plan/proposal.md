## Why

The repository simplification audit produced seven evidence-backed follow-up
changes, but its plan currently exists only in conversation and would be lost
as durable project context.

## What Changes

- Add a short, ordered simplification roadmap under `docs/superpowers/plans/`.
- Record the compatibility constraints and verification gates that every
  future implementation change must preserve.
- Keep each recommendation as a separate future agent-ready change rather than
  treating this roadmap as approval for one sweeping refactor.

## Capabilities

No capability changes; `.openspec.yaml` sets `skip_specs: true`.

## Non-goals

- Implementing any of the seven simplification recommendations.
- Changing API, CLI, conversion, validation, anonymization, or audit behaviour.
- Deleting archived workflow artifacts before their readership is measured.

## Impact

Documentation and change records only; no named surface, dependency, resource
resolution rule, generated schema artifact, or runtime file changes.
