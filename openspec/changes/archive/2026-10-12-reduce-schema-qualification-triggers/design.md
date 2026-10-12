## Context
Filename selection cannot distinguish version bookkeeping inside uv.lock. Use a checked deterministic dependency projection as the relevant path; never claim the projection is test evidence.

## Reuse ladder

| Candidate | Coverage | Gap | Maintenance signal, lookup date | Verdict |
|---|---|---|---|---|
| Existing native tiers and verification wrapper | Selection, actual command evidence, locking, exact obligations | Semantic projection is application-owned | Installed checks-v0.16.1, 2026-10-12 | Reuse |
| Standard library TOML, JSON and SHA256 | Parse and canonical digest entire lock data | Root normalization and validation are local policy | Existing tooling uses tomllib, 2026-10-12 | Reuse |

## Decisions
New tools/schema_dependencies.py exposes fingerprint(root), write_dependencies(root), check_dependencies(root), run_guard(root). The manifest tools/schema-verification/dependencies.json contains format version and canonical normalized-lock digest. Required obligation schema-dependency-consistency lives in dependencies.required.json; result .agent-ready/schema/dependencies-result.json is ignored. CLI write refreshes projection deliberately; check executes truthful guard. All parsed data is retained except one validated root version. Guard runs first on uv.lock, its helper/contract and manifest paths; existing schema tiers replace only uv.lock with dependencies.json. Adapter _preflight and explicit qualifier check consistency before work. Existing tiny repositories gain a valid synthetic lock and fingerprint.

## Risks
Native evidence remains whole-tree conservative; this change reduces selection, not cache invalidations once selected. Development dependency updates still qualify intentionally. A guard failure may be followed by other selected tiers because that is current template scheduling; each adapter repeats cheap consistency before costly work and therefore also refuses. Tools use the repository's existing tomllib developer environment, without changing the Python runtime package floor.
