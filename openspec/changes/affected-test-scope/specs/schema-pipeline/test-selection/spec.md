## MODIFIED Requirements

### Requirement: Tooling and shared inputs receive coverage

WHEN an existing tooling module has demonstrable test consumers THEN the selector SHALL include its transitive test consumers, including consumers outside tooling; WHEN dependency discovery is uncertain, a tool is deleted or unmapped, or tooling configuration changes THEN it SHALL retain conservative broad coverage. Shared fixtures, data, project configuration, lock and shipped artifacts SHALL retain full-suite selection. Unrelated change bookkeeping SHALL NOT broaden selection solely due to its directory or commit boundary.
Tests: `tests/tooling/test_affected_tests.py::TestSharedInputsReceiveCoverage::test_tooling_inputs_select_tooling`, `tests/tooling/test_affected_tests.py::TestSharedInputsReceiveCoverage::test_shared_data_selects_everything`, `tests/tooling/test_affected_tests.py::TestToolConsumersDetermineSelection::test_real_execution_consumers_are_selected`, `tests/tooling/test_affected_tests.py::TestToolConsumersDetermineSelection::test_uncertain_discovery_never_silently_narrows`

#### Scenario: Tool script or device corpus changes

- **WHEN** tools/schema_verification.py or tests/data/device/grammar-corpus.json changes
- **THEN** all demonstrable transitive test consumers with conservative uncertainty fallback, or the full default suite respectively, are selected

#### Scenario: Tooling configuration remains conservative

- **WHEN** an unknown tools configuration, verification-costs.json, tach.toml or pre-commit configuration changes
- **THEN** tooling coverage remains broad

#### Scenario: Shared fixture outranks a narrow module

- **WHEN** a changed tool reaches tests/conftest.py or shared support
- **THEN** the full suite is selected

#### Scenario: Independent bookkeeping adds no execution dependency

- **WHEN** change metrics or review records accompany a tool edit
- **THEN** selection is identical to that tool edit alone

## ADDED Requirements

### Requirement: Ordinary execution retains exact evidence identity

WHEN Strategy A is enabled THEN the ordinary affected-test runner SHALL use the shared command-evidence authority for its actual selected pytest command; unavailable identity SHALL execute tests normally, and failed execution SHALL return failure without automatic retry. WHEN the policy is disabled THEN tests SHALL run directly. Focused evidence SHALL NOT stand in for a different full coverage obligation.
Tests: `tests/tooling/test_affected_execution.py::test_selected_command_is_the_shared_evidence_obligation`, `tests/tooling/test_affected_execution.py::test_shared_execution_failure_is_not_relabelled_or_retried`, `tests/tooling/test_affected_execution.py::test_unavailable_evidence_or_disabled_policy_executes_tests`

#### Scenario: Missing identity cannot skip a test

- **WHEN** a deleted tracked input prevents native identity construction
- **THEN** the selected tests execute and their real exit status is returned

#### Scenario: Failed command remains failed

- **WHEN** the shared command execution reports failure
- **THEN** the hook fails without retrying or replacing its result
