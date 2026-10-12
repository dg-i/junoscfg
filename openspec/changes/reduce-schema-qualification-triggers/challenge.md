# Independent Test/Challenge

## STOP-T
PASS: frozen criteria are coherent and close the expensive-only selection
bypass. No existing-test contradiction or specification correction identified.
Independent work is required by the verification-selection trust boundary.

## Executed evidence
`tests/tooling/test_schema_dependency_trigger_challenge.py`: 22 red tests in
0.22 seconds before implementation; all fail because the new module is absent.
Ruff passes. No full check or real schema execution was used.

Ten mutation cases preserve sensitivity to revision, Python constraints,
resolution markers, root dependencies and metadata, dependency version/source,
artifact hash/size/URL. Eight invalid-root cases cover absent, empty and
nonstring versions, absent/duplicate roots, unexpected/extended sources and
malformed TOML. Three guard probes require successful prior actual execution,
then verify missing/malformed/stale projections remove that success record.

The native installed selector runs against real tiny Git commits: a root-version
change must select exactly the guard; a dependency change must fail consistency,
and its refreshed projection must select the guard before both schema tiers.
These are selection observations, not claims of real-schema execution savings.

## Complementary boundaries
Builder acceptance tests cover stale fingerprints at all four direct doors:
assertion run, generation, sentinel and qualify. Existing template identity,
locking and caching are retained. No additional cache or template change is
needed. The fingerprint remains a checked projection, never schema evidence.

## Checkpoint
Proceed to implementation and green bounded acceptance tests, then fresh review.
The intentional red-test commit skips only affected-tests; required fields/caps
and other applicable commit hooks remain enabled.
