# conversion/device-output-comparison Specification

## Purpose
Give change reviewers one reusable record and diff tool for explaining conversion changes over immutable device captures.

## Requirements

### Requirement: Record every available rendering and output
WHEN record OUT.json is run from a repository tree THEN the tool SHALL read the manifest's available conf, set, json and xml gzip renderings in memory, convert each to set, structured, json and yaml through junoscfg.convert_config_result, and write a deterministically keyed JSON result without modifying captures.
Tests: `tests/tooling/test_compare_device_outputs.py::test_record_covers_the_matrix_and_preserves_result_evidence`

#### Scenario: Plain records retain evidence
- **WHEN** six synthetic captures each provide four renderings and record is called without anonymization
- **THEN** 96 conversion keys are present, each with the output and sorted unique diagnostic triples (source, severity, path with missing path as empty), and sorted field-prefixed diagnostic messages including warnings
- **THEN** a conversion exception stores only its class and later conversions continue; absent manifest rendering files are skipped as in the template

### Requirement: Repeat each anonymization mode
WHEN record OUT.json --anonymize is run THEN the tool SHALL include plain, ten individual rules and all rules together, using the template's fixed salt and rule selections for each conversion.
Tests: `tests/tooling/test_compare_device_outputs.py::test_anonymized_record_covers_each_rule_and_plain`

#### Scenario: The rule matrix is complete
- **WHEN** six synthetic captures provide four renderings and anonymization is enabled
- **THEN** 1,152 keys cover all output formats and each mode, with one enabled selection per individual mode and every selection in all

### Requirement: Explain every changed record field
WHEN diff BASE.json HEAD.json is run THEN the tool SHALL compare the sorted union of conversion keys, report changed and total counts, emit a zero-context unified diff for output changes and base/head values for other changed fields.
Tests: `tests/tooling/test_compare_device_outputs.py::test_diff_explains_outputs_diagnostics_exceptions_and_key_changes`

#### Scenario: Changes and stable records
- **WHEN** records have an unchanged key, output edit, diagnostic and field-warning edits, exception edit, added key and removed key
- **THEN** only changed keys are reported in sorted order, every changed field is shown and identical records report zero differences

### Requirement: Keep the existing developer command door
WHEN the script is invoked with record OUT.json [--anonymize] or diff BASE.json HEAD.json THEN the tool SHALL execute the corresponding operation using the existing positional arguments and report counts on stdout.
Tests: `tests/tooling/test_compare_device_outputs.py::test_script_record_and_diff_commands`

#### Scenario: Existing workflow arguments
- **WHEN** the shared script is invoked from a synthetic repository tree
- **THEN** record writes its result and diff on identical records reports zero changes; no schema, device, network or separate comparison framework is used
