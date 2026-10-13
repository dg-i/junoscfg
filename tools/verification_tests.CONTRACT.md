# verification_tests — contract

Application-owned full default test execution and combined coverage; the native
engine owns admission, capacity, checkpoint receipts and tier evidence.

- Execute every live collected test exactly once across workers; compare complete
  collections and require a disjoint exhaustive assignment and actual phase reports.
- Preserve assertions, strict xfails and real skip outcomes. No worker, collection,
  setup, call, teardown, report or coverage failure can produce success.
- Cost hints control placement only. Unknown tests remain assigned; product modules share
  worker-local fixtures. Worker pytest caches, result files and coverage are unique.
- Aggregate all coverage data once and enforce pyproject.toml's unchanged floor.
  Reject inherited test-selection or coverage-configuration overrides.
- The native full command alone may suppress its redundant affected-test hook.
  Normal focused/commit verification remains authoritative outside that command.
- No test-result cache, schema qualification, receipt policy or partial-suite mode.

verification_shard is the worker plugin for this adapter; it records collection
and executed reports and never decides whether a test is required.
