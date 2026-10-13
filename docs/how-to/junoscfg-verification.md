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
