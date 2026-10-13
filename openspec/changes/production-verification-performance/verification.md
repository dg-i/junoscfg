# Production verification evidence

Starting application master: `507a3dc74248ce2d670f6a5e27023d34990e6965`.
Starting shared engine main: `43433b033c0f2dc9565c071ccdda595b2d72a097`.
The original experiment is preserved at `f277c896582ccfb94787a02ff06fae4f896f236f`
on `codex/verification-timing-experiment`; its measurements are historical inputs,
not native production measurements.

## Environment and scope

Darwin arm64, Python 3.14.7, uv 0.12.18, 10 CPUs, 32 GiB memory.
Dependencies installed before measurement. Canonical command includes native
readiness/capacity, hooks, all applicable gates, complete ordinary suite, aggregate
branch coverage and selected real-schema tiers. Ten test workers and four native
gate workers are scheduling choices, not test selection. Real-schema tiers remain
serial with both public generation passes. No remote push will be performed.

## Assurance and selection

Independent application acceptance: 110 cases passed against pending native source
through PYTHONPATH; locked-dependency and canonical checkpoint results remain due.
See roles/test-challenge.md for executed negative controls and original failures.
The ordinary suite retains `test_bundled_conversion_preflight`, which invokes the
identical two real-schema conversion assertions against shipped artifacts without
rebuilding. Successful generation proof requires the generated artifacts to match
the shipped artifacts. This supplies inexpensive consumer compatibility assurance
when producers, inputs, environment and artifact integrity remain qualified.

Producer declarations cover extraction, XSD fixes, schema/grammar/tree generation,
shared constants, fixture/corpus inputs and dependency projection. Unknown paths,
invalid history, import-time consumer changes and unavailable valid context select
qualification. Native runtime identity must bind executable imports before reuse;
independent upstream review found two omissions, repaired in the immutable
pin `4e8f8faf44a77c1e59fcd351fd00dc02aa677a58`; fresh upstream review approved this exact revision.

## Preparation and trials

Production checkpoint trials are not yet run. Preparation, exact immutable candidate,
each trial, failures/retries and maxima will be recorded here after the native
candidate is reviewed and pinned. No production budget result is asserted yet.

Preparation: physical XSD copies isolated in this worktree; installed dependency
and refreshed projection/runtime metadata before trials. Dependency build reported
0.851 s (uv); exact combined installation/preparation wall time was not instrumented
and remains UNMEASURED. No recurring verification work was moved to preparation.

Locked acceptance run: `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest
tests/tooling/test_schema_selection.py tests/tooling/test_verification_tests.py
-q --tb=short` passed 110 cases in 15.43 s. Fields and caps passed.

## Integration repairs before timing

The first normal commit hook ran the full ordinary suite: 17 failed, 10,522
passed, 37 skipped, 20 xfailed and 16 fixture errors in 195.18 s. This was not
a canonical checkpoint trial. One old native selection fixture lacked its new
selector/runtime and correctly selected conservatively; the repaired fixture
retains version-only/dependency assertions and additionally checks uncertain
context. Receipt fixtures now reuse existing hook Git-environment isolation.
Those two files passed 91 tests under the reproduced hook Git index.

The other wrapper fixtures intentionally run tiny candidate repositories through
the installed editable application. New native engine policy correctly refused
that undeclared external editable root. The explicit `native_driver` fixture
observes the real installed project's complete driver identity while native
candidate manifests still bind the tiny repository. It changes no identity bytes,
execution, output or stability assertion. Ten generation/corruption/metadata/ledger
integration cases passed in 87.77 s. The native driver's own boundary is covered
by the independently reviewed upstream 774-test suite. Both template modes and
all upstream fast checks passed; upstream main was locally fast-forwarded to the
reviewed immutable pin. No remote writes occurred.

## First native checkpoint and relationship challenge

At immutable application candidate `c0590a69822b85ef7897486475b9154dc8b68cdf`,
first cold canonical checkpoint passed in **378.652666334 s**. Cold preparation
isolated the empty evidence location in 0.000076166 s. Every native gate passed;
ordinary suite: 10,555 passed, 37 skipped, 20 xfailed, 10,612 collected, 74.111 s;
combined coverage 92.96786389413988%, unchanged floor 91.47%. This candidate is
superseded by the source-boundary correction below; retain this trial, do not
count it among final-code repetitions.

Independent subsequent probes introduced and qualified a producer that called a
consumer function (and a module __getattr__ variant), then changed only that
consumer body. Regeneration changed schema additionalProperties, yet the original
selector omitted qualification. This is an implementation defect against existing
generation-independence criteria, not a request to change them. Current producer
imports/callback inspection found no such eligible consumer dependency; the gap
was allowing newly qualified source relationships to inherit that audit silently.

Repair: enforce an explicit reviewed source/configuration/dependency boundary.
Successful qualification cannot refresh this audit. Missing/stale/unknown audit
scope selects qualification. Root release versions and already-audited isolated
consumer bodies remain normalized. All current source paths and new/deleted paths
are compared; relevant wrappers and schema fixtures also remain bound. Independent
regressions execute the future-relationship counterexamples and preserve genuine
native receipt/hash/stability validation. Final review and final-code repeated
measurements remain required before application integration.
