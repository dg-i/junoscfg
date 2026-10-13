# Testing and verification

Application-owned record; follow [the improvement policy](how-to/improve-verification.md).
Measurements, owner decisions and agent judgments are distinguished below.

## Cadence state

- Integration branch: master.
- Interval: 10 first-parent commits.
- Observed integration head: 507a3dc74248ce2d670f6a5e27023d34990e6965 (pre-merge assessment).
- Cadence anchor SHA: 95585fbf1cd59fe4b9cb15be870f6a5020be49a3.
- Last reviewed SHA: NONE (initial adoption, not a completed cadence review).
- Last declined SHA: NONE.
- Pending assessment head: 507a3dc74248ce2d670f6a5e27023d34990e6965.
- Invitation status: pending; 24 first-parent commits at the pre-merge assessment. The retained anchor and invitation survive adoption.

## Feedback stages

Historical budget (superseded for the three workloads below): the owner increased the provisional budget from 275 to **900 seconds for the
whole full checkpoint** on 2026-10-13,
including surrounding checks. It is an investigation budget, never a timeout
or permission to skip required checks. No separate target or tolerance was agreed.
A single observation is not evidence of a timing regression; compare equivalent
workloads and record cache/environment differences before drawing conclusions.

| Stage | Commands / required risks | Observed baseline | Accepted budget | Target / tolerance | Evidence / conditions |
|---|---|---|---|---|---|
| Local fast | affected tests per tests/CONTRACT.md; agent-ready check --set fast | UNMEASURED for the complete stage | UNSET, owner has not selected one | UNSET | Commit hooks and focused tests; do not infer stage time from one test |
| Pull request | Canonical full checkpoint below; repository integrity, full suite, coverage and selected expensive tiers | 245.796 s total; pytest 213.46 s | 900 s total, owner decision 2026-10-13 | UNSET; repeat comparable observations before a regression verdict | One prior checkpoint at e65c09b44d2d334ccb0e64602d99fc7bfb80975b; Python 3.13.15; cache state not recorded |
| Scheduled / release | Full checkpoint and schema tiers selected under verification-evidence.md; explicit older schema qualification when required | UNMEASURED for the complete release workload | 900 s applies to the full checkpoint; broader release workload budget UNSET | UNSET | No comparable complete release-stage timing available |

Canonical full checkpoint:

```sh
uv run --locked --group dev --with griffe --with tach --with towncrier --with vulture agent-ready check --set full --base <base-sha>
```

Prior evidence: `openspec/changes/archive/2026-10-12-test-tooling-performance/verification.md`:
10440 passed, 13 skipped, 20 xfailed; coverage 92.97%. That record reports
one matched tooling improvement from 102.62 s to 83.10 s, preserving all original
test identities and adding isolation coverage. It does not prove a full-stage trend.
Current refresh evidence lives in its OpenSpec review and verification records.

## Workload distinction

The earlier 245.796-second checkpoint did not represent uncached real-schema
qualification. Archived `streamline-schema-qualification/review.md` records
1261.679596 seconds for schema assertions and two generation passes alone.
Archived `reduce-schema-qualification-triggers/metrics.md` records a complete
full checkpoint of 1695.965102 seconds including qualification. These are
historical observations, not a new refresh regression or an accepted higher budget.
The 900-second budget is therefore a known gap for uncached schema workloads.
Keep cache state and selected tiers visible when comparing future runs.

## Quality dimensions

| Dimension | Evidence / gaps | Target / success check |
|---|---|---|
| Behavioural assurance | Unit owners, contract laws and device corpus per tests/CONTRACT.md; coverage is a gap indicator. Strict xfails and device-evidence gaps remain recorded in tests and docs/BACKLOG.md. | Preserve existing assertions, coverage floor and required schema obligations; no new numerical target agreed |
| Reliability | Fresh test repositories and uncached integrity sentinels; no longitudinal flake/rerun rate available. Refresh caught a stale lock projection before merge. | Preserve isolated state and fail-closed evidence; measure recurring failures before selecting improvements |
| Corpus organisation | Unit, contract, corpus, tooling and support responsibilities are explicit in tests/CONTRACT.md; affected selection has completeness tests. | Preserve ownership, test doors, selection completeness and isolated fixtures; no restructuring selected |

## Selected improvements and accepted gaps

- REFRESH-01: initialize this record and its session pointers; owner approved,
  agent implements; success is a reviewed record plus full verification before merge.
- REFRESH-02: regenerate the lock projection with the existing generator; this
  repairs the updater's stale fingerprint without changing qualification policy.
- Local-fast and complete release timing, cache-conditioned repetitions, flake
  rates and target tolerances remain explicit gaps. The owner accepted starting
  with the 900-second full budget; no broader numerical targets are inferred.
- Keep independent improvement items and their status in docs/BACKLOG.md.
  No additional corpus or performance work is selected by this adoption.

## Review outcomes

2026-10-13: Initial refresh assessment at the integration head recorded above.
Owner chose 900 seconds to leave headroom and approved preserving current hooks.
Agent judgment: retain assurance and corpus structure; collect comparable full
checkpoint observations before choosing further optimizations. Prior tooling
improvement has one matched observation, not a measured long-term trend.

2026-10-13 job-end assessment: full checkpoint passed in 1661.945 seconds,
including uncached schema qualification; 10440 tests passed and coverage was
92.97%. Final fast checks passed. The 900-second budget gap is consistent with
historical cold runs; no new timing regression is established. Refresh caught
a stale dependency fingerprint. Flake trends remain unmeasured. One feedback
invitation is pending; the initial cadence anchor is retained.

## Schema performance implementation

Owner-approved target on 2026-10-13: at most 180 seconds for warm shipped-release
qualification, including native wrapper overhead; every further second saved is
useful. Cold or changed-content checks remain separately measured. The owner
accepted approximately 201 MiB additional serialization memory from research.
The change `schema-content-performance` records implementation measurements.
Quality: preserve checker semantics and exact artifact comparisons. Duplication:
reuse only successful identical pure checks. Cost: deque traversal and buffered
JSON address measured bottlenecks. Reliability: template evidence binds runtime,
dependency bytes and lineage, with independent failure/corruption tests.

2026-10-13 schema-performance job-end assessment at integration head
6d5d41937b82db0e7e5b46c505edb08e72bdefc4 (12 first-parent commits since the
retained anchor): final full checkpoint passed at application head
e8ff3cfcf7d92fc1aab6862305add4f36bb06e90 in 597.57 seconds, including native
qualification; 10,448 passed, 37 skipped, 20 xfailed. Three warm shipped-release
native qualifications took 112.638111417, 111.743011875 and 112.506422750 seconds
(mean 112.296), each within 180 seconds. Cold full observation was 794.74 seconds
with 318.009 seconds in schema portions; older-release native qualification
passed for 21.4 and 23.2. These workload-specific observations meet the applicable
budgets without establishing a long-term timing trend. Environment: Python
3.14.7, macOS arm64, jsonschema 4.26.0, Lark 1.3.1, template 43433b0.
Behavioural assurance retained checker semantics and exact artifact comparisons;
independent tests cover corrupt/changed proof, and review caught an optional
dependency regression that is now corrected. Corpus structure is unchanged;
longitudinal flake rates remain UNMEASURED. Reviewer capability equivalence remains
a recorded limitation. Evidence: the schema-content-performance change's
verification.md and events.jsonl. One consolidated feedback invitation remains
pending; no owner review or decline is inferred, and the cadence anchor is retained.

## Production verification adoption

The owner approved production adoption and a baseline update after the isolated
experiment, then restricted integration to local merges (the owner will push).
Current happy-flow end-to-end targets are **400 seconds cold**, **200 seconds warm** and
**95 seconds without schema qualification**, with dependencies already installed.
These supersede the provisional timing guidance for these three workloads. They
are desired happy-flow timings, not hard limits, timeouts or verification failure
thresholds. Slower runs prompt investigation, not automatic rejection. Broader
release workloads and behavioural assurance obligations are unchanged.
Cold means no reusable qualification evidence; warm means valid input- and
runtime-bound proof; the third scenario requires justified schema nonselection.

Historical experiment, based on master
`507a3dc74248ce2d670f6a5e27023d34990e6965`: cold baseline 565.161 s,
original pure-proof warm 354.898 s, matched whole-proof serial warm 241.295 s,
and no-schema baseline 245.391 s. Experimental final cold runs were 342.148,
344.763 and 346.223 s; warm 73.782, 74.182 and 72.950 s; no-schema 72.923,
72.505 and 72.946 s. These are experiment measurements, not a production
checkpoint baseline: production retains native admission and stronger runtime
identity. The experiment missed the original 45-second target; that historical result is retained.

Production baseline at product commit `44324d36bb489b13212e3f02be251429af41f95d`:

| Full-checkpoint workload | Three complete-workflow observations (s) | Maximum (s) | Happy-flow target (s) | Margin to target (s) |
|---|---|---:|---:|---:|
| Cold qualification | 376.120, 381.742, 387.548 | 387.548 | 400 | 12.452 |
| Warm qualification | 91.294, 92.090, 92.865 | 92.865 | 200 | 107.135 |
| No schema qualification | 87.665, 88.396, 87.889 | 88.396 | 95 | 6.604 |

All nine successful runs include the canonical full command; required prior native
audit-record commits and normal hooks are included where applicable. Dependencies
were installed. Cold resets isolate reusable whole/content evidence while retaining
immutable audit provenance. Warm logs confirm native reuse; no-schema uses actual
audit-only changes and selects no expensive tier. All ordinary tests still run:
10,579 passed, 37 skipped, 20 xfailed; coverage 92.9679%, floor 91.47% unchanged.

Environment: macOS arm64, Python 3.14.7, uv 0.12.18, 10 CPUs, 32 GiB; native engine
4e8f8fa. Three final repetitions per workload; preparation is separately recorded.
Two failed setup attempts (367.419 s missing historical audit sources; 0.861 s
dirty prior-event ledger) and superseded cold trial 378.653 s remain in the
production-verification-performance change's verification.md. These failures were
correctly refused, not counted as successful samples. No product test failures
occurred in the nine successful final runs.

Agent assessment: adopt the reviewed scheduling and conservative selection changes.
All three happy-flow targets were met consistently on this machine. After inspecting
the results, the owner explicitly replaced the no-schema target of 45 s with 95 s
on 2026-10-13; the original missed target remains historical evidence. The new
no-schema maximum has 6.604 s headroom, a modest margin. Ordinary verification alone takes about 65–74 s.
Further work should profile fixtures and native identity overhead through the regular
change process. Ten workers trade additional concurrency for time; peak memory and
long-term flake rates remain unmeasured. These observations are feasibility evidence,
not machine-independent guarantees. Assertions, corpus responsibilities, strict
xfails, schema stability passes and coverage floor are preserved. Source audit
maintenance is deliberate: producer/dependency changes require review before new
consumer exemptions can be trusted. The pending cadence invitation remains open;
no separate general review or satisfaction response is inferred.
