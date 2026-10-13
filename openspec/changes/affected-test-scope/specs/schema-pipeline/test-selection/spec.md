## MODIFIED Requirements

### Requirement: Tooling and shared inputs receive coverage

WHEN an existing tooling module has demonstrable test consumers THEN the selector SHALL include its transitive test consumers, including consumers outside tooling; WHEN dependency discovery is uncertain, a tool is deleted or unmapped, or tooling configuration changes THEN it SHALL retain conservative broad coverage. Shared fixtures, data, project configuration, lock and shipped artifacts SHALL retain full-suite selection. Unrelated change bookkeeping SHALL NOT broaden selection solely due to its directory or commit boundary.
Tests: `tests/tooling/test_affected_tests.py::TestSharedInputsReceiveCoverage::test_tooling_inputs_select_tooling`, `tests/tooling/test_affected_tests.py::TestSharedInputsReceiveCoverage::test_shared_data_selects_everything`

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
