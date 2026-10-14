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
Tests: `tests/tooling/test_affected_execution.py::test_selected_command_is_the_shared_evidence_obligation`, `tests/tooling/test_affected_execution.py::test_shared_execution_failure_is_not_relabelled_or_retried`, `tests/tooling/test_affected_execution.py::test_unavailable_evidence_or_disabled_policy_executes_tests`, `tests/tooling/test_affected_execution.py::test_undeclared_inputs_cannot_consult_a_success_receipt`

#### Scenario: Missing identity cannot skip a test

- **WHEN** a deleted tracked input prevents native identity construction
- **THEN** the selected tests execute and their real exit status is returned

#### Scenario: Failed command remains failed

- **WHEN** the shared command execution reports failure
- **THEN** the hook fails without retrying or replacing its result

#### Scenario: Ignored or external inputs remain conservative

- **WHEN** private corpus/schema discovery, external overrides or unknown pytest options can change unbound execution inputs
- **THEN** the runner executes tests directly without consulting old ordinary success evidence

### Requirement: Repository files a test reads receive coverage

WHEN a repository file outside the package, test and tooling trees changes THEN the selector SHALL include the test consumers of every tools/tests module reading that file, or a directory above it, through a path anchored in the repository; a path read only inside a test function that no other module imports SHALL reach only its module. WHEN a module outside tooling passes the bare root or a computed path below it, or cannot be parsed or followed, THEN it SHALL be treated as reading every such file, without escalating unrelated selections. Unclassified configuration SHALL also select the tooling suite; documents and change records SHALL add nothing beyond their readers. Package data SHALL select like its package's source, and a non-Python file at the package root SHALL select the full suite. Changed paths SHALL include a moved file's old path.
Tests: `tests/tooling/test_affected_tests.py::TestRepositoryFilesATestReadsReceiveCoverage::test_a_file_a_test_reads_selects_that_test`, `tests/tooling/test_affected_tests.py::TestRepositoryFilesATestReadsReceiveCoverage::test_a_directory_shared_support_reads_selects_everything`, `tests/tooling/test_affected_tests.py::TestRepositoryFilesATestReadsReceiveCoverage::test_package_data_selects_its_package`, `tests/tooling/test_affected_tests.py::TestRepositoryFilesATestReadsReceiveCoverage::test_unclassified_configuration_keeps_tooling_coverage`, `tests/tooling/test_affected_tests.py::TestRepositoryFilesATestReadsReceiveCoverage::test_documents_and_change_records_nobody_reads_select_nothing`, `tests/tooling/test_affected_tests.py::TestToolConsumersDetermineSelection::test_a_named_root_path_is_a_dependency`, `tests/tooling/test_affected_tests.py::TestToolConsumersDetermineSelection::test_a_path_read_inside_a_test_reaches_no_importer`, `tests/tooling/test_affected_tests.py::TestToolConsumersDetermineSelection::test_a_root_wide_read_outside_tooling_reaches_every_outside_file`, `tests/tooling/test_affected_tests.py::TestToolConsumersDetermineSelection::test_other_spellings_of_a_root_read_are_found`, `tests/tooling/test_affected_tests.py::TestToolConsumersDetermineSelection::test_a_test_another_module_runs_keeps_its_importers`, `tests/tooling/test_affected_tests.py::TestToolConsumersDetermineSelection::test_an_unparsable_module_reaches_outside_files_without_escalating`, `tests/tooling/test_affected_tests.py::TestWithNoFilesTheChangeComesFromGit::test_a_rename_lists_the_old_path_too`

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
