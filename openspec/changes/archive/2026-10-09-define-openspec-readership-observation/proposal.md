## Why

The simplification roadmap allows proposing removal of OpenSpec artifact types
only after measuring their readership for one release. Existing archived
metrics contain no bound readership evidence, and the release that would start
the observation has not been tagged, so the repository needs a reproducible
protocol that distinguishes zero readers from missing telemetry.

## What Changes

- Define the release-bounded cohort, evidence sources, coverage rules, and
  aggregation procedure for OpenSpec artifact readership.
- State that unmeasured or incomplete evidence disqualifies an artifact type
  from deletion rather than counting as zero readership.
- Record the current pre-observation baseline and the two release boundaries
  that must exist before any deletion proposal.
- Update the simplification roadmap to distinguish the completed documentation
  reduction from the pending release-long observation.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- None. This change documents a maintenance measurement; it does not alter
  product or workflow behavior.

## Reader and task

The reader is the maintainer deciding whether an OpenSpec artifact type can be
removed. They must be able to run the observation for one full release cohort,
audit its coverage, and either open an evidence-backed deletion proposal or
retain every artifact type.

## Non-goals

- Do not claim that the observation period has started before its baseline tag.
- Do not infer a reader count from current `UNMEASURED` metrics.
- Do not delete, merge, or make optional any OpenSpec artifact type in this
  change.

## Impact

The change updates the metrics how-to and the saved simplification roadmap.
There is no runtime, dependency, API, CLI, test, or executable configuration
impact.
