## Purpose

Select conservative, nonduplicated ordinary pytest coverage for repository edits while keeping documentation-only commits inexpensive.

## ADDED Requirements

### Requirement: Tooling and shared inputs receive coverage

WHEN a tooling script or configuration, the test hook configuration, or tach configuration changes THEN the selector SHALL include the tooling suite; WHEN shared test data changes THEN it SHALL include the full default suite.
Tests: `tests/tooling/test_affected_tests.py::TestSharedInputsReceiveCoverage::test_tooling_inputs_select_tooling`, `tests/tooling/test_affected_tests.py::TestSharedInputsReceiveCoverage::test_shared_data_selects_everything`

#### Scenario: Tool script or device corpus changes

- **WHEN** tools/schema_verification.py or tests/data/device/grammar-corpus.json changes
- **THEN** the tooling suite or full default suite respectively is selected

### Requirement: Deleted tests retain executable coverage

WHEN a test file or conftest is deleted THEN the selector SHALL select its nearest existing directory under tests, and the pre-commit hook SHALL invoke the selector even for a deletion-only commit.
Tests: `tests/tooling/test_affected_tests.py::TestDeletedTestsRetainCoverage::test_deleted_test_selects_existing_ancestor`, `tests/tooling/test_affected_tests.py::TestSharedInputsReceiveCoverage::test_hook_runs_for_deletion_only_commits`

#### Scenario: Last test in a nested directory is removed

- **WHEN** a removed test path no longer has an existing parent directory
- **THEN** its nearest existing test ancestor is selected instead of a nonexistent pytest target

### Requirement: Selection does not duplicate directory coverage

WHEN multiple changed files select a directory and its descendants THEN the selector SHALL emit only the covering directory while preserving existing package/importer and unrelated-document behavior.
Tests: `tests/tooling/test_affected_tests.py::TestSharedInputsReceiveCoverage::test_ancestor_selection_subsumes_descendants`, `tests/tooling/test_affected_tests.py::TestATestChangeSelectsItself::test_a_document_selects_nothing`

#### Scenario: Tool and its regression test change together

- **WHEN** a tool change selects tests/tooling/ and its regression test also changes
- **THEN** tests/tooling/ is emitted once without the redundant individual file
