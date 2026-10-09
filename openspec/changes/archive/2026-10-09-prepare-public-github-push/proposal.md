## Why

The public repository still points documentation readers at the upstream
project and names its production consumer without a route to that public
consumer. Its simplification roadmap also sits under an internal-looking path.

## What Changes

- Link the production consumer to its public GitHub repository everywhere the
  current project documentation or source commentary identifies it.
- Point the documentation site's repository link at `dg-i/junoscfg`.
- Move the intentionally public simplification roadmap from
  `docs/superpowers/plans/` to `docs/roadmaps/` and preserve its navigation
  exclusion.

## Capabilities

No capability requirements change; this is repository metadata and
documentation organization, so the change skips delta specs.

## Non-goals

- Rewriting archived OpenSpec records that accurately name their historical
  artifact locations.
- Replacing the local `agent-ready-python` source before that project has a
  released, portable URL.
- Changing package behavior, public API, CLI behavior, or dependencies.

## Impact

Documentation, contributor metadata, comments, and one documentation path are
affected. No runtime behavior or named surface changes.
