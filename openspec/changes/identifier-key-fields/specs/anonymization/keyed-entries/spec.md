## Purpose

Anonymization reads a list entry's key fields as the leaves the structure tree
declares, so every rule sees a key value with its own type and path, and no
rule depends on a key the walker invents.

## ADDED Requirements

### Requirement: Key fields are leaves of their declared type

WHEN the anonymize walker meets a list entry THEN it SHALL hand each key field
`entry_keys()` names to the rules as the leaf the tree declares for it, with
that leaf's own type, and SHALL synthesise no leaf for `name`; an enum key
field such as `list-type` SHALL pass unchanged.
Tests: `tests/test_anonymize/test_walker.py::TestKeyFieldsAreLeaves::test_a_key_field_carries_its_declared_type`, `tests/test_anonymize/test_walker.py::TestKeyFieldsAreLeaves::test_no_name_leaf_is_synthesised`, `tests/test_anonymize/test_walker.py::TestKeyFieldsAreLeaves::test_an_enum_key_passes_unchanged`

#### Scenario: Two key fields

- **WHEN** the entry `{"list-type": "as-list", "list-name": "AS-LIST-A"}` is
  walked with every rule on
- **THEN** each rule sees `list-type` and `list-name` with their declared leaf
  types, and `list-type` stays `as-list`

#### Scenario: A list keyed name

- **WHEN** a `policy-statement` entry keyed `name` is walked
- **THEN** the rules see `name` as the tree's `name` leaf, not a leaf built
  from the list node

### Requirement: An AS-list reference survives anonymization

WHEN a configuration holding an AS-list reference inside a group is converted
through `convert_config` or CLI `convert` with `--anonymize-all`, or with
`--anonymize-as-numbers 64496` THEN the output SHALL keep the reference as one
`as-path-neighbors <list-type> <list-name>` statement with both key values,
`list-type` unchanged, and under `--anonymize-all` SHALL anonymize the group
name.
Tests: `tests/test_anonymize/test_integration.py::TestKeyedEntriesSurvive::test_an_as_list_reference_survives_anonymize_all`, `tests/test_anonymize/test_integration.py::TestKeyedEntriesSurvive::test_as_numbers_leave_the_as_list_reference_whole`, `tests/test_cli.py::TestCliAnonymize::test_anonymize_all_keeps_the_as_list_reference`

#### Scenario: Structured input, every rule on

- **WHEN** the structured form is converted to set with `--anonymize-all`
- **THEN** the line ends `as-path-neighbors as-list <name>`, with a name present

#### Scenario: AS numbers only

- **WHEN** the same input is converted with `--anonymize-as-numbers 64496`
- **THEN** the line ends `as-path-neighbors as-list AS-LIST-A`

### Requirement: No value anonymized before escapes

WHEN the anonymization test configurations are anonymized with every rule on
THEN every value the previous release replaced SHALL still be replaced, and the
anonymized output of `name`-keyed lists SHALL be byte-identical; phase 5 SHALL
stop and report any value whose treatment moves otherwise.
Tests: `tests/test_anonymize/test_integration.py::TestKeyedEntriesSurvive::test_no_value_anonymized_before_escapes`, `tests/test_anonymize/test_integration.py::TestKeyedEntriesSurvive::test_name_keyed_output_is_unchanged`

#### Scenario: An IP key keyed name

- **WHEN** an interface `address` entry keyed `name` holds `203.0.114.1/24`
  and is anonymized with `--anonymize-ips`
- **THEN** it is replaced exactly as before
