# Review: reducing non-verification workflow overhead

## Finding

The measured maintenance workflow spent **13 minutes 1 second outside recorded verification**. The requested 50% ceiling is **6 minutes 31 seconds**. The reusable workflow changes have been released and adopted, but **no comparable before/after run has demonstrated a reduction yet**.

Finalization and preflight together account for **54% of the non-verification baseline**. They are the strongest starting points for improvement. This is a review of the measured workflow, not an approval to remove required checks or independent review.

## Measurement basis

The original maintenance run lasted 28 minutes 49 seconds. Subtracting the union of measured verification commands and commit hooks leaves 781.212291 seconds. Overlapping work is counted once. Human-input waiting was zero.

| Activity outside measured verification | Time | Share |
|---|---:|---:|
| Finalization, metrics, archive, version and integration preparation | 4m 06s | 31% |
| Preflight, instruction reading, discovery and preparation | 2m 59s | 23% |
| Review coordination and concurrent report preparation | 1m 43s | 13% |
| Editing and admission preparation | 1m 28s | 11% |
| Records between verification checkpoints | 1m 07s | 9% |
| Diagnosis and preparation repair | 1m 03s | 8% |
| Intent preparation | 36s | 5% |

These are phase-level residuals, not a precise allocation of agent reasoning, tool dispatch, writing or waiting. Uninstrumented checks remain an attribution limitation. The review window includes concurrent parent work; recorded reviewer inspection was only 22 seconds. The later template release and adoption was a different workload and is not a valid after-sample.

## Finalization: four improvement suggestions

**1. Resolve the closing sequence during preflight.** Record the required order once: complete evidence, commit governed records before checks, validate, archive, bump the paired version and lock, run applicable checks, integrate and tag. Use that checkpoint during closure instead of rediscovering the process. The original run had a version-bump repair; the later adoption also attempted a fast check before committing its evidence.

**2. Capture metrics and assemble the report once.** Reuse native verification events, command logs and the existing metrics command. Obtain full commit IDs directly from Git instead of transcribing them. Keep one authoritative evidence record and link to it. This addresses repeated report preparation and the observed incorrect-SHA metrics retry. Missing telemetry must remain explicitly unmeasured.

**3. Prepare independent closing facts while the reviewer works.** Identify the current integration version, required tag, archive destination and evidence paths during the review window. Do not mutate the reviewed snapshot or treat a pending verdict as approval. Recheck facts that can change before integration. This can shorten the critical path without weakening review independence.

**4. Use the project interpreter and fail-fast release commands.** Reuse existing version tooling, stop dependent commands after any failure, and confirm version agreement before committing. The original system-Python bump failed because `tomllib` was unavailable, and the surrounding sequence continued. Preventing that error also avoids correction and repeat-check work; verification savings must still be reported separately.

## Preflight: four improvement suggestions

**1. Read a bounded set of authoritative instructions once.** Start with the root instructions, the applicable lane and the owning contracts. Expand into other documents only for a concrete unresolved question. Retain paths and decisions in the existing preflight record; reread when relevant instructions change. The baseline included several speculative path and module probes.

**2. Resolve environment and execution facts in one preparation pass.** Establish the clean integration base, isolated worktree, installed interpreter, dependency source, canonical commands and evidence validity before implementation. Prefer installed dependencies and existing caches. This avoids repeated discovery and the baseline's initial interpreter realignment; successful environment preparation alone is never qualification proof.

**3. Select the lane and required roles before starting checks.** Record which phases apply, which are legitimately omitted, and when fresh review is required. For this maintenance lane, independent lightweight review precedes the canonical full checkpoint. The original first full attempt ran too early and failed on review and preparation requirements.

**4. Check admission inputs before launching the expensive checkpoint.** Prepare the required changelog fragment, planned paths, readiness inventory and schema inputs; inspect the production baseline and let the native selector decide qualification. This addresses the original missing fragment and schema inventory. It moves necessary preparation earlier rather than bypassing qualification or suppressing failures.

## Recommended order and acceptance

Start with a bounded preflight record and a reliable closing sequence: preflight suggestions 1–3 and finalization suggestions 1, 2 and 4. Several are already reflected in the released workflow guidance. Their actual time benefit still needs measurement.

Measure the next genuine, comparable maintenance change using the same interval-union accounting. Report total elapsed time, verification separately, non-verification residual, phase boundaries, retries and human waiting. Success is a residual at or below **390.6061455 seconds**, with all applicable obligations satisfied. Do not create artificial work to obtain an after-sample, and do not assign estimated savings to these suggestions.

## Evidence and reproducibility

The measured change is archived under
`openspec/changes/archive/2026-10-13-clarify-audit-unknown-values/`.
Its verification and metrics records retain the implementation and checks.
The later adoption is archived under
`openspec/changes/archive/2026-10-13-adopt-workflow-economy/`.
See the [verification baseline](../VERIFICATION.md#measured-maintenance-workflow)
and [measurement protocol](../how-to/capture-change-metrics.md).

The original UTC interval was 2026-10-13 12:34:19.152399 to
13:03:08.439494: 1729.287095 seconds. The union of recorded verification and
hook intervals was 948.074804 seconds. Their difference is 781.212291 seconds;
half is 390.6061455 seconds. Rounded table values are for readability.

Raw command logs, the interval-union calculation and phase residuals are retained
locally in `private_test_data/workflow-measurement-2026-10-13/` and
`private_test_data/workflow-overhead-2026-10-13/`. These ignored measurement
bundles are not shipped in a fresh clone. Complete agent-time attribution and a
comparable after-sample remain unavailable; the archived records do not establish
an independently reproduced speedup.
