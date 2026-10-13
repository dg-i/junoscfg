# Independent application review

## Done

**APPROVED. No unresolved actionable findings or specification challenges.**
Reviewed base `507a3dc74248ce2d670f6a5e27023d34990e6965` through product
candidate `44324d36bb489b13212e3f02be251429af41f95d` in a fresh session without
Builder private reasoning. Subsequent measured commits change only audit events.
Approval covers the application adapter, selection boundary, fixture repairs and
completed measurements. Native dependency approval remains the separate exact-pin
review in `roles/native-review.md` for `4e8f8faf44a77c1e59fcd351fd00dc02aa677a58`.

## Evidence

Read the freeze, delta, applicable contracts, independent Test/Challenge records,
complete application diff, fixture changes and native review/verification records.
Independently executed **156 focused tests**, all passing, and verified that the
production audited boundary matches all **90** source/configuration/lock entries.
Fixture changes preserve existing assertions and actual execution/output/stability
checks. The native_driver fixture observes the installed project; it does not
redirect synthetic candidate output into the real project's evidence store.

Directly inspected every final measurement JSON and command log under
`private_test_data/verification-production/`. Nine successful canonical full
checkpoints each collected **10,636** ordinary tests: **10,579 passed, 37 skipped,
20 xfailed**. Combined coverage was **92.96786389413988%**, preserving the
**91.47%** floor. Cold runs executed all three selected tiers; warm runs reused
all three valid whole-tier receipts. No-schema runs selected no expensive tiers.

| Scenario | Successful observed totals, seconds | Maximum | Budget | Result |
|---|---|---:|---:|---|
| Cold: final-2, final-4, final-5 | 376.120240, 381.742210, 387.548091 | 387.548091 | 400 | Met |
| Warm: final-1 through final-3 | 91.294150, 92.089849, 92.864590 | 92.864590 | 200 | Met |
| No schema: final-1 through final-3 | 87.665292, 88.395786, 87.889102 | 88.395786 | 45 | Not met |

These are observed local results, not a cross-machine or longitudinal guarantee.
Dependencies and OS caches were retained. Cold preparation isolated digest-keyed
whole-tier/content reuse caches while retaining immutable ledger provenance;
preparation is separately recorded. Later totals include the normal prior-event
commit and hooks; checkpoint-only and audit portions remain distinguishable.
The updated verification.md and docs/VERIFICATION.md tables agree with the raw
records, maxima, budgets and retained failures. Cold/warm compare against the starting base. No-schema measurements compare
against `44324d3` with audit-only differences; independent tests exercise actual
consumer-body exemptions. The known 45-second gap remains explicit, as the freeze
permits; no assurance was weakened to claim it achieved.

Both failed final-code attempts remain visible: cold-final-1 exited 1 after
367.418987542 seconds because external preparation moved receipts still referenced
by the ledger; cold-final-3 exited 1 after 0.861036667 seconds because prior native
events were uncommitted. These are benchmark sequencing faults. Restoring immutable
provenance and using normal audit commits corrected them without product changes,
receipt fabrication, admission waivers or removal of failed observations.

### Required review prompts

1. **Trust-boundary input.** Candidate, physical input and executing-runtime bytes
   affect reusable success. Native verification retains admission, capacity and
   immutable proof authority. Application selection requires validated successful
   context and the audited relationship boundary; preparation alone cannot qualify.
   Independent negatives cover missing/duplicate reports, worker/coverage failures,
   changed inputs/runtime, corrupt receipts and stale audits.
2. **Incompatible-but-valid input.** Unknown tests remain eligible without cost
   hints. Legitimate skips/xfails retain distinct outcomes. Successive root release
   versions recover only exact hash-proven ancestor bytes for the three permitted
   files; mismatched consumer history remains conservative. No unresolved valid
   counterexample was identified.
3. **Shared blind spot.** Executed producer-call and module __getattr__ challenges
   are now regressions. Qualification cannot refresh the reviewed relationship
   manifest; changed producer/dependency/configuration relationships cannot silently
   inherit consumer exemptions. Live manifest equality and actual terminal phase
   reports provide evidence beyond shared collection expectations.
4. **Second answer.** Application tools own selection and execution reporting;
   native agent-ready owns admission, receipts and reuse. Historical lock handling
   reuses schema_dependencies.fingerprint_text. The source audit is a relationship
   boundary, not a second success cache. No conflicting provider was found.
5. **Figures and non-goals.** Historical figures match preserved experiment JSONL;
   final figures above match production records and logs. Product syntax/API,
   schema artifacts, assertions and coverage floor are unchanged. The report makes
   neither a 45-second success claim nor an impossibility claim. Decision
   `2026-10-11-retire-jvd-from-per-change-verification` remains effective.

## Changed paths

Reviewer writes only this `review.md`. Product code, tests, specifications and
concurrently edited records are untouched. No commit, branch switch or merge.

## Commands and exit status

- `.venv/bin/python -B -m pytest -q -p no:cacheprovider tests/tooling/test_schema_selection.py tests/tooling/test_schema_dependency_trigger_challenge.py tests/tooling/test_verification_tests.py`: **0**, 156 passed; log `/private/tmp/production-review-focused.log`.
- Executed `source_boundary` equality and `verified_source_boundary` against the
  production checkout: **0**, 90 matching entries.
- Read-only diff, measurement/log and ledger inspection: **0**. An initial
  historical path lookup returned 128; the retained experiment evidence was then
  located through git ls-tree and inspected successfully.
- Canonical Builder full checkpoints above: nine **0**, two retained **1**;
  independent reviewer did not duplicate expensive measurements.

- `uv run --locked --group dev agent-ready fields` and `agent-ready caps`: **0**,
  existing informational warnings only. Initial sandboxed attempts exited 2 on
  uv-cache access; authorized retries passed. Review-file diff check: **0**.

## Open questions for the owner

None. The known no-schema budget gap is reported under the approved freeze.

## Deviations

Initial review and independent tests were coordinated around timed runs and the
preliminary report stayed outside the candidate. This final report supersedes its
pending verdict. No product corrections were required by this review.

## Owner follow-up after this review

The owner subsequently replaced the no-schema target of45 seconds with95 seconds
after reading the results. This recorded instruction changes no product code,
assurance criterion or measured value. All three no-schema runs meet the revised
target; maximum88.395786167 seconds leaves6.604213833 seconds. The review above
retains the original45-second assessment as historical evidence.
