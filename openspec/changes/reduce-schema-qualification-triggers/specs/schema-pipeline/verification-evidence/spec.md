## ADDED Requirements

### Requirement: Dependency selection ignores only editable root version

WHEN dependency relevance is computed THEN the application SHALL fingerprint the complete parsed uv.lock with only the nonempty version field of the unique junoscfg package whose source is exactly editable dot removed; malformed TOML, absent or ambiguous root records, or an unexpected root source SHALL refuse. Every other parsed field SHALL remain represented.
Tests: `tests/tooling/test_schema_dependencies.py::test_only_root_version_is_ignored`, `tests/tooling/test_schema_dependencies.py::test_ambiguous_or_invalid_root_refuses`

#### Scenario: Release bookkeeping changes only the project version

- **WHEN** only the unique editable root package version changes
- **THEN** the dependency fingerprint remains identical and the lock edit selects only the cheap consistency tier

#### Scenario: Any other lock data changes

- **WHEN** a dependency version, source, artifact hash, root dependency, Python constraint or other parsed field changes
- **THEN** the fingerprint changes and cannot be accepted until its committed projection is refreshed

### Requirement: Dependency consistency is a truthful cheap obligation

WHEN a lock, fingerprint or guard input changes THEN a first native guard tier SHALL execute consistency validation with its own required obligation, without claiming schema assertions ran; missing, malformed or stale fingerprints SHALL fail without leaving successful guard completion. Ordinary full-suite tests and every schema adapter execution SHALL enforce the same check before expensive schema work.
Tests: `tests/tooling/test_schema_dependencies.py::test_guard_publishes_only_consistency`, `tests/tooling/test_schema_dependencies.py::test_committed_fingerprint_is_current`, `tests/tooling/test_schema_dependencies.py::test_schema_preflight_refuses_stale_dependencies`

#### Scenario: Dependency changes without refreshing the projection

- **WHEN** uv.lock changes semantically and its fingerprint remains stale
- **THEN** expensive-only selection executes the cheap guard and fails, ordinary verification fails, and direct schema execution refuses before parsing or generation

#### Scenario: Actual dependency update is prepared

- **WHEN** the fingerprint is refreshed for a relevant lock change
- **THEN** its changed path selects both existing real-schema tiers as well as the cheap consistency guard

#### Scenario: Guard execution fails after earlier success

- **WHEN** consistency validation encounters invalid or mismatched input after a successful prior guard
- **THEN** no successful guard result survives and no schema test IDs are published
