## Resolved instructions
Owner-approved implementation; instruction-integrity C1–C3. No installed template edits. Review the harness before costly qualification.

## Requirements
The delta for schema-pipeline/verification-evidence retains exact coverage, immutable inputs, fail-closed execution and semantic metadata. It narrows routine release selection and separates assertion execution from public generation stability.

## Evidence
Existing tools/schema_verification.py, its contract, tests/tooling/test_schema_verification*.py and schema corpus are the baseline. Installed verification.execute repeats a command for stability and hashes those outputs on reuse; preserve that ownership. Public build and build_from_xsd plus direct grammar generation are distinct retained paths.

## Non-goals
No new cache, dependency, runtime generator changes or changed Junos acceptance. Defer parsing deduplication until measured evidence supports it.

## Acceptance criteria
All tests named in the delta; independent Test/Challenge covers real execution counts, early refusal, output and metadata drift, failed publication, candidate mutation, and cached-output corruption. Existing 12 assertion IDs per release remain unchanged. Cheap existing parity tests run before expensive qualification.

## Performance expectations
One assertion pass plus two public builds replaces two assertion passes plus sentinel. Capture timings during the next required 25.2 qualification. Historical 31.6-minute total is context only; no promised speed threshold.

## Outstanding decisions
None; split tiers preserve template integrity without upstream migration.

## Execution and checkpoint
- Assurance preference: economy
- Risk floor: high, verification integrity trust boundary
- Roles required: Builder; independent Test/Challenge; fresh Reviewer; Finalizer
- Resume point: phase 4 after committed phase 2/design and independent Test/Challenge dispatch

## Delta log
- Freeze established: this delta and proposal; two-build estimate superseded by three-build design preserving existing wrapper output validation.

- Dependency inspection: generator imports of shared compression/key helpers resolve to display/constants.py through display/__init__.py. Include those exact trigger paths; no acceptance obligation changes.

- Fresh review found two violations of retained boundaries (inherited qualifier Git context; dirty explicit generation manifests). Existing contract determines both repairs; acceptance criteria unchanged. Added regressions and focused reruns before expensive execution.
