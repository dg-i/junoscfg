# Independent Test/Challenge

## Scope and baseline

Phase 4 for production-verification-performance. Read AGENTS.md, tests/CONTRACT.md,
proposal, delta, evidence freeze, design and the phase-4 skill. The frozen promise
is complete ordinary execution, conservative schema selection and engine-bound
whole-tier proof. No implementation or existing assertions were changed.

## Acceptance evidence

Added tests/tooling/test_verification_tests.py and tests/tooling/test_schema_selection.py.
All delta `Tests:` identities exist. The 94 parametrized cases cover:

- Complete identical worker collections with exhaustive disjoint assignment;
  missing, duplicate, foreign and inconsistent collections or reports refuse.
- Setup, call, teardown, exit errors and strict XPASS refuse; legitimate ordinary
  skip and expected-failure outcomes remain distinguishable from passing.
- Unknown scheduling nodes remain eligible and module fixture locality is retained.
- Real isolated two-worker mini-suites detect collection/lifecycle failures and
  combined coverage below the configured floor; coverage combine and report
  subprocess failure controls assert the failing command was actually reached.
- Declared producer/physical input/runtime paths and unknown paths select;
  isolated consumer bodies, workflow-only tests and documents retain exemptions.
  Import-time calls, decorators, bases, changed imports and malformed/missing
  source cannot acquire the consumer-body exemption.
- Root-release-only changes retain the cheap-guard exception; changing a dependency
  version does not. A prepared runtime file and absent/malformed records cannot
  provide successful qualification evidence. Even consumer-only selection consults
  established successful context.

Executed before the production modules existed:

`uv run --locked --group dev pytest -q tests/tooling/test_verification_tests.py tests/tooling/test_schema_selection.py`

Exit 1: 94 failed. The failure cause was ModuleNotFoundError for the three new
production modules. Full local output: /private/tmp/production-verification-tests-red.log.
This is red-phase evidence, not a claim that implementation has passed. No suite
or full checkpoint was run. Ruff check and format on both new files exited 0 after
formatting corrections. Parent requested no commit because it batches phase edits.

## Challenge findings

1. Preparation cannot establish qualification. If selection compares only freshly
   prepared runtime/input metadata with current bytes, changing an input and
   re-preparing makes stale success appear current. The approved spec already
   prohibits this. Builder confirmed selection requires validated successful native
   generation context; tests exercise absent context even for documentation changes.
2. Outer receipt reuse can bypass inner content checks. Engine bytes must bind the
   whole tier, including unchanged-version dependency, standard-library and
   importable bytecode changes. Routed to the native independent challenger, who
   reports actual identity/execute controls for runtime mutation plus rewritten
   preparation at the same base and command. Application path-classification tests
   alone do not establish this property; native evidence remains required.
3. Collection equality cannot prove execution. Actual unique terminal lifecycle
   reports, worker exit status and coverage status remain separate obligations;
   negative controls test each boundary.

These findings enforce existing frozen criteria; no specification amendment or
new scope is proposed. No existing test contradicts the delta was identified.
Existing assertions were left intact. Parent must review these new tests and
complete native evidence and production green runs before approval.

## Verification assessment

Assurance: negative controls protect the scheduling/proof boundaries rather than
lowering assertions. Reliability: isolated synthetic repositories and real worker
mini-suites avoid operator data; mocked coverage failures assert they were reached.
Corpus: tests stay with tooling owners and use tests/support/paths.py. Feedback
cost: focused checks only; production timing remains the Builder's required work.
Cadence entry observed master 507a3dc74248ce2d670f6a5e27023d34990e6965 and 24
first-parent commits since anchor 95585fbf1cd59fe4b9cb15be870f6a5020be49a3.
The existing pending invitation is retained; parent owns shared job-end update.

## Handoff

Next work: Builder implements against this red baseline, runs focused tests and
preserves the independent native challenge obligations. No implementation was
performed, no branch switched, and no commit, push, merge or full checkpoint run.

## Follow-up: implemented native-context boundary

Added a synthetic repository fixture that invokes real native verification.execute,
including two stability passes, and validates the resulting receipt with real
verification.valid. Runtime identity and observable installed versions are stubbed
inputs; prepared metadata validation, Git history, input/output hashes and receipt
validation remain real. No native source was modified.

Thirteen context cases cover unchanged and consumer-only success, version-only
repreparation, changed/missing physical input, stale metadata, changed runtime or
dependency bytes followed by preparation, producer changes, consumer comparison-base
hash mismatch, changed products, failed records and corrupt records.

- Installed-engine run before dependency adoption: exit 1, 13 setup errors because
  the required verification_runtime module was absent. Output:
  /private/tmp/production-context-red.log.
- Pending-native-source probe with PYTHONPATH=/private/tmp/agent-ready-verification-production/checks/src
  and `.venv/bin/python -B -m pytest -q tests/tooling/test_schema_selection.py::test_native_generation_context_rejects_stale_proof`:
  exit 0, 13 passed. Output: /private/tmp/production-context-probe.log.

A separate executable counterexample found that successive root-version-only
releases lost the documented cheap-guard exemption: proof at 0.28.3 accepted
0.28.4 plus refreshed metadata; after committing that release and using it as the
next base, 0.28.5 plus refreshed metadata was refused. The blanket receipt/base
old-hash check discarded legitimate historical version-only content.
`test_successive_release_only_changes_keep_cheap_guard_exception` failed with
exit 1 against the pending native implementation; output:
/private/tmp/production-successive-version-red.log.

Builder accepted this as an implementation defect under existing criteria and
proposed resolving only the three version-exempt paths from base Git ancestry,
requiring an exact match to the receipt hash before semantic normalization.
Consumer-body exemptions remain tied to the current comparison base. Independent
regression verification follows the repair; no assertion was weakened.

An additional potential untracked import-shadowing gap was routed to the native
challenger: root Python sources are excluded from the runtime imports scan while
application manifests enumerate tracked files. This is a proposed probe, not an
executed finding in the application tests.

## Follow-up repair verification

Historical version recovery was implemented by the Builder. The consecutive-release
regression now covers all three exempt files: package __init__.py, pyproject.toml
and uv.lock. All three pass. The original package-version case was observed failing
before the repair. The two additional variants landed while the repair was being
written; a sensitivity run disabled only historical_version_text in memory and all
three failed, with no implementation file edits. Output:
/private/tmp/production-successive-version-repair-disabled.log (exit 1, 3 failed).
The earlier successive-version log was replaced by the three-case green run;
the original failure and exact False-versus-True assertion remain recorded in
this phase's tool output and orchestrator message.

The complete independent application acceptance set then passed against the
pending native source:

`PYTHONPATH=/private/tmp/agent-ready-verification-production/checks/src .venv/bin/python -B -m pytest -q tests/tooling/test_schema_selection.py tests/tooling/test_verification_tests.py`

Exit 0: 110 passed. Output: /private/tmp/production-challenge-green.log.
This verifies the application boundary using the pending native implementation;
the locked adopted dependency and full checkpoint remain Builder obligations.
No application or native implementation was edited by Test/Challenge. Existing
consumer-old-hash mismatch and changed runtime/input preparation refusals remain
passing. The consecutive-version finding is resolved without changing the spec.

## Commit-hook fixture integration

The first normal commit hook exposed two isolated-fixture assumptions:

- The dependency trigger fixture copied production tier declarations but provided
  neither the configured .venv selector interpreter nor successful qualification
  context. Native selection correctly chose all tiers on uncertainty, contradicting
  the fixture's old guard-only expectation. The exact existing test reproduced
  this failure (exit 1; /private/tmp/dependency-selection-fixture-red.log).
- New native-context fixtures inherited the outer commit hook's GIT_INDEX_FILE.
  Native tracked-file inspection then read the outer repository's index inside
  the tiny fixture. An exact fixture node reproduced missing activation.json
  (exit 1; /private/tmp/schema-selection-hook-environment-red.log).

Fixture-only repairs preserve assertions: dependency routing bridges the selector
subprocess to the real select function with explicit established-context state,
retains the guard-only/version and all-tier/dependency assertions, and additionally
requires all tiers when context is uncertain. Receipt validity remains exercised
by the separate real native-context fixture. Selection tests import the existing
autouse isolated_git_environment fixture instead of duplicating Git control lists.

Focused locked-environment verification with the inherited real worktree Git index:

`GIT_INDEX_FILE=/Users/manon-dev/src/junoscfg/.git/worktrees/junoscfg5/index uv run --locked --group dev pytest -q tests/tooling/test_schema_dependency_trigger_challenge.py tests/tooling/test_schema_selection.py`

Exit 0: 91 passed. Output: /private/tmp/schema-selection-hook-environment-green.log.
Ruff passed for both edited test files. No implementation, assertions, full suite,
commit, push or merge was changed or run by this follow-up.

## Audited consumer boundary regression and repair

Read-only probes reproduced the owner's producer/consumer hypothesis. A producer
was changed to depend on an eligible consumer, committed and successfully qualified
through real native execution and two stability passes. A later consumer-body-only
change altered generated schema additionalProperties from true to false, while
established_context returned true and select returned false. Both direct calls and
module __getattr__ callbacks supplied by real imports reproduced the defect.
Scripts and output remain under /private/tmp/consumer-producer-selection-probe.*
and /private/tmp/consumer-getattr-selection-probe.*. Current source inspection found
validate.__getattr__ protected by producer classification, local producer callbacks,
and no current generator-to-eligible-consumer call; the missing enforced independence
boundary still allowed future qualified producer edits to introduce one.

The Builder's repair adds a committed audited relationship manifest. Qualification
and metadata preparation cannot refresh it. Added 24 independent boundary cases
in test_schema_selection.py. Existing native-context fixtures now explicitly create
and commit a real boundary before execution; real execute, valid, two-pass output,
Git and file-hash checks remain intact. New cases cover:

- Exact source/configuration/lock inventory; new and deleted Python source changes.
- Eligible body and root version normalization, with unsafe import-time structures
  and producer bodies retaining complete source identity.
- Missing, corrupt, empty, wrong-format, extra-field, incomplete, unknown-source,
  changed-hash and symlinked boundary records.
- Successfully qualified new producer dependencies followed by output-changing
  body edits, including actual Python module __getattr__ import hooks.
- Newly qualified dependency, verification-wrapper and configuration changes
  retaining stale audit boundaries; neither qualification nor preparation refreshes
  the recorded manifest.

The first 19 cases were observed red before source_boundary existed. Five added
lock/wrapper/configuration cases arrived while implementation landed, so explicit
in-memory sensitivity controls were also run: removing the audit guard produced
five failures, and omitting lock identity produced two failures. No implementation
files were edited for those controls. Logs:
/private/tmp/consumer-boundary-guard-disabled.log and
/private/tmp/consumer-boundary-lock-omitted.log. The initial red log was subsequently
replaced by the first 22-case green run; its 19 missing-helper errors remain in the
phase tool output and handoff messages.

After the expanded source/tools/declared-fixture/configuration/lock boundary settled:

`GIT_INDEX_FILE=/Users/manon-dev/src/junoscfg/.git/worktrees/junoscfg5/index uv run --locked --group dev pytest -q tests/tooling/test_schema_selection.py tests/tooling/test_schema_dependency_trigger_challenge.py tests/tooling/test_verification_tests.py`

Exit 0: 156 passed. Output: /private/tmp/consumer-boundary-final-focused.log.
Ruff and diff-check passed. The defect is resolved under the existing generation
independence criterion; no assertion was weakened. No implementation or whole-suite
checkpoint was performed by Test/Challenge. Writes stop here for the Builder's
commit and final verification.
