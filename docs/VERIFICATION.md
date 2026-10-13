# Testing and verification

Application-owned record; follow [the improvement policy](how-to/improve-verification.md).
Measurements, owner decisions and agent judgments are distinguished below.

## Cadence state

- Integration branch: master.
- Interval: 10 first-parent commits.
- Observed integration head: 8b3093d00c8fab03de2bfcb7327d493df180e2f1.
- Cadence anchor SHA: 95585fbf1cd59fe4b9cb15be870f6a5020be49a3.
- Last reviewed SHA: NONE (initial adoption, not a completed cadence review).
- Last declined SHA: NONE.
- Pending assessment head: 8b3093d00c8fab03de2bfcb7327d493df180e2f1.
- Invitation status: pending; 11 first-parent commits since the initial anchor.

## Feedback stages

The owner increased the provisional budget from 275 to **900 seconds for the
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
