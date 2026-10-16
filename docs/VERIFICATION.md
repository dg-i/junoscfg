# Testing and verification

Application-owned record; follow [the improvement policy](how-to/improve-verification.md).
Measurements, owner decisions and agent judgments are distinguished below.

## Cadence state

- Integration branch: master.
- Interval: 10 first-parent commits.
- Observed integration head: c3912da21bb46ae3857ebc65a105316cedf482fc (post-merge, pre-archive assessment).
- Cadence anchor SHA: 95585fbf1cd59fe4b9cb15be870f6a5020be49a3.
- Last reviewed SHA: NONE (initial adoption, not a completed cadence review).
- Last declined SHA: NONE.
- Pending assessment head: c3912da21bb46ae3857ebc65a105316cedf482fc.
- Invitation status: pending; 93 first-parent commits at the post-merge assessment. The retained anchor and invitation survive adoption.

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

## Measured maintenance workflow

2026-10-13 pre-integration assessment at master
`5226534324d03d1af6c00701fdbf683f118923e8`: 44 first-parent commits since the
retained anchor. The existing invitation remains pending; no owner review or
decline is inferred. Change `clarify-audit-unknown-values` measured the complete
maintenance route. Its first full attempt failed on review/changelog/inventory
setup; ordinary tests passed. Corrected cold full passed in 377.724 s;
no-schema full passed in 84.301 s after native proof justified
nonselection. Both retained 10,579 passed tests and 92.97% coverage. Independent
review approved the docstring-only edit. No assurance or corpus change was made.
Raw phase/command/hook evidence and final integration assessment are retained in
`private_test_data/workflow-measurement-2026-10-13/report.md`; the archived change
records failures and cache conditions. These are single observations, not a trend.

## Shared workflow adoption

2026-10-13 entry assessment at master `362301f834db3559f0f86f7ae0f6e378905dc3ad`: 52 first-parent commits since the retained cadence anchor; the existing invitation remains pending. Template v0.13.1 and checks 0.17.1 change workflow guidance and updater behavior. Verification engine source is unchanged from the production baseline, but the dependency identity changes and may invalidate qualification evidence. Preserve all three happy-flow targets and all assertions, coverage and corpus rules. Non-verification workflow reduction remains unproven; this refresh is not a comparable maintenance benchmark. Command evidence is retained in `private_test_data/workflow-refresh-2026-10-13/`.

Job-end adoption assessment: canonical full passed in 353.552s, including newly
selected schema qualification, with 10579 ordinary tests passing and 92.97%
coverage. The complete suite took 69.973s and overlapped qualification. Existing
project dependencies were retained; the canonical overlay installed 24 packages
(24 ms installation substep, download/resolution not separately timed). No
verification policy, assurance floor or corpus structure changed. Shared pages
match v0.13.1 exactly, and independent review approved the companion split.
The non-verification 50% improvement is not yet demonstrated by a comparable run.
One pending cadence invitation is retained; no owner review or decline is inferred.

## Execution-scoped schema selection

2026-10-14 change `schema-qualification-scope` retains the 400/200/95-second
happy-flow targets, ordinary suite and 91.47% coverage floor. Initial combined
checkpoint at `f401245` took 363.81s: all 10612 ordinary tests and both schema
tiers passed, but the overall checkpoint failed spec scenario preservation and
updater/application lane separation. This is not a passing cold-checkpoint sample.
After a records-only correction, valid native proof selected no schema work;
the complete checkpoint passed in 83.88s, ordinary suite 68.821s, coverage
92.967863894%. Both schema content checks had executed fresh in the initial run.
The independent reviewer also checked actual updater-only release source changes.
These are single-workload observations, not a trend. Final integration assessment
and shared lane correction are retained in the change's verification record. The existing
cadence invitation remains pending; no owner review or decline is inferred.

Final assessment for this change: the original-baseline checkpoint at `4290d37`
took 170.50s. Lane, 10612 ordinary tests, 92.967863894% coverage and both schema tiers
passed; the aggregate command exited 1 solely for missing ignored skill mirrors.
Supported regeneration plus the isolated skills check (0.14s, exit 0) closed that
integrity failure without changing tracked execution inputs. Independent review
approved reuse of the green components; the failed aggregate status is preserved.
The 83.88s successful no-schema demonstration was not repeated. No targets, tests,
coverage, hooks or review requirements changed. At pre-integration master `b20aa2b`,
65 first-parent commits have elapsed since the retained cadence anchor; the existing
invitation remains pending. Local integration and patch-release bookkeeping do not
constitute owner feedback or a new cadence review.

Job completion: local merge `1b3c79f` preserves the approved execution inputs;
archive and v0.28.14 change only release/bookkeeping data. The existing pending
cadence invitation is retained, with no new owner feedback inferred.

Job completion (affected-test scope): local merge `f639ae2` narrows ordinary
affected-test selection to dependency and reader consumers and adopts template
v0.14.4. The equivalent CLI-docstring commit fell from 173.37s to 8.67s; the final
full checkpoint at `e20ed29` passed in 175s (schema evidence reused; 360s cold at
`5adc8ae`), within the unchanged 400s cold / 200s warm targets. No tests, coverage,
hooks or review requirements were removed. The pending cadence invitation is
retained; no owner feedback is inferred.

Job completion (yaml-new format): local merge `5ec3682` adds the `yaml-new` format
without changing verification. The final full checkpoint at `a55c960` passed in 170s
(schema-25.2 tiers selected by `src/junoscfg/__init__.py`; 360s cold at `c95e67f`),
within the unchanged 400s cold / 200s warm targets; the fast set passed at `95b6820`.
No tests, coverage, hooks or review requirements were removed. The pending cadence
invitation is retained; no owner feedback is inferred.

Job completion (relative-null-flags): local merge `19e13c5` makes relative JSON output
spell presence flags as absolute output does, without changing verification. The full
checkpoint at `10a53b2` passed in 352s cold (schema-25.2 tiers selected by
`src/junoscfg/convert/output/__init__.py`), within the unchanged 400s cold target; the
fast set passed at `d9deb10`. No tests, coverage, hooks or review requirements were
removed. The pending cadence invitation is retained; no owner feedback is inferred.

Job completion (yaml-new-alias-cycles): local merge `0897096` lets yaml-new expand shared
blocks and refuse cycles and alias bombs, adding timer-guarded bomb rows (a POSIX timer in
`tests/support/aliases.py`) so an unbounded expansion fails instead of hanging. The full
checkpoint at `8fecbdd` passed in 349s cold and the follow-up at `b30dcd2` in 167s (schema-25.2
tiers selected by `src/junoscfg/convert/input/json_input.py`), within the unchanged 400s cold /
200s warm targets; the fast set passed at `084e1de`. No tests, coverage, hooks or review
requirements were removed. The pending cadence invitation is retained; no owner feedback is
inferred.

Job completion (yaml-depth-ceiling): local merges `3a121e8` and `c21e7b8` remove the yaml-new
alias size bound and replace the depth bound with a fixed 64-level ceiling; the
timer-guarded bomb rows of yaml-new-alias-cycles are retired with the bound (an alias bomb
is expanded by ruling) and `tests/support/aliases.py` no longer has the POSIX timer. The full
checkpoint at `a10ba71` passed in 351s cold and the follow-up at `5d4244b` in 170s
(schema-25.2 tiers selected by `src/junoscfg/convert/input/json_input.py`), within the
unchanged 400s cold / 200s warm targets; the fast set passed on the merged `c21e7b8`. No
tests, coverage, hooks or review requirements were removed beyond the retired bound's own
rows. The pending cadence invitation is retained; no owner feedback is inferred.

Job completion (relative-selections): local merge `5cbff05` writes a `--path --relative`
selection as absolute output writes it, without its path, in every format, and adds the
device-corpus law `TestRelativeSelections` (depth 4; 575 selections at depth 5 in the
change's evidence). The full checkpoint at `ab46c51` passed in 350s cold and the follow-up at
`f677934` in 166s (schema-25.2 tiers selected by `src/junoscfg/convert/__init__.py`), within
the unchanged 400s cold / 200s warm targets; after the correction review (tests and records
only) the focused tests and the fast set passed at `9d00c00`. No tests, coverage, hooks or
review requirements were removed. The pending cadence invitation is retained; no owner
feedback is inferred.

Job completion (input-trust-rule): local merge `1a79527` records the owner's rule that
configuration input is trusted in every format (`ARCHITECTURE.md` section 8, decision
2026-10-15-configuration-input-is-trusted); documents and contracts only. The full
checkpoint at `433bf4d` passed in 337s (schema-25.2 tiers selected by the two contract
edits), within the unchanged 400s cold / 200s warm targets. No tests, coverage, hooks or
review requirements changed. The pending cadence invitation is retained; no owner feedback
is inferred.

Job completion (qfx-null-probes): local merge `e6a8389` adds the `json-null-probes` device
probe source and the importer's JSON-source and awaiting-capture support; repository
tooling and test data only. The full checkpoint at `2d4d978` passed in 351s (schema-25.2
tiers selected by the new `.json.gz` under `tests/data/device`), within the unchanged 400s
cold / 200s warm targets. No tests, coverage, hooks or review requirements changed. Gap
observed, not repaired here: every worktree must commit the shared activation copy, so two
ready changes always both plan `.agent-ready/activation.json` and readiness refuses one;
the parallel session parked its changes for this run. The pending cadence invitation is
retained; no owner feedback is inferred.

Job completion (own-crash-fixes): local merge `2593859` fixes three defects in junoscfg's own
conversion code (a non-string `yaml` key, JSON and XML past 64 levels, an absolute leaf
selection's tags). The full checkpoint at `85df3e9` passed in 347s (13,703 passed;
schema-25.2 tiers selected by `json_input.py`), within the unchanged 400s cold / 200s warm
targets; after the review's record fixes and four message-door rows (`0cc3649`) the affected
tests and `agent-ready check --set fast` passed (247s) and the full checkpoint was not
repeated, as no runtime file changed. Tests were added, none weakened; no coverage, hook or
review requirement changed. The activation-copy gap recorded for qfx-null-probes recurred:
the two changes were admitted one after the other. The pending cadence invitation is
retained; no owner feedback is inferred.

Measurement (device-validation, before review round 2): the default-tier device-capture
law (`tests/corpus/test_device_renderings.py::TestTheValidatorsTakeWhatTheDevicePrinted`,
about 4 s of calls) and the verb and curly checks in `tests/corpus/test_set_corpus.py`
(which already compiles the grammar) need no budget change. The full checkpoint passed in
318.7 s cold at `73b317b` (schema-25.2 tiers selected; ordinary suite 68.4 s, 14,062 passed)
and in 83.3 s warm at `a130c96` (both qualification proofs reused; suite 65.8 s), within
the 400 s cold and 200 s warm targets. The first cold run at `77b313a` took 348 s with a
98.4 s suite: `tools/verification-costs.json` priced `test_device_renderings.py` at 1.08 s
where it measured 26 s serial, and one shard carried 83 s; repriced, the slowest shard
carries 56.5 s. A no-schema run is not reachable for this change's diff (it changes schema
inputs); its ordinary work is the warm run's. No tests, coverage, hooks or review
requirements were removed.

Job completion (device-validation): local merge `cc7204d` makes the validators take what the
devices printed and adds the device-capture validation law to the default tier
(`TestTheValidatorsTakeWhatTheDevicePrinted`, `TestEveryCaptureValidatesAsSet`). The full
checkpoint at `73b317b` passed in 318.7 s cold and at `a130c96` in 83.3 s warm (schema-25.2
tiers selected by the schema inputs), within the unchanged 400 s cold / 200 s warm targets;
review round 2 changed records only. `tools/verification-costs.json` reprices
`test_device_renderings.py` (1.08 to 26.0 s). No tests, coverage, hooks or review
requirements were removed. The pending cadence invitation is retained; no owner feedback is
inferred.

Job completion (backlog-open-findings): local merge `c3912da` changes documents only
(`docs/BACKLOG.md` and a changelog fragment). The canonical full checkpoint at `284dafc`
passed in 165 s (schema-25.2 tiers selected in the fresh worktree, "audited execution
boundary missing or changed", and passed). No verification path changed; no tests,
coverage, hooks or review requirements were removed. The pending cadence invitation is
retained; no owner feedback is inferred.
