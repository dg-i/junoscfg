# Independent Test/Challenge

## STOP-T
PASS for criteria coherence and test scope; no specification correction or
existing-test contradiction identified. Runtime acceptance remains red pending
implementation. Required because evidence integrity is a trust boundary.

## Executed evidence
Independent `tests/tooling/test_schema_qualification_challenge.py` uses genuine
tiny pytest assertion sessions, a controlled public ArtifactBuilder seam in a
child process, and the installed template verification wrapper. Seven probes
are red before implementation (10.20 seconds, missing run_generation API).
Ruff passes. No real schema or full check was run.

The probes require two actual build calls on semantic drift and second-build
failure, one on source/input mutation, no builder invocation for missing or
partial assertion completion, and no result visible inside either build.
Successful qualification preserves the assertion IDs, reports distinct
generation IDs, reuses intact output without execution, and executes two fresh
builds after protected-output corruption. Negative probes assert reached build
counts so unrelated early refusal cannot produce a false green result.

## Scope assessment
The frozen criteria preserve exact assertion coverage and timestamp-only metadata
normalization, and leave stability/reuse ownership with the installed wrapper.
Builder timing acceptance observes real setup/call/teardown reports and public
build elapsed time; timings are separate from outcomes. Independent probes do
not claim real-schema performance measurements or isolated generator stage
costs. Existing semantic-metadata tests remain complementary evidence.

## Checkpoint
Next: implement and make acceptance probes green, then fresh review. Deliberate
red-test commit exempts only the affected-test hook; other applicable hooks and
fields/caps gates remain required. No product implementation is owned here.
