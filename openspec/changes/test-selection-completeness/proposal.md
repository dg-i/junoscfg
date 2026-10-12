## Why

Ordinary commit checks silently select no tests for tooling scripts and shared corpus inputs, undermining efficient focused verification.

## What Changes

Select the tooling suite for tooling code/configuration and the full default suite for shared test data; preserve package/importer selection.
Select an existing containing test directory for deleted test files and conftests, and always invoke the selector hook so deletion-only commits are checked.
Remove descendant selections already covered by an ancestor directory to avoid duplicate pytest collection.

## Capabilities

### New Capabilities

- `schema-pipeline/test-selection`: ordinary repository pytest selection; operational tooling grouping, no runtime schema behavior.

### Modified Capabilities

None, because ordinary affected-test selection has no existing capability spec.

## Non-goals

No runtime, qualification admission/caching, CI matrix, test-oracle, grammar or public surface changes. No heuristic fixture dependency map.

## Impact

`tools/affected_tests.py`, its hook and tests, and `tests/CONTRACT.md`. No declared zone owns tooling; surface is an administrative grouping (existing batch-process-config precedent).

## Completion

Owner-approved optimization plan: tooling and shared data cannot silently skip verification; removed tests select existing targets; documents remain cheap; ancestor selections do not duplicate tests. Parent coordinates full check, fresh review, merge and archive.
