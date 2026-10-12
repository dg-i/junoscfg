# schema-pipeline/verification-evidence Specification

## Purpose
Schema verification records actual executed coverage and generated-artifact integrity against immutable physical inputs, so command success can support reviewed evidence reuse without changing the schema oracle.

## Requirements

### Requirement: Completion comes from executed outcomes

WHEN a schema shard finishes THEN the adapter SHALL publish exactly its required unique test and shard IDs only after exit zero, exact selected coverage, successful setup and teardown, and passed calls or expressly permitted executed skips; collection alone SHALL NOT constitute completion.
Tests: `tests/tooling/test_schema_verification.py::TestExecutedCompletion::test_passed_reports_complete_exact_ids`, `tests/tooling/test_schema_verification.py::TestExecutedCompletion::test_incomplete_failed_or_wrong_reports_refuse`

#### Scenario: Collected tests never execute

- **WHEN** every required ID is collected but no call outcome is observed
- **THEN** no successful completion manifest is published

### Requirement: Existing release skips stay truthful

WHEN an existing count test skips for an unpinned release THEN the adapter SHALL accept it only with the reviewed exact identity/reason and successful setup/teardown, retain the skipped outcome, and reject unexpected or all-skipped execution.
Tests: `tests/tooling/test_schema_verification.py::TestExecutedCompletion::test_allowed_skips_keep_identity_reason`

#### Scenario: Unpinned count executes its existing skip

- **WHEN** an allowed count test reports its exact release-specific skip
- **THEN** evidence records skipped with its observed reason and never calls it passed

### Requirement: Unknown physical inputs and versions refuse early

WHEN a shard prerequisite is missing, empty, symlinked, unknown-release, outside its declared physical path, or has unavailable/mismatched observable runtime versions THEN the adapter SHALL refuse before costly schema execution.
Tests: `tests/tooling/test_schema_verification.py::TestPhysicalInputs::test_missing_empty_symlink_or_unknown_dump_refuses`, `tests/tooling/test_schema_verification.py::TestPhysicalInputs::test_unknown_or_changed_runtime_refuses`, `tests/tooling/test_schema_verification_challenge.py::TestPrerequisitesBeforeExecution::test_shard_refuses_before_launching_pytest`, `tests/tooling/test_schema_verification_challenge.py::TestPrerequisitesBeforeExecution::test_sentinel_refuses_runtime_mismatch_before_generation`

#### Scenario: Legacy symlink points to a real dump

- **WHEN** a dump or any containing declared path is a symlink
- **THEN** the command refuses even when its target is readable

### Requirement: Real generation preserves the candidate

WHEN a shard runs THEN it SHALL execute the existing schema suite and real_artifacts generation, export actual temporary products to ignored stable paths, compare shipped-release protected products to settled committed products, and refuse failed execution or candidate/input mutation without publishing success.
Tests: `tests/tooling/test_schema_verification.py::TestCandidateIntegrity::test_inherited_hook_context_preserves_parent_repository`, `tests/tooling/test_schema_verification.py::TestCandidateIntegrity::test_real_runner_exports_artifacts_without_mutation`, `tests/tooling/test_schema_verification.py::TestCandidateIntegrity::test_mutated_inputs_or_failed_execution_publish_no_success`, `tests/tooling/test_schema_verification_challenge.py::TestFailureCannotPublishSuccess::test_actual_failed_run_cannot_retain_success_manifests`, `tests/tooling/test_schema_verification_challenge.py::TestQualifiedLifecycleRecordBoundary::test_fixed_tracked_record_changes_do_not_block_execution`, `tests/tooling/test_schema_verification_challenge.py::TestQualifiedLifecycleRecordBoundary::test_record_update_during_execution_does_not_mutate_the_candidate`, `tests/tooling/test_schema_verification_challenge.py::TestQualifiedLifecycleRecordBoundary::test_nonrecord_or_explicit_input_mutation_remains_a_failure`, `tests/tooling/test_schema_verification_challenge.py::TestQualifiedLifecycleRecordBoundary::test_native_tracked_events_allow_the_next_real_wrapper_execution`, `tests/tooling/test_schema_verification_challenge.py::TestQualifiedLifecycleRecordBoundary::test_explicit_read_inputs_override_fixed_record_spelling`, `tests/tooling/test_schema_verification_challenge.py::TestQualifiedLifecycleRecordBoundary::test_source_renamed_to_a_fixed_record_is_not_evidence_only`, `tests/tooling/test_schema_verification_challenge.py::TestQualifiedLifecycleRecordBoundary::test_staged_source_with_restored_working_bytes_refuses_before_execution`

#### Scenario: A test mutates its schema input

- **WHEN** execution changes a declared input or tracked candidate
- **THEN** the result is rejected and no completion manifest survives

### Requirement: Generation sentinel and stability use real work

WHEN integrity is checked THEN assertion execution SHALL run once per selected release, and a separate generation qualification SHALL execute fresh public ArtifactBuilder generation twice under the existing template stability mechanism, compare all four protected products and all metadata except generated_at, and compare shipped-release products to committed artifacts. Generation completion SHALL describe generation obligations, never claim another pytest execution. The standalone sentinel remains available but is not scheduled redundantly.
Tests: `tests/tooling/test_schema_qualification.py::TestGenerationQualification::test_fresh_build_exports_integrity_without_pytest`, `tests/tooling/test_schema_qualification.py::TestGenerationQualification::test_failure_clears_completion`, `tests/tooling/test_schema_verification_metadata.py::TestMetadataStabilityAcrossExecutedPasses::test_only_generated_at_may_change`

#### Scenario: Protected generated bytes change

- **WHEN** regenerated protected products or semantic metadata differ from committed shipped products or the actual second pass
- **THEN** qualification fails without refreshing the candidate and template evidence cannot be reused

#### Scenario: Assertion failure precedes generation

- **WHEN** the assertion tier has no successful completion record
- **THEN** generation qualification refuses before invoking the public builder

### Requirement: Qualified application seeds remain inactive

WHEN qualification is configured THEN routine automatic tiers SHALL select only the shipped release on generator/schema relevant paths, with assertions before generation stability; older releases SHALL remain available for explicit compatibility qualification. Existing activation, caps, surfaces and template-owned evidence validity SHALL remain authoritative; assertion exports are local diagnostics, while qualified generation exports are hash-bound stability outputs.
Tests: `tests/tooling/test_schema_verification.py::TestEvidenceConfiguration::test_shipped_assertion_and_generation_tiers_are_declared`, `tests/tooling/test_schema_verification.py::TestEvidenceConfiguration::test_rollback_retains_evidence_and_uncached_declarations`

#### Scenario: Safe scaffold recommendations are resolved

- **WHEN** scaffold recommends generic api, canonical sources or larger limits
- **THEN** existing application policies remain authoritative; qualification selection does not alter activation or those policies

#### Scenario: Workflow-only correction

- **WHEN** wrapper tests, documentation or bookkeeping change without generator/schema paths changing
- **THEN** automatic path selection does not launch real-schema qualification

#### Scenario: Explicit compatibility qualification

- **WHEN** an operator selects a declared older release
- **THEN** its unchanged exact schema assertions and generation qualification are available

### Requirement: Invalidated or rolled-back evidence never stands in for execution

WHEN input, generator, lock, runtime, coverage, candidate or integrity evidence is invalidated THEN the existing template SHALL refuse or rerun as applicable; rollback SHALL retain evidence and execute declared tiers uncached without importing historical evidence.
Tests: `tests/tooling/test_schema_verification.py::TestEvidenceConfiguration::test_rollback_retains_evidence_and_uncached_declarations`

#### Scenario: Verification is disabled

- **WHEN** rollback disables verification after evidence exists
- **THEN** retained evidence remains and declared actual commands execute uncached

### Requirement: Qualification reports elapsed phases

WHEN assertions or public generation execute THEN evidence SHALL report nonnegative measured elapsed seconds for each observed pytest setup/call/teardown and public build, without treating timing as completion or altering existing outcomes.
Tests: `tests/tooling/test_schema_qualification.py::TestTimingEvidence::test_executed_phase_durations_are_recorded`

#### Scenario: A real assertion completes

- **WHEN** pytest emits successful setup, call and teardown reports
- **THEN** the outcomes retain their identity and a separate timing mapping reports all three measured phases
