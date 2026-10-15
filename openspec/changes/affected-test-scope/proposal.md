## Why

Ordinary commits select every tooling test for any tools-directory input, even
when a small, identifiable execution path owns the change. Coherent bookkeeping
commits can therefore repeat unrelated tests. The full checkpoint already removes
its duplicate affected hook, and schema scope is fixed in v0.28.14.

## What Changes

- Narrow defensible Junoscfg tooling selection with conservative unknown-input,
  configuration, fixture and deletion behavior; test both selection directions.
- Document focused, hook and full obligations, valid reuse, cheap gates and timing.
- Adopt independently reviewed shared workflow/evidence improvements through the
  supported updater after upstream integration; no application cache duplicate.
- Measure equivalent workloads with hooks, setup and failed attempts visible.

## Capabilities

- schema-pipeline/test-selection: execution-based ordinary tooling test scope.

## Non-goals

No weaker tests, coverage, schema qualification, independent review or hook bypass.
No consumer/CLI behavior changes, dependency pruning or revised timing targets.
No import of historical logs as native evidence; no push or unrelated work edits.
