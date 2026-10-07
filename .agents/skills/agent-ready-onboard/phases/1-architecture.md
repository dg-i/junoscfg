# Phase 1 — Architecture

## Outcome

`ARCHITECTURE.md` section 8 answered; `[tool.template.zones]` and
`[tool.template.domains]` complete in `pyproject.toml`; `CODEOWNERS` rendered by
`agent-ready render codeowners`. `agent-ready fields` passes.

## Greenfield

Propose the layering from the interview, not from code that does not exist yet.
Two or three layers is usually right; more is a guess about a future you have
not seen. Write section 8 as the rules that hold everywhere: layering, error
handling, money, time, identity.

## Brownfield — evidence to gather

- The import graph, and every cycle in it. `tach` names the modules in a cycle
  but never an edge, so take the cycle path from `grimp` and propose the single
  edge to cut.
- Directory shape and naming, which usually encodes an intended structure that
  the imports have since violated.
- Churn per path over the last year, and how many people touched each area.
- What covers each area today: which test files exercise it, whether the
  acceptance path reaches it at all, and what it does that leaves the process —
  writes outside the repository, network calls, subprocesses. Structure tells you
  how the code is arranged; only this tells you what would go unnoticed.

Exclude from the evidence, or you will over-report: imports inside
`if __name__ == "__main__":` demonstration blocks, and imports under
`if TYPE_CHECKING:`. On one surveyed codebase the demonstration blocks alone
were 19 of 48 apparent violations; on another they were none of 42. Never assume
the share — measure it here.

## Brownfield — the proposal

Run `agent-ready scaffold zone <name> --path <glob> --owner <owner>` for each
zone you propose, and the same for domains. The paths and owners are what you
derived. A domain's key is also its directory under `openspec/specs/`,
character for character, so choose a key that reads as a path segment. `tier` and `intent` are written as sentinels because you cannot derive
them, and the check will fail until they are answered.

Present each zone with its evidence in one line: what it covers, how much it
changes, how many people touch it, and what it imports that surprised you.

## Questions you must ask

1. For each zone: what would a mistake here cost — an apology, a bad week, or a
   regulator? That is the tier, and it is nothing else: not how often the code
   changes, and not how well tested it is.
2. For each zone: active, frozen, restructuring, being replaced, or on its way
   out? Restructuring keeps the behaviour and changes the shape, so phase 3 pins
   it; being replaced keeps neither, so phase 3 leaves it. Your churn figure
   cannot tell these apart and will mislead you if you try.
3. For each cycle: is the edge I propose cutting the right one, or is the
   dependency real and the layering wrong?
4. For each domain: what is it for? The code shows what it does.

## Approval

The human approves the zone and domain tables and section 8. `CODEOWNERS` is
rendered from the approved tables with `agent-ready render codeowners`, never
hand-edited; `agent-ready render codeowners --check` is the gate that keeps it
so.

CODEOWNERS routes review; hosting settings make it mandatory. Inspect generated
warnings: exact paths union their owners; nested paths run broad to specific
and retain broader owners. Complex globs and basename rules may route extra
owners. GitHub accepts any one listed owner, so this does not require both
zone and domain approval. Agree the approval policy separately from routing.
