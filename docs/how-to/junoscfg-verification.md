# Junoscfg verification

Application-owned qualification and execution policy. The shared
[admission and evidence protocol](verification-evidence.md) remains authoritative
for native readiness, receipts and runtime identity;
[parallel verification](parallel-verification.md) defines the adapter contract.

## Schema qualification

For junoscfg, a cheap dependency guard runs on lock/projection changes and
reports only its consistency obligation. The checked projection binds locked
schema execution libraries and their transitive dependency records, sources,
artifact hashes and Python resolution constraints. Unrelated packages and root
release metadata do not change it. Shared checks code is bound by its native
execution-module closure, so updater-only releases do not invalidate proof.
Missing/stale relevant projections refuse even under expensive-only checks and
direct adapters. Routine real-schema tiers
qualify only the shipped schema. Assertion execution
has no stability manifest; the separate generation tier has one and runs public
generation twice. Its inputs include the assertion result and exported products,
so changed prerequisite bytes invalidate generation evidence. Generation outputs,
not assertion exports, are the integrity-authoritative retained artifacts.
The [schema qualification instructions](run-a-batch-of-changes.md#run-the-schema-tier-when-the-generators-change)
cover explicit older-release qualification and timing reports.

## Schema content proof

Schema qualification generates fresh JSON and grammar inputs on every run. The
existing Draft202012 schema validation and Lark compilation can reuse successful
proof only when exact input bytes, worker source, Python and dependency identities
match. The wrapper follows the shared
[exact-content proof contract](verification-evidence.md#exact-content-proof).
The shard's bound outcomes identify each check as `executed` or `reused`, including
its receipt and hash. Ordinary `pytest --schema` runs execute both checks.

This reuse leaves both independent serial artifact builds and all other assertions
in place. Byte comparison still covers compressed products; metadata excludes only
`generated_at`. Cold/changed inputs remain slower. Use the shared protocol
when invalidating enclosing whole-command and content proof for a cold measurement.

## Complete parallel verification

The native full checkpoint runs four independent read-only gates concurrently,
then respects mutation barriers. Its complete application adapter uses ten pytest
workers with isolated caches and coverage files. Product modules remain together
to retain fixture locality; tooling tests use measured scheduling hints. Its
reporting and fail-closed completion follow the shared parallel-verification
contract. Coverage merges executed data and applies the
existing branch-enabled floor. Scheduling costs never select or remove tests.
The full checkpoint suppresses only its duplicate `affected-tests`
hook when the complete suite is included; ordinary commit hooks remain active.

Application tests may overlap selected schema tiers. Native readiness, shared
capacity, serial tier dependencies and failure recording remain mandatory. The
configuration is opt-in; removing `gate-workers`, `full-suite`, `overlap-tiers`
and `affected-test-hook` restores serial native scheduling.

## Conservative schema classification

Both real-schema tiers use `tools.schema_selection` as their native selection
command. Producers, validation algorithms, relevant dependencies, physical schema
inputs and generation options select qualification. The reviewed boundary binds
product sources, qualification adapters and fixture helpers, following their
local imports transitively. An unreferenced `tools/` script does not participate
merely because it is tooling. New producer imports/callbacks require audit.

Documentation, instructions, workflow tooling, release bookkeeping and unrelated
dependency updates preserve proof when relevant inputs remain equal. Pyproject
comparison binds build/interpreter/entry-point settings, pytest configuration,
expensive-tier declarations and unknown tool tables; ordinary gate settings and
release metadata are independent. Validator function bodies always qualify.
Existing isolated consumer bodies require unchanged import structure and an
unchanged audited producer relationship; uncertain execution effects qualify.

A negative decision requires valid native generation proof with unchanged
explicit inputs, output hashes and executing runtime. Preparation alone is not
proof. Native `runtime-modules` binds the shared execution module closure and
external dependency bytes, startup/import paths, shadows and pytest plugins;
updater and documentation bytes are outside that closure. The lock projection
and prepared observation use the same execution responsibility, rather than all
installed packages. Ordinary whole-command identity and complete tests remain.

Missing, corrupt or incompatible evidence selects qualification with a specific
stderr reason. The JSON boolean protocol remains exact. Successive irrelevant
commits can reuse original proof; historical configuration and lock text must
match the original receipt hash. A changed relevant dependency, algorithm or
engine cannot obtain a skip by rewriting instructions or refreshing metadata.
The committed `consumer-boundary.json` is refreshed only after review of actual
execution relationships, never by preparation or successful qualification alone.

## Ordinary tests and commit cost

`tools/affected_tests.py` reads staged paths for ordinary commits; without staged
paths it uses the branch and working-tree diff. Source-package changes retain unit
importers and contract tests. Tooling modules follow audited reverse dependencies
through tools and all test modules. Root fixtures/shared support select the full
suite; nested fixtures select their directory. A changed or deleted test module also
selects the test modules importing its helpers or tests; any src/tests/tools Python
change selects the selector's own tests. Tools that read `tests/` or `tools/` are
selected too: a test edit adds about 4 s, a tool edit about 9 s (measured 2026-10-15). Root `conftest.py` and
alternate pytest configuration select the full suite; untracked files beside the
tested code refuse evidence reuse. Unknown loaders, malformed dependency
sources, deleted or unmapped tools and configuration retain conservative coverage.
Package data selects its package. A repository file a test or tool reads by an
anchored constant path selects that module's tests, so the CI workflow selects its
type-policy test and `examples/` (declared by shared support) the full suite; a
module passing the bare root or a computed path outside tooling reads every such
file. Other unclassified configuration also selects the tooling suite. Renames
list both paths. Package-wide source scanners are not yet selected for package
changes (backlog SELECT-SCAN-001); the full checkpoint covers them. The precise boundary is
`tools/affected_tests.CONTRACT.md`. OpenSpec metrics and review bookkeeping do not
add test targets to an otherwise identical selection.

Under Strategy A, the ordinary runner uses the template's existing command evidence
API. A later identical selected pytest command can reuse successful native proof
only with matching source bytes, base, physical root, environment, executable and
runtime identity. There is no application receipt cache and no import of raw logs.
Unavailable identity runs the selected tests; a failed execution remains failure.
Changing coverage flags or test selection changes the obligation. A focused or
serial no-coverage run cannot satisfy the full suite with aggregate coverage.

The canonical full checkpoint already excludes the affected-test hook through the
shared runner and executes `tools.verification_tests` once with coverage. Ordinary
commits still run all applicable hooks. Batch coherent edits before committing;
resolve fields, caps, lane, readiness and strict OpenSpec validation before the full
checkpoint, and keep its tested inputs fixed until completion. Review/metric records
alone do not justify another full run; changed executing inputs do. Version, lock,
shared fixtures and unknown configuration deliberately retain broad ordinary tests.
That remaining release cost is policy, not an exemption inferred from bookkeeping.
A template update moves the lock, so its commit runs the whole suite serially
without coverage and the following full checkpoint runs it again in parallel with
aggregate coverage: two distinct obligations, neither of which satisfies the other.

Ordinary evidence reuse is unavailable when private capture/schema directories,
pytest or Junoscfg environment overrides, alternate pytest configuration or unknown
configured options may introduce unbound inputs. The runner executes tests directly
in those contexts; their status and options are unchanged. This is distinct from
schema qualification's explicit private-input manifests and native evidence.
