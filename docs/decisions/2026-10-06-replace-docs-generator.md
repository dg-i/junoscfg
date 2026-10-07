---
status: proposed
scope: ["docs/**", "mkdocs.yml", "tool.template.toolbox"]
enforced-by: none
review-by: 2027-04-06
---

# Replace the mkdocs documentation stack

## Context

mkdocs has had no release since 2024-08-30 and its repository was last pushed
on 2025-10-20, with 192 open issues. Measured in onboarding phase 2 alongside
the rest of the toolbox, it is the only entry whose activity data fits
abandonment rather than completion.

The theme and the API-reference plugin are both healthy — mkdocs-material has
1 open issue and was pushed 2026-10-02, mkdocstrings 6 and 2026-10-03 — but
both are mkdocs *plugins*. They cannot outlive the generator they load into, so
this is one decision about three dependencies, not a choice among them.

## Decision

Replace the generator. Until a replacement is chosen all three entries stay
approved in `[tool.template.toolbox]`, because the site builds today:
`mkdocs build --strict` is clean.

The binding constraint on any replacement is the API reference, not the theme.
`mkdocs.yml` carries over thirty nav entries under `api/internals/` that
mkdocstrings generates from docstrings; a generator that cannot reproduce those
from the same source makes this a documentation rewrite rather than a swap.

## Consequences

- Retires `mkdocs`, `mkdocs-material` and `mkdocstrings` together, plus the
  `docs` dependency group and `mkdocs.yml`.
- Rule 5 of the documentation checklist in `AGENTS.md` names `mkdocs.yml` and
  its `nav:` section by path; it has to be reworded with the replacement, and
  phase 7 should not harden that wording in the meantime.
- Nothing is enforced by a check: no tool can tell that a generator has stopped
  being maintained. The `review-by` date is the only thing that brings this
  back, and it is set to the stage review so there is one date to keep, not two.
