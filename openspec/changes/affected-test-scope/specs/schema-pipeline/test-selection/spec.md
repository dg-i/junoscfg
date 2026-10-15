## MODIFIED Requirements

### Requirement: Tooling and shared inputs receive coverage

WHEN an existing tooling module has demonstrable test consumers THEN the selector SHALL include its transitive test consumers, including consumers outside tooling; WHEN dependency discovery is uncertain, a tool is deleted or unmapped, or tooling configuration changes THEN it SHALL retain conservative broad coverage. WHEN a test module changes or is deleted THEN the selector SHALL include it while it exists and the test modules importing it, transitively, under the same fixture and uncertainty rules; a deleted tools module SHALL also select its remaining importers and readers. WHEN any tests/tools Python module changes THEN the selector's own real-tree assertions SHALL run. Root pytest configuration (conftest.py, pytest.ini, tox.ini, setup.cfg and similar) SHALL select the full suite. Shared fixtures, data, project configuration, lock and shipped artifacts SHALL retain full-suite selection. Unrelated change bookkeeping SHALL NOT broaden selection solely due to its directory or commit boundary.
Tests: `tests/tooling/test_affected_tests.py::TestSharedInputsReceiveCoverage::test_tooling_inputs_select_tooling`, `tests/tooling/test_affected_tests.py::TestSharedInputsReceiveCoverage::test_shared_data_selects_everything`, `tests/tooling/test_affected_tests.py::TestToolConsumersDetermineSelection::test_real_execution_consumers_are_selected`, `tests/tooling/test_affected_tests.py::TestToolConsumersDetermineSelection::test_uncertain_discovery_never_silently_narrows`, `tests/tooling/test_affected_tests.py::TestToolConsumersDetermineSelection::test_a_test_module_selects_its_importers_transitively`, `tests/tooling/test_affected_tests.py::TestATestChangeSelectsItself::test_a_test_module_selects_the_tests_that_import_it`, `tests/tooling/test_affected_tests.py::TestATestChangeSelectsItself::test_shared_ground_selects_everything`, `tests/tooling/test_affected_tests.py::TestTheSelectorsOwnAssertionsFollowTheGraph::test_any_tests_or_tools_module_selects_the_selector_tests`, `tests/tooling/test_affected_tests.py::TestToolConsumersDetermineSelection::test_a_deleted_test_module_selects_its_remaining_importers`, `tests/tooling/test_affected_tests.py::TestToolConsumersDetermineSelection::test_a_deleted_tool_selects_its_remaining_importers`, `tests/tooling/test_affected_tests.py::TestToolConsumersDetermineSelection::test_a_deleted_tool_the_root_conftest_names_selects_everything`, `tests/tooling/test_affected_tests.py::TestToolConsumersDetermineSelection::test_a_tool_named_indirectly_selects_its_user`

#### Scenario: Tool script or device corpus changes

- **WHEN** tools/schema_verification.py or tests/data/device/grammar-corpus.json changes
- **THEN** all demonstrable transitive test consumers with conservative uncertainty fallback, or the full default suite respectively, are selected

#### Scenario: Tooling configuration remains conservative

- **WHEN** an unknown tools configuration, verification-costs.json, tach.toml or pre-commit configuration changes
- **THEN** tooling coverage remains broad

#### Scenario: Shared fixture outranks a narrow module

- **WHEN** a changed tool reaches tests/conftest.py or shared support
- **THEN** the full suite is selected

#### Scenario: A test module's helpers are imported elsewhere

- **WHEN** tests/tooling/test_schema_verification.py, whose helpers other schema test modules import, changes
- **THEN** those importing modules are selected with it

#### Scenario: A deleted module's importers still run

- **WHEN** tests/corpus/test_schema_data.py, whose helpers tooling tests import, is deleted
- **THEN** those importing tests are selected

#### Scenario: Independent bookkeeping adds no execution dependency

- **WHEN** change metrics or review records accompany a tool edit
- **THEN** selection is identical to that tool edit alone

## ADDED Requirements

### Requirement: Ordinary execution retains exact evidence identity

WHEN Strategy A is enabled THEN the ordinary affected-test runner SHALL use the shared command-evidence authority for its actual selected pytest command; unavailable identity SHALL execute tests normally, and failed execution SHALL return failure without automatic retry. WHEN the policy is disabled THEN tests SHALL run directly. Focused evidence SHALL NOT stand in for a different full coverage obligation.
Tests: `tests/tooling/test_affected_execution.py::test_selected_command_is_the_shared_evidence_obligation`, `tests/tooling/test_affected_execution.py::test_shared_execution_failure_is_not_relabelled_or_retried`, `tests/tooling/test_affected_execution.py::test_unavailable_evidence_or_disabled_policy_executes_tests`, `tests/tooling/test_affected_execution.py::test_undeclared_inputs_cannot_consult_a_success_receipt`

#### Scenario: Missing identity cannot skip a test

- **WHEN** a deleted tracked input prevents native identity construction
- **THEN** the selected tests execute and their real exit status is returned

#### Scenario: Failed command remains failed

- **WHEN** the shared command execution reports failure
- **THEN** the hook fails without retrying or replacing its result

#### Scenario: Ignored or external inputs remain conservative

- **WHEN** private corpus/schema discovery, external overrides, unknown pytest options or untracked files beside the tested code can change unbound execution inputs
- **THEN** the runner executes tests directly without consulting old ordinary success evidence

### Requirement: Repository files a test reads receive coverage

WHEN a repository file outside the package, test and tooling trees changes THEN the selector SHALL include the test consumers of every tools/tests module reading that file, or a directory above it, through a path anchored in the repository; a path read only inside a test function that no other module imports SHALL reach only its module. WHEN a module outside tooling passes the bare root or a computed path below it, or cannot be parsed or followed, THEN it SHALL be treated as reading every such file, without escalating unrelated selections. Unclassified configuration SHALL also select the tooling suite; documents and change records SHALL add nothing beyond their readers. Package data SHALL select like its package's source, and a non-Python file at the package root SHALL select the full suite. Changed paths SHALL include a moved file's old path.
Tests: `tests/tooling/test_affected_tests.py::TestRepositoryFilesATestReadsReceiveCoverage::test_a_file_a_test_reads_selects_that_test`, `tests/tooling/test_affected_tests.py::TestRepositoryFilesATestReadsReceiveCoverage::test_a_directory_shared_support_reads_selects_everything`, `tests/tooling/test_affected_tests.py::TestRepositoryFilesATestReadsReceiveCoverage::test_package_data_selects_its_package`, `tests/tooling/test_affected_tests.py::TestRepositoryFilesATestReadsReceiveCoverage::test_unclassified_configuration_keeps_tooling_coverage`, `tests/tooling/test_affected_tests.py::TestRepositoryFilesATestReadsReceiveCoverage::test_documents_and_change_records_nobody_reads_select_nothing`, `tests/tooling/test_affected_tests.py::TestToolConsumersDetermineSelection::test_a_named_root_path_is_a_dependency`, `tests/tooling/test_affected_tests.py::TestToolConsumersDetermineSelection::test_a_path_read_inside_a_test_reaches_no_importer`, `tests/tooling/test_affected_tests.py::TestToolConsumersDetermineSelection::test_a_root_wide_read_outside_tooling_reaches_every_outside_file`, `tests/tooling/test_affected_tests.py::TestToolConsumersDetermineSelection::test_other_spellings_of_a_root_read_are_found`, `tests/tooling/test_affected_tests.py::TestToolConsumersDetermineSelection::test_a_path_kept_in_an_attribute_or_computed_name_is_a_read`, `tests/tooling/test_affected_tests.py::TestToolConsumersDetermineSelection::test_a_test_another_module_runs_keeps_its_importers`, `tests/tooling/test_affected_tests.py::TestToolConsumersDetermineSelection::test_an_unparsable_module_reaches_outside_files_without_escalating`, `tests/tooling/test_affected_tests.py::TestWithNoFilesTheChangeComesFromGit::test_a_rename_lists_the_old_path_too`

#### Scenario: Workflow file read by a policy test

- **WHEN** .github/workflows/ci.yml changes
- **THEN** tests/tooling/test_type_policy.py is selected

#### Scenario: Shared support declares a directory

- **WHEN** a file under examples/ changes, is added or is deleted
- **THEN** the full default suite is selected

#### Scenario: A read file is moved

- **WHEN** .github/workflows/ci.yml is renamed
- **THEN** the changed paths include its old path, which selects its reader

#### Scenario: Shipped package data changes

- **WHEN** src/junoscfg/audit/data/unused-types.yaml changes
- **THEN** the selection equals that of a source change in the audit package

#### Scenario: Unread change records stay inexpensive

- **WHEN** only OpenSpec change records, changelog fragments, skills or unread documents change
- **THEN** no tests are selected
