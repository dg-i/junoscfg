---
status: accepted
scope: ["tool.template.always-loaded-budget"]
enforced-by: budget
review-by: 2027-04-06
---

# Raise the always-loaded budget to 4600

## Context

Installing OpenSpec's own tooling in onboarding phase 6 added 12 skills under
`.agents/skills/openspec-*` and 12 commands under `.claude/commands/opsx/`.
`agent-ready budget` then measured **4410 tokens against a budget of 4000**.

The measurement splits in a way that matters:

| Contributor | Tokens |
|---|---|
| `AGENTS.md` | 2818 |
| the 4 agent-ready skills | 276 |
| the 12 openspec skills | 792 |
| `.claude/commands/opsx/*` (gitignored here) | 524 |
| **total measured** | **4410** |
| **committed set** (what CI sees) | **3886** |

So the 4000 budget was not actually breached by anything in the repository: CI
clones without `.claude/`, measures 3886, and passes. The breach is local only.

Phase 7's `AGENTS.md` reorganisation is projected to take that file from 162
lines to its 70-line cap, about 2818 tokens to about 1218, which would put the
committed set near 2286 and the local measure near 2810.

## Decision

Raise `always-loaded-budget` from 4000 to 4600.

The number is not derived from the breach, which resolves on its own. It is
headroom: 4600 leaves roughly 1800 tokens above the projected post-phase-7
committed set, which is room for another tool's skills without this
conversation happening again.

## Consequences

- The gate stops failing locally today and keeps passing in CI.
- It also stops reporting a real signal for longer: at 4600 the set could grow
  by another 1800 tokens before anyone is told. The `review-by` is the backstop.
- Revisit at the review date with the post-phase-7 measurement. If the committed
  set is near 2286 as projected, 4600 is more headroom than this repository
  needs and should come back down.
