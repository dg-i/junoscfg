# Qualify parallel verification and selective expensive checks

Use this guide when optimising a measured verification bottleneck. The native
[admission and evidence](verification-evidence.md) protocol owns readiness,
capacity, receipts and conservative selector fallback. The application owns test
execution, fixture safety and the meaning of producer/consumer relationships.
Keep serial defaults until the proposed configuration passes these controls.

## Execute the complete suite

Prefer the application's existing runner. For pytest, evaluate
[pytest-xdist](https://pytest-xdist.readthedocs.io/en/stable/distribution.html) and
[pytest-cov](https://pytest-cov.readthedocs.io/en/latest/xdist.html) before writing an adapter; record an actual unmet requirement through
the normal dependency/reuse review. Worker count, placement and cost estimates
are application choices established by measurement, never template defaults.

Before declaring `full-suite = true`, establish that the configured `test-command`
executes every required test and enforces the existing coverage policy. Collection
alone is not execution. For a sharded adapter, require identical full collections,
a disjoint exhaustive assignment of live test identities, actual execution reports
and successful worker exits. New tests without cost hints must still be assigned;
hints change placement only. Reject missing, duplicate, foreign or stale reports,
partial collections, worker crashes and unexpected outcome values.

Account for setup, call and teardown separately. A skipped setup can legitimately
omit the call; a passed setup requires it. Preserve actual skips and expected
failures, strict unexpected-pass failures, and every assertion. Collection,
setup, call, teardown and reporting failures must make the full command fail.
Wait for all started workers and retain their diagnostics; on interruption,
terminate and reap children before releasing resources. A zero exit from a
coordinator cannot substitute for complete successful worker evidence.

Give each run and worker separate result paths, coverage data, pytest caches,
temporary files and writable fixture resources. Audit process-global caches,
environment overrides, ports and external services too. Share immutable inputs
only; scope expensive read-only fixtures deliberately and keep dependent tests
near them when useful. A session fixture is normally instantiated per worker.
Do not let one worker mutate another's input or consume an earlier run's output.

Aggregate coverage from the current completed run and apply the existing source,
branch and threshold settings once. Reject inherited test-selection or coverage
overrides that could weaken the declared complete suite. Keep coverage merge and
report failures fatal. An adapter's acceptance tests should execute small real
multi-worker suites: a new unhinted test, a worker/collection failure, failing
setup and teardown, legitimate skip/xfail, strict XPASS, and coverage below the
floor. Verify each negative control reaches the boundary it claims to test.

## Overlap only independent work

Use native `gate-workers`, `overlap-tiers` and `affected-test-hook` as described in
[bounded scheduling](verification-evidence.md#bounded-scheduling). Review shared
reads and writes before enabling overlap: runtime installation, generated inputs,
coverage output and fixture preparation are mutation barriers. Install/sync first;
concurrent commands use the prepared environment. Retain serial tier order where
one tier consumes another's outputs and bind those prerequisite bytes as inputs.
Keep genuine artifact stability passes separate from assertion execution; do not
remove an independent generation pass to save time.

Only the full invocation containing the complete suite may suppress its duplicate
affected-test hook. Commit, fast and docs-only checks retain their normal hooks.
Measure CPU and peak memory as well as elapsed time; choose bounded concurrency
that leaves headroom. Unknown resource costs and long-term flake rates stay
UNMEASURED. Roll back scheduling through configuration without waiving admission,
assertions, coverage, required tiers or failure reporting.

## Audit any negative selection decision

Start with broad conservative path selection. A custom `selection-command` may
return false only for a reviewed application-specific non-impact case. Unknown
paths, additions, deletions, renames, missing history, malformed source and changed
inputs, dependencies or runtime select expensive verification unless a specific
reviewed rule proves irrelevance. Ordinary compatibility tests still execute.

A producer/consumer exemption needs an audited relationship, not only an AST
comparison or a successful expensive run. Inspect imports, callbacks, registration,
decorators, defaults, class construction and other import-time execution. Record
the reviewed source/input/configuration/dependency boundary and bind it to the
bytes or narrowly justified normalization the classifier uses. Changes outside
that boundary invalidate the exemption. New successful producer qualification
does not establish that future consumer edits are independent; refresh the audit
only after reviewing that relationship. Preparation and qualification must never
silently refresh the audit. Keep domain rules and audit formats application-owned.

If nonselection depends on prior qualification, validate native successful evidence
against current inputs, outputs, dependency implementations and actual runtime.
Freshly prepared metadata is not proof. Compare historical source to the hashes
in that evidence; a convenient ancestor or same version string is insufficient.
Missing, stale, corrupt or incompatible proof selects the expensive tier. Avoid
an application-owned receipt cache. Add negative controls for changed producer
relationships followed by qualification, changed runtime followed by preparation,
missing proof, changed artifacts and source-history mismatch. Preserve uncached
integrity sentinels and native admission on every invocation.

## Measure the admitted workflow

Follow [verification improvement](improve-verification.md). Define cold, warm and
justifiably unselected workloads precisely. State which stores are reset and which
are retained; preserve immutable audit provenance when clearing reusable proof.
A warm observation must show valid native reuse, and an unselected observation
must exercise a real justified change rather than an artificial selector bypass.

Measure the canonical full command with normal hooks, admission, required prior
record commits and wrapper overhead. Report preparation, dependency installation,
queue delay and cleanup separately and state the end-to-end boundary. Record
immutable application and check-package revisions, interpreter, dependencies,
hardware, worker count, cache state, sample count, individual observations and
slowest run. Compare equivalent workloads with repeated observations; retain
failed setup attempts and superseded trials separately from successful samples.
Experimental harness results are not an admitted production baseline.

Report assertions, collected/executed outcomes, coverage settings and observed
coverage beside timing. Preserve missed targets and remaining uncertainty.
Happy-flow targets are desired timings, not hard limits, timeouts or automatic
failure thresholds. Record any hard limit separately with its explicit enforcement
policy; changing a target requires an owner decision, never a retrospective claim
that an originally missed target was met. These measurements demonstrate local
feasibility, not machine-independent guarantees or long-term reliability.
