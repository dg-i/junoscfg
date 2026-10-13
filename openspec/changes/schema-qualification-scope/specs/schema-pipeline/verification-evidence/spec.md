## MODIFIED Requirements

### Requirement: Dependency selection ignores only editable root version
WHEN dependency relevance is computed THEN the application SHALL fingerprint the complete locked records and transitive dependency edges used by schema execution, including relevant Python resolution constraints, sources and artifact hashes; unrelated packages and editable release versions SHALL NOT invalidate qualification. Missing or ambiguous required dependency records SHALL refuse. Updater-only agent-ready-checks releases SHALL be judged by actual executing module identity, not distribution version.
Tests: `tests/tooling/test_schema_scope.py::test_dependency_projection`, `tests/tooling/test_schema_scope.py::test_updater_release_projection`

#### Scenario: Unrelated updater dependency changes
- **WHEN** only updater or documentation code changes in agent-ready-checks
- **THEN** schema dependency identity remains equal while relevant executing engine changes invalidate proof

#### Scenario: Transitive schema dependency changes
- **WHEN** a locked dependency used by a schema producer or validator changes
- **THEN** the dependency fingerprint changes and qualification is required

#### Scenario: Release bookkeeping changes only the project version
- **WHEN** only the unique editable root package version changes
- **THEN** the dependency fingerprint remains identical and the lock edit selects only the cheap consistency tier

#### Scenario: Any other lock data changes
- **WHEN** a non-version lock field changes
- **THEN** fields in the schema execution closure or its resolution constraints change the fingerprint and require a refreshed projection, while unrelated package fields preserve it

### Requirement: Schema selection fails safely on uncertain relevance
WHEN automatic qualification is considered THEN the application SHALL select schema producers, their transitive execution dependencies, relevant inputs, generation options and validation algorithms; irrelevant documentation, instructions, workflow tooling, release bookkeeping and dependency updates SHALL reuse valid native evidence. Missing or invalid relevant evidence SHALL select qualification with a specific reason. Unknown schema-impacting changes SHALL qualify or refuse. Ordinary tests, integrity, coverage and independent review SHALL remain unchanged.
Tests: `tests/tooling/test_schema_scope.py::test_execution_path_selection`, `tests/tooling/test_schema_selection.py::test_native_generation_context_rejects_stale_proof`

#### Scenario: Workflow-only edits with valid evidence
- **WHEN** an unrelated tool, instruction or configuration changes
- **THEN** qualification is not selected and ordinary verification remains required

#### Scenario: Changed validation algorithm
- **WHEN** a validation function body changes
- **THEN** qualification is selected even if import-time structure is unchanged

#### Scenario: No valid evidence
- **WHEN** relevant proof is missing, corrupt, or incompatible
- **THEN** qualification is selected and the failed condition is explained

#### Scenario: An isolated consumer function changes
- **WHEN** unchanged import-time structure and the audited execution relationship prove the changed body does not participate in schema production
- **THEN** expensive qualification is omitted while complete ordinary compatibility and consumer checks run

#### Scenario: A runtime or producer input changes
- **WHEN** relevant inputs or execution identity differ or cannot be verified
- **THEN** previous success cannot silently authorize skipping required qualification
