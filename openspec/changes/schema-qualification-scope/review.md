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
