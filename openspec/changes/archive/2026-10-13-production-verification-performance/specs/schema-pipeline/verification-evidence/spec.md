## ADDED Requirements

### Requirement: Parallel full verification preserves complete execution
WHEN the full checkpoint uses parallel ordinary tests THEN the adapter SHALL execute the entire live default collection exactly once across isolated workers, require actual successful phase reports, propagate every worker or coverage failure, and enforce the unchanged combined coverage floor. Scheduling hints SHALL change placement only, never eligibility. The native checkpoint SHALL retain readiness, capacity and immutable success evidence.
Tests: `tests/tooling/test_verification_tests.py::test_complete_disjoint_execution`, `tests/tooling/test_verification_tests.py::test_incomplete_or_failed_execution_refuses`, `tests/tooling/test_verification_tests.py::test_scheduler_covers_unknown_tests`

#### Scenario: A worker omits or duplicates a test
- **WHEN** the worker union differs from the identical complete collections
- **THEN** full verification fails instead of publishing success

#### Scenario: Parallel coverage is below the configured floor
- **WHEN** all workers pass but combined coverage is below the existing threshold
- **THEN** the full command fails

### Requirement: Schema selection fails safely on uncertain relevance
WHEN automatic qualification is considered THEN the application SHALL select all declared producer paths and relevant physical inputs, dependencies, runtime or schema configuration changes, preserve justified workflow-only and isolated consumer-body exemptions, and select qualification or refuse when classification is missing, malformed or uncertain. Release-only editable-root version changes SHALL retain their cheap guard exception. Input preparation SHALL NOT constitute successful qualification evidence.
Tests: `tests/tooling/test_schema_selection.py::test_all_producers_and_unknown_paths_qualify`, `tests/tooling/test_schema_selection.py::test_consumer_body_and_workflow_exemptions`, `tests/tooling/test_schema_selection.py::test_import_time_uncertainty_qualifies`, `tests/tooling/test_schema_selection.py::test_runtime_or_input_change_cannot_skip`

#### Scenario: An isolated consumer function changes
- **WHEN** unchanged import-time structure proves the changed body does not participate in schema production
- **THEN** expensive qualification is omitted while complete ordinary compatibility and consumer checks run

#### Scenario: A runtime or producer input changes
- **WHEN** relevant inputs or execution identity differ or cannot be verified
- **THEN** previous success cannot silently authorize skipping required qualification

### Requirement: Whole-tier proof binds the executing engine
WHEN automatic qualification reuses native successful evidence THEN the whole-tier identity SHALL bind the actual declared schema interpreter, standard library, importable bytecode and dependency implementation in addition to existing inputs, commands, outputs and environment. Unknown or changed identity SHALL cause execution or refusal, never stale success. Mutating preparation alone SHALL NOT create qualification proof.
Tests: `tests/tooling/test_schema_selection.py::test_runtime_or_input_change_cannot_skip`

#### Scenario: Standard library changes without a package version change
- **WHEN** engine bytes differ from the receipt identity
- **THEN** the old whole-tier receipt is not reused
