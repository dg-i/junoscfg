# Junoscfg verification

Application-owned qualification and execution policy. The shared
[admission and evidence protocol](verification-evidence.md) remains authoritative
for native readiness, receipts and runtime identity;
[parallel verification](parallel-verification.md) defines the adapter contract.

## Schema qualification

For junoscfg, a cheap dependency guard runs on lock/projection changes and
reports only its consistency obligation. The checked projection excludes only
the editable root package version; changing any other parsed lock data requires
refreshing it and selects real qualification. Missing/stale projections refuse
even under expensive-only checks and direct adapters. Routine real-schema tiers
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
command. Producer paths, relevant dependencies, schema inputs and unknown changes
select qualification. Recognized consumer function-body changes may avoid it only
when import-time structure is unchanged and validated native generation proof
binds the current schema inputs, dependencies, artifacts and actual execution
runtime. Decorators, class construction and import-time calls conservatively
select qualification. Ordinary compatibility and consumer tests still run.

Missing, corrupt or incompatible proof, uncertain history or malformed selection
output selects qualification. Preparation records installed versions but cannot
establish proof. Runtime identity binds the actual project interpreter, dependency
bytes, startup/import paths and relevant import environment; ignored import
shadows and executable bytecode are not exempt. Re-preparing after a runtime or
dependency change cannot turn old evidence into valid proof. Only the three root
release-version files may use hash-proven ancestor text for successive release
bumps; no consumer exemption is inferred from mismatched historical source.

A committed `tools/schema-verification/consumer-boundary.json` records the audited
source relationship. It binds all product and tooling Python sources, declared
schema fixture sources, configuration and relevant lock data; only already-audited
isolated consumer bodies and root release versions are normalized. Qualifying a
changed producer does not by itself prove that future consumer changes are safe.
A stale or missing audit therefore selects qualification even after a new success.
Refresh this boundary only after reviewing producer imports/callbacks and the
consumer compatibility checks; preparation and qualification never refresh it.
This deliberately trades occasional extra qualification for safe uncertainty.
