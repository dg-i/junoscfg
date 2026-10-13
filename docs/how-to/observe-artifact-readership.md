# Observe artifact readership before simplifying a workflow

Use a bounded observation when considering removal of a change artifact type.
This is an operator observation protocol, not automatic telemetry or permission
to skip required artifacts. Keep application-specific release choices and results
in an application-owned observation report.

## Define the cohort before observing

Choose consecutive release tags on the target branch and record their immutable
commit IDs. Start only when the baseline tag exists. Require baseline ancestry
and no live change directories at either boundary; otherwise use another period
or explicitly account for every straddling change before drawing conclusions.
List the expected phases, artifact types and participating agent/human roles in
advance. Include review, finalization and integration consumers, not only builders.

At closure, inventory archived changes from metrics files first added between the
two tagged trees. Use Git's committed trees, disable rename detection, and cross-check
against the change/archive inventory so missing metrics cannot hide a change.
Inspect the closing tree, not the current checkout. An empty cohort is inconclusive.
Retain both commit IDs, the cohort file list and any boundary exceptions in the report.

## Record observed reads

Record exact repository-relative paths in each change's `metrics.md` row named
`distinct files read per phase, by artefact type`. Use a JSON object mapping phases
to artifact types to sorted, unique path lists; for example:

```json
{"implement":{"proposal":["openspec/changes/example/proposal.md"],"tasks":["openspec/changes/example/tasks.md"]}}
```

This example covers only one phase and is not a complete observation. Keep
participant attestations and the expected phase/type inventory beside the metrics
as application-owned evidence. Union the observed paths across participants for
each phase/type while retaining who reported them, including human readers.
Record paths as read; retain a mapping when archival renames them.

An explicit empty list means a completely observed phase/type had no readers.
A missing phase/type, unavailable participant observation, invalid JSON or
`UNMEASURED` means unknown, never zero. Mark a legitimately inapplicable phase
with its reason in the coverage audit; do not silently omit it. Record reads as
they occur, not from the final diff or expected workflow order. Native session
logs can establish positive observations, but cannot establish complete readership.

Run [metrics capture](capture-change-metrics.md) after recording the manual row.
The existing command preserves it as operator-reported Markdown evidence; it does
not validate this protocol or independently verify completeness. Do not add fields
to the runtime/workflow telemetry importer or edit machine evidence to claim a
measurement it did not make. Retain the source observations for review.

## Audit coverage before proposing deletion

Parse each row as JSON and check the full phase/type/path shape, unique keys,
string paths and the declared inventory. A nonempty object alone is insufficient.
Audit every applicable phase and every participating role in every cohort change.
Count distinct paths and changes with at least one read per artifact type, and
record where each type actually existed. Retain incomplete observations explicitly.

An artifact type is a deletion candidate only when the entire cohort is covered,
the type existed in at least one change, and it had zero agent and human readers.
Also inspect current skills, gates, decisions and repository instructions: a
required input or evidence artifact remains required even without observed reads.
Check automated consumers as well as readers before proposing removal.

Open a separate `agent-ready-change` proposal for a qualifying candidate, with
the cohort, per-type counts, coverage audit and requirement/dependency inspection.
Observation alone never authorizes deletion. If coverage is incomplete or no type
qualifies, record that result; repeat only when the maintenance question warrants it.
