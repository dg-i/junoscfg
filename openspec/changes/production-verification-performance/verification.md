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

All production trials, exact immutable candidates, failures/retries and maxima
are recorded below. The original preparation statement remains separate.

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
native receipt/hash/stability validation. Final review and final-code repeated measurements below close this obligation.

## Final production measurements

Product code: `44324d36bb489b13212e3f02be251429af41f95d`; later measured heads differ only in native audit events. All times are seconds. Total includes the whole canonical command and, where required, the prior native audit-event commit with normal hooks. Checkpoint is the command alone; no recurring verification was moved outside either number. Audit bookkeeping was not required before the first successful final-code cold run.

| Trial | Total | Checkpoint | Prior audit commit | Exit | Immutable measured head |
|---|---:|---:|---:|---:|---|
| cold-1 | 378.652666334 | 378.652666334 | 0.000000000 | 0 | `c0590a69822b85ef7897486475b9154dc8b68cdf` |
| cold-final-1 | 367.418987542 | 367.418987542 | 0.000000000 | 1 | `44324d36bb489b13212e3f02be251429af41f95d` |
| cold-final-2 | 376.120239583 | 376.120239583 | 0.000000000 | 0 | `44324d36bb489b13212e3f02be251429af41f95d` |
| cold-final-3 | 0.861036667 | 0.861036667 | 0.000000000 | 1 | `44324d36bb489b13212e3f02be251429af41f95d` |
| cold-final-4 | 381.742209625 | 380.787936792 | 0.941074250 | 0 | `d1e135fbcec8572621c2215df0406ce235cd67b1` |
| cold-final-5 | 387.548091208 | 386.547141625 | 0.987170292 | 0 | `9522180ef2a870161d02d3e76fe4c2aa76819463` |
| warm-final-1 | 91.294149542 | 90.359307041 | 0.922828583 | 0 | `ad30de63c12d3819abc0a59faecfb84a20487af8` |
| warm-final-2 | 92.089849375 | 91.252733917 | 0.824825375 | 0 | `7466fd66991a36e9803b91687b56438fdd00baad` |
| warm-final-3 | 92.864589875 | 92.022648583 | 0.830336291 | 0 | `abfeed3492315373f1accce5299ba2843545abb7` |
| none-final-1 | 87.665292500 | 86.850088792 | 0.803939958 | 0 | `8c9a136c0ee40a88acf8a398b6b1214e10ea6bac` |
| none-final-2 | 88.395786167 | 87.556591041 | 0.826748500 | 0 | `c0ff05360378316a13f9acea3a34f6f07eb9c99a` |
| none-final-3 | 87.889101542 | 87.054197375 | 0.823338333 | 0 | `4afdcee3b114be6b38fda5eedaec7f43ad6bcdb0` |

`cold-1` is the superseded implementation trial. Final-code `cold-final-1` failed because the original preparation moved ledger-referenced immutable provenance; the product correctly refused it. `cold-final-3` refused the dirty prior-event ledger before verification. Corrected preparation retains immutable 32-hex run receipts/logs/tasks at their original paths and isolates all 64-hex digest-keyed reuse receipts plus the content cache. Successful cold logs confirm actual execution, not reuse; retaining historical audit records cannot satisfy the native execution cache lookup. All failed trials are retained above and are not successful timing samples.

| Scenario | Comparable baseline | Successful final totals | Maximum | Budget | Headroom at maximum |
|---|---:|---|---:|---:|---:|
| Cold | 565.161 | 376.120239583, 381.742209625, 387.548091208 | 387.548091208 | 400 | 12.451908792 |
| Warm whole-proof | 241.295 | 91.294149542, 92.089849375, 92.864589875 | 92.864589875 | 200 | 107.135410125 |
| No schema | 245.391 | 87.665292500, 88.395786167, 87.889101542 | 88.395786167 | 95 | 6.604213833 |

All three scenarios meet their current limits in all three successful comparable runs. No-schema missed the original 45-second target in every run; after viewing these results the owner explicitly replaced it with 95 seconds on 2026-10-13. Best demonstrated total is 87.665292500 s; headroom at the maximum is 6.604213833 s. The original pure-check warm baseline was 354.898 s; use the matched whole-proof baseline above when assessing orchestration. Production adds native admission and stronger runtime identity compared with the isolated experiment, so its final experimental numbers are not silently relabelled as production results.

### Cache conditions, selected checks and preparation

All successful final runs: 10,636 ordinary tests collected, 10,579 passed, 37 skipped, 20 xfailed; coverage 92.96786389413988% (6,873/7,242 statements; 2,963/3,338 branches), floor 91.47% unchanged. Repository integrity, pre-commit hooks other than the duplicate affected-test hook, interfaces, stage, documentation, lane, readiness/capacity and native evidence checks remained in the measured command. Ordinary worker durations are retained in each VERIFICATION_SUITE log record.

Cold: dependencies installed, no digest-keyed whole/content cache available; dependency guard, 12 schema assertions and both public generation passes executed. Warm: identical base, source, environment and physical inputs; all three selected tiers reused validated native receipts. No-schema: base is the reviewed product commit and the actual changes are only events.jsonl records; neither real schema tier nor dependency guard is applicable, while the complete ordinary suite and surrounding checks run. Independent consumer-body and producer/invalidation controls supplement this real bookkeeping workload.

Cold cache-reset costs (separate, not recurring verification):
- `cold-1`: 0.000076166 s.
- `cold-final-1`: 0.000303291 s.
- `cold-final-2`: 0.016288416 s.
- `cold-final-3`: 0.057955542 s.
- `cold-final-4`: 0.068263459 s.
- `cold-final-5`: 0.155304041 s.

Dependencies, XSD copies and runtime metadata were prepared before timings; combined initial preparation remains UNMEASURED as stated above. No OS/filesystem cache flush was performed. Each cold reset preserved old evidence in an isolated sibling location; existing main/experiment evidence was not removed. No simultaneous reviewer test run overlapped measurements. Repetitions establish feasibility on this machine, not a guarantee for other machines or future runs.

### Reproduction

Production branch: `codex/verification-production`; measured worktree: `/Users/manon-dev/.codex/worktrees/verification-production/junoscfg`. The final archive commit is a version/documentation-only successor of the measured code. Original experiment remains on `codex/verification-timing-experiment`. Raw JSON/logs, worker reports and exact external harness scripts are preserved in `private_test_data/verification-production/` and `private_test_data/verification-runs/` (ignored, copied to the main checkout before worktree cleanup).

```sh
# In a prepared worktree, commit prior native audit events using normal hooks.
# Include that commit cost if reporting a repeated complete-workflow total.
PYTHONDONTWRITEBYTECODE=1 uv run --locked --group dev --with griffe \
  --with tach --with towncrier --with vulture agent-ready check --set full \
  --base 507a3dc74248ce2d670f6a5e27023d34990e6965 --verbose
# No-schema workload: use --base 44324d36bb489b13212e3f02be251429af41f95d
# only while the actual later diff consists of the recorded audit-only commits.
```

For exact local repetition before later product changes, run `python3 private_test_data/verification-production/production-cold-prep.py <unique-label>` before each cold run, then `python3 private_test_data/verification-production/production-measure.py <unique-label> <base-sha>`. Warm and no-schema omit cold preparation. Each result records the exact command, head, base, total, checkpoint and audit time. The scripts refuse to overwrite preserved cold evidence. Re-establish a justified diff and regenerate valid context for new production changes; do not reuse the historical no-schema base indiscriminately.

### Bottlenecks, assurance and adoption

The ordinary suite takes roughly 65–74 seconds even without expensive qualification; native orchestration and integrity checks add further cost. The 45-second budget therefore was not demonstrated without removing necessary verification. Ten workers increase simultaneous memory/process demand; peak memory and long-term flake rates remain UNMEASURED. Cold headroom is modest and normal machine load can exceed it. Future optimization should profile the remaining ordinary fixture/setup costs and repeated native identity work under the regular workflow, preserving byte-sensitive invalidation and complete coverage.

Adopt the reviewed native engine pin and application scheduling/selection through this regular change. Preserve the coverage floor, executed-test reports, serial schema stability passes, fail-closed unknown classification, and audited producer/consumer relationship manifest. The latter requires explicit review and refresh after relevant producer/dependency/configuration changes; successful qualification alone does not approve a new relationship. The source audit and negative controls support exempting the declared isolated consumer bodies, not all consumer code universally. No schema artifacts, public product semantics or prior assertions were weakened. Fresh review and independent challenge evidence are adjacent.


## Owner target adjustment

After final review and measurements, the owner explicitly approved 95 seconds
instead of45 for the no-schema scenario. This changes the accepted target only;
all timings, failures, code, assertions and coverage remain unchanged. Cold400
and warm200 remain unchanged. All three current targets were demonstrated in
three successful runs each; the narrow no-schema margin is not a guarantee.
