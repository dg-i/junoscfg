# Done

**Final bounded review verdict: approved. P1 and P2 are closed; no review findings or binding review obligations remain.** This verdict covers implementation and verification evidence, not the later merge/archive/version/tag housekeeping.

The original review below is retained unchanged as historical evidence. Its initial blocked status is superseded by this bounded follow-up.

The shared lane correction was independently reviewed and released as checks `checks-v0.17.4` at peeled commit `8f21be09833035dd4a1c63c09d19165d420cbcbc` and template `v0.13.4` at peeled commit `3327b4747b2e83ce2c288141e37e0068e25f55e4`. Exact application adoption: `6bdaf5bc15ad22d11b19d8a25effa11bc82a6f88`. Final tested application head: `4290d373de23229f145b5b23fe027b6dd4506c7f`, against the original baseline `b20aa2b116fac222a2cf46306632b2dcb4ea442b`.

# Evidence

**P1 closure:** `private_test_data/schema-scope-final-full.log` shows the lane check passing against the original combined baseline and crediting 55 updater-only paths. The correction preserves exact `refresh_receipt.matches` admission and applies historical proof only within ordinary lane processing. Attested single-parent checkpoints, complete recorded path transitions, immutable canonical mirror/ignore evidence, and composed byte/mode equality constrain every credited path. Manual application transitions remain governed. Inspection of the staged and committed adoption found the expected release metadata, updater receipt, changelog fragment and ownership documentation; no application implementation correction was introduced.

The same full run passed OpenSpec and every other check except generated skill mirrors. It executed 10,612 ordinary tests with 37 skips and 20 strict xfails, and both schema tiers succeeded. Native receipts are `ad96b3d19d81881218e1dcbb0f083987df0cd43f1390d97a651c910daaa144a2`, `15f07385b6f2fe09ed9e7f0a6ddf716ba29c6c246a57c299cbb8f8335d712a1c`, and `6f44be03ee764984293fe8345c8beea5b9a8955380e068f214f2dbb4b4eb9f34`.

**Final gate closure:** the aggregate full command exited **1**, with the sole diagnostic `failing: skills`: four `.claude/skills/agent-ready-*` mirror directories were missing. The supported `agent-ready skills --regenerate` restored only ignored derived mirrors, and the isolated `agent-ready skills` rerun exited **0**; evidence is `private_test_data/schema-scope-skills-closeout.log`. Read-only Git inspection confirmed HEAD remained `4290d37`, with only native `events.jsonl` records modified. Tracked sources, tests, specs and canonical skills were unchanged. The regenerated Markdown mirrors do not invalidate the already-passed application/schema execution components. The full command is **not** relabelled successful; final assurance consists of its retained green components plus the successful repair of its sole failed integrity gate.

This is an evidence-based failed-gate closeout, not a waiver or a comparison-base substitution. The user's explicit instruction to avoid repeating green checks when their inputs remain valid governs the bounded rerun. No further test/schema/full repetition is warranted for the mirror repair. P2's OpenSpec scenario correction remains closed and also passes in the original-baseline run.

Upstream evidence inspected: `/private/tmp/updater-checkpoint-review.md`, `/private/tmp/updater-checkpoint-release-evidence.md`, and `/private/tmp/updater-checkpoint-integration-probe.json`. The upstream reviewer reports no actionable findings, focused tests and independent adversarial probes; the release evidence records its full package and rendered-template validation. I read the immutable fix and tests and confirmed release runtime files match reviewed feature `9755e995003889f34ba06124ab39760f59d28f1f`. No broader upstream re-review or repeated green tests were performed.

# Changed paths

Only `/private/tmp/junoscfg-schema-scope-review.md` was updated by this reviewer. The original findings/history remain below. The orchestrator owns recording closures in the live change and later integration housekeeping.

# Commands and exit status

- Read-only immutable upstream diff/tag checks — exit 0. Peeled tag references match the handoff; reviewed `lane.py`, `refresh_history.py`, and unchanged `refresh_receipt.py` have no release delta.
- Read-only application staged/committed diff, status and retained log inspection — exit 0. No reviewer tests or gates were run concurrently with hooks or qualification.
- Parent's original-baseline canonical full at `4290d37` — **exit 1**, solely `skills`; lane, ordinary suite, and both schema tiers passed.
- Parent's supported mirror regeneration and isolated failed `agent-ready skills` rerun — **exit 0**, retained in the closeout log.
- Earlier independent 148-test review result and native selector proof remain valid; they were not repeated.

# Open questions for the owner

None.

# Deviations

The aggregate original-baseline full command remains recorded as failed, followed by successful targeted closure of its sole integrity defect. The explicit owner instruction forbids unnecessary repetition of green checks; restoring ignored derived Markdown mirrors changed no tracked or schema execution input. This overrides any expectation to obtain another all-green aggregate invocation merely for presentation. The report remains at the requested temporary path.

---

# Initial review — retained history

# Done

Fresh isolated Phase 6 review of `schema-qualification-scope` completed. **Implementation verdict: approved, with no new implementation findings. Change completion is withheld until the combined application/updater baseline passes the required gates.**

Reviewed immutable application diff `b20aa2b116fac222a2cf46306632b2dcb4ea442b..f401245cec541c02de7ab91ec0d20ffb810f3215` in `/Users/manon-dev/src/junoscfg-wt/schema-qualification-scope`. Reviewed the subsequent record-only correction through `9155303a9431652b5dd5e99f7411c96782b4c43c` separately. No Builder report or private reasoning was supplied.

## Ranked findings and binding obligations

1. **P1 / completion obligation, already known: combined-baseline lane gate remains red.** The canonical full run against the supplied application base finishes with `failing: OpenSpec live, lane`; the lane diagnostic rejects template-owned skill changes included through exact updater commit `1aef9ef5ea749a3f6e4848f2d1b8b4941e053171`. Requirement: ordinary integrity gates remain unchanged and green. Recommendation: resolve the shared updater-history recognition defect through its reviewed upstream release/adoption, then run the canonical full checkpoint against the original combined baseline. A record-only baseline passing lane does not prove that condition. Keep this obligation on this change, not in an optional backlog. Later runtime/adoption corrections require bounded review of their consequences and appropriately invalidated evidence.
2. **P2 / corrected record defect: omitted inherited OpenSpec scenarios.** At the reviewed implementation head, the MODIFIED requirements omitted four existing scenario headings, and OpenSpec refused the replacement blocks. The record-only correction at `9155303` restores those headings, and `schema-scope-no-schema-full.log` now reports every check passed. This closes the record defect; it does not close item 1.

No independent backlog findings or pending specification challenges were identified. No duplicate evidence provider or override was introduced: the application computes relevance and the native engine remains the authority for successful execution and reuse.

# Evidence

Read the frozen outcome, delta specs, contracts, independent Test/Challenge evidence, acceptance tests, and complete application/adoption diff. The observed implementation covers validator bodies and transitive local helpers, narrows lock records to the execution dependency closure, excludes unrelated tool/configuration changes, and retains conservative qualification on invalid or incompatible proof.

Independent executed checks:

- Focused scope, selector, and dependency challenge suite: **148 passed**.
- Actual selector against the current committed head: `{"selected": false}` using retained native generation evidence. No receipt was copied, rewritten, or synthesized by this reviewer.
- Actual source audit boundary verifies successfully.
- In-memory mutations of the real lock: changing Ruff's locked version preserves the projection; changing jsonschema's locked version changes it; checks distribution version bookkeeping alone preserves it.
- Upstream `checks-v0.17.0..checks-v0.17.1` changes `update.py` as its only checks runtime source. The installed declared runtime closure excludes `update.py`, includes the verification implementation, and binds its external PyYAML dependency. This independently corroborates the updater regression's provenance.

Retained execution evidence inspected, without repeating costly qualification:

- `private_test_data/schema-scope-full.log`: 10,612 ordinary tests passed, 37 skipped, 20 xfailed; full command failed the two gates above.
- Native successful receipt `367c1ee0795ba181d3b565eb3d785cced03641eb49828207bc7ae326d1fd4b1a`: dependency guard, exit 0.
- Native successful receipt `2a150f86706c0b6dc2b93a179835ed88da0487b557643e1726ee362e303d23db`: schema assertions, exit 0.
- Native successful receipt `57a30b676d4e87cf790b15251f296a79278728b98523953f960d5d4c605b3b2d`: schema generation, exit 0.
- Suite coverage JSON reports **92.96786389413988%**. The diff does not change the coverage floor, ordinary test adapter, or product assertions.
- `private_test_data/schema-scope-no-schema-full.log`, at record-only head `9155303` against qualification head `f401245`: every check passed, no expensive tier selected, and the same ordinary pass/skip/xfail counts. This is valid evidence of record-only nonselection, with its narrower comparison base preserved.

## Required review prompts

1. **Trust-boundary input:** local receipt JSON, output hashes, declared paths, runtime/import contents, and historical Git input bytes cross the evidence-admission boundary. The existing native receipt validation, physical-input rules, current runtime comparison, exact declaration equality, and hash-proven history remain in force. Focused tests exercised corrupt/stale/missing proof, changed runtime/producer/input, and source-boundary failures. No new path to a false negative selection was found.
2. **Incompatible-but-valid input:** two successive unrelated commits, a release-only lock/project change, and an updater-only checks release are valid inputs that the prior whole-environment assumption mishandled. The focused native-receipt cases, real no-schema checkpoint, real-lock probes, and inspected installed module closure support the revised behavior. Relevant validation-body and transitive helper changes still qualify.
3. **Shared blind spot:** classification-only tests cannot establish that runtime identity remains stable; the new tiny-receipt fixtures still stub the runtime probe. Independent counterchecks therefore used the installed module closure and real selector against genuine successful evidence. These support the intended boundary. The full-baseline lane failure remains explicit instead of treating successful schema/test substeps as complete acceptance.
4. **Second answer:** application `fingerprint_text`, source/configuration projection, and prepared observations classify the inputs they own; native verification supplies execution proof and runtime module identity. The same lock projection is used for current and historical text, and both real-schema tiers share the selector. No alternate success store or skip switch was added. Runtime module scope is supplied through the existing native declaration API.
5. **Stated figures and non-goals:** reproduced the pass count from retained native suite output and coverage from its JSON; verified actual nonselection and the stated updater source-diff claim. No new performance guarantee is inferred from a single checkpoint. The frozen non-goals hold in the reviewed diff: no Junos acceptance or generated product changes, no ordinary test/assertion/coverage reduction, and no blanket override. Existing historical timing records were treated as observations, not new claims to reproduce by rerunning schema work.

Applicable decision context: `2026-10-11-retire-jvd-from-per-change-verification` remains unchanged; this tooling-only review did not revive JVD or change product syntax. Verification cadence was checked at local master `b20aa2b116fac222a2cf46306632b2dcb4ea442b`: 65 first-parent commits since retained anchor `95585fbf1cd59fe4b9cb15be870f6a5020be49a3`. The existing pending invitation remains pending; no owner feedback was inferred.

Context expansions for the orchestrator to retain in existing metrics if needed: installed `agent_ready_checks/verification_runtime.py`, `verification_content.py`, and `verification_dependencies.py` to check the actual adopted runtime boundary; upstream `agent-ready-python` tag diff to verify the updater-only release claim; `docs/decisions/2026-10-11-retire-jvd-from-per-change-verification.md` for the governing unchanged corpus decision.

# Changed paths

Only `/private/tmp/junoscfg-schema-scope-review.md` was written by this reviewer. No application code, specifications, tests, lifecycle checkbox, metrics, evidence, or Git state was edited. The orchestrator owns copying this report into the change and recording lifecycle disposition.

# Commands and exit status

- `.venv/bin/python -B -m pytest -q -o addopts='' -p no:cacheprovider tests/tooling/test_schema_scope.py tests/tooling/test_schema_selection.py tests/tooling/test_schema_dependency_trigger_challenge.py` — exit 0; 148 passed.
- `.venv/bin/python -B -m tools.schema_selection --base HEAD` — exit 0; `{"selected": false}` at the record-only correction head.
- Read-only Python probes of actual lock projections, `verified_source_boundary`, installed `verification_dependencies.closure`, receipt metadata, and coverage JSON — exit 0.
- `git diff checks-v0.17.0 checks-v0.17.1 --name-only` in upstream repository — exit 0.
- Git diff/status/history reads — exit 0. The implementation snapshot remains pinned; subsequent observed edits were change records only.
- A lookup for guessed upstream module filenames `verification_modules.py` / `verification_scope.py` returned exit 2 (not present); resolved the installed package paths and inspected `verification_dependencies.py` instead. A graph availability test returned exit 1: this isolated worktree has no graph JSON. No graph was generated.
- Retained canonical full run against original base — nonzero, `OpenSpec live, lane`; successful test/schema substeps do not change that result.
- Retained canonical full run against `f401245` after record correction — exit 0, every check passed; its narrower base is not a substitute for the remaining combined-baseline obligation.

# Open questions for the owner

None. The requested behavior and ownership split are sufficiently specified. The remaining gate defect needs implementation/evidence, not another owner policy decision.

# Deviations

Report destination is the orchestrator-requested temporary path rather than editing live change records. Full/schema work was deliberately not rerun in this isolated review; native retained evidence and focused execution provide the review evidence. The upstream runtime was inspected as a relevant dependency rather than re-reviewing its entire separately reviewed change. Graph lookup was unavailable, so actual contracts, source, and frozen codemap supplied architectural context.
