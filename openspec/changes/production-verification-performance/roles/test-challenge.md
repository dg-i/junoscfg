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
