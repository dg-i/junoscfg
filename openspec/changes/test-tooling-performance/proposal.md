# Reduce repeated tooling fixture preparation

Prepare immutable synthetic repository inputs once and copy them into isolated test roots.
Preserved behaviour: every existing test, real child pytest run, candidate/input mutation check, fresh runtime observation and generation call remains.
Verification: matched Python 3.13 tooling runs with branch coverage; compare test identities/outcomes and durations; add isolation evidence for shared setup.
Changelog: misc entry for developer test efficiency; no consumer or CLI change.
Scope: tests/tooling harness only; no production runtime, verification admission, cache, dependencies or CI changes.
Success: measurable tooling reduction without removing assertions or sharing successful execution evidence.
Review: independent lightweight maintenance review; parent coordinates full check and merge.
