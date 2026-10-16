## MODIFIED Requirements

### Requirement: Set validation reads every verb conversion reads

WHEN set input carries a `protect`, `activate`, `delete` or `deactivate` line THEN set
validation SHALL validate the statement path after the verb as `set` validates it, except
that the path may stop where one value would follow, and SHALL take the line only where it
names a statement the device can tag, as the set reader places the tag (one read-only walk,
`junoscfg.display.meta_target`, serves both): a container, a leaf, leaf-list or flag before
its value (the device prints `deactivate ... max-hello-size`), or a list entry after its whole
key (`deactivate routing-options static route 198.51.100.0/24`). A line SHALL be invalid when
it stops at a list's keyword without the entry's name (`protect policy-options
policy-statement`; the QFX5120 25.2R2-S1.5 refuses it, "syntax error, expecting
<identifier>"), names a leaf's value or one value of a leaf-list (`deactivate ... community
64496:2`; the device refuses it, "syntax error, expecting ';', [Enter], or '|'", and the set
reader refuses both), or stops inside an entry's key, before a keyword the key needs
(`route-filter 10.0.0.0/8` without its match type) or before a key value (`virtual-link
neighbor-id 10.255.255.1 transit-area`). This holds through `SetValidator.validate`,
`JunosValidator.validate_set`, `validate_set`, `validate_config`, `validate_structured` and CLI
`-v -i set|structured`. The validator reads the structure tree beside its grammar for a verb
line and raises `SchemaLoadError` where there is none. A `set` line SHALL still give a leaf
its value, and a line starting with any other word SHALL be rejected; an error message SHALL
carry the whole line, never a cut one. Every verb line of the committed device captures
stays valid.
Tests: `tests/unit/validate/test_set_validator.py::TestEveryVerbIsValidated::test_a_verb_line_is_validated_as_its_path`, `tests/unit/validate/test_set_validator.py::TestEveryVerbIsValidated::test_an_invalid_path_after_a_verb_is_reported`, `tests/unit/validate/test_set_validator.py::TestEveryVerbIsValidated::test_set_gives_a_leaf_its_value`, `tests/unit/validate/test_set_validator.py::TestEveryVerbIsValidated::test_another_verb_is_no_command`, `tests/unit/validate/test_set_validator.py::TestEveryVerbIsValidated::test_a_long_line_is_reported_whole`, `tests/unit/validate/test_set_validator.py::TestEveryVerbIsValidated::test_a_verb_line_names_no_value`, `tests/unit/validate/test_set_validator.py::TestEveryVerbIsValidated::test_a_verb_line_names_no_list_without_its_entry`, `tests/unit/validate/test_set_validator.py::TestEveryVerbIsValidated::test_a_verb_line_without_a_structure_tree_is_a_load_error`, `tests/unit/display/test_meta_path.py::TestAMetaPathNamesWhatTheReaderTags::test_the_target`, `tests/contract/test_every_door.py::TestEveryVerbNamesAStatementPath::test_every_door_agrees`, `tests/corpus/test_set_corpus.py::TestEveryCaptureValidatesAsSet::test_every_verb_line_of_the_capture_validates`, `tests/corpus/test_device_probes.py::TestEveryProbedLineValidatesAsTheDeviceTookIt::test_the_line`

#### Scenario: A protected group

- **WHEN** `protect groups GR-PROTECTED` follows the group's `set` lines
- **THEN** the input is valid through every door

#### Scenario: A deactivated leaf

- **WHEN** `deactivate system host-name` follows `set system host-name router1`
- **THEN** the input is valid, while `set system host-name` alone is not

#### Scenario: A line that stops inside an entry's key

- **WHEN** `deactivate policy-options policy-statement P term T from route-filter 10.0.0.0/8`
  follows the route filter's `set` line with its match type `exact`
- **THEN** the line is invalid through every door, as the set reader cannot place it

#### Scenario: A long invalid line

- **WHEN** a line longer than 80 characters is invalid
- **THEN** the error quotes it whole

#### Scenario: A list's keyword without its entry

- **WHEN** `protect policy-options policy-statement` or `deactivate policy-options
  policy-statement` follows `set policy-options policy-statement JUNOSCFG-PROBE term t1 then
  accept` (probe D5)
- **THEN** the line is invalid through every door, as the device refuses it

#### Scenario: One value of a leaf-list

- **WHEN** `deactivate routing-options static route 198.51.100.0/24 community 64496:2` follows
  the route's `set` lines (probe A2), or `deactivate system host-name router1` follows
  `set system host-name router1`
- **THEN** the line is invalid through every door, where `-v` said OK and conversion failed

#### Scenario: A keyed entry after its whole key

- **WHEN** `deactivate protocols ospf area 0.0.0.0 virtual-link neighbor-id 10.255.255.1
  transit-area 0.0.0.2` follows the entry's `set` line
- **THEN** the line is valid, and the line without its last value is invalid

#### Scenario: No structure tree beside the grammar

- **WHEN** a grammar directory holds no structure tree and a verb line is validated
- **THEN** `SchemaLoadError` names the missing tree; a `set` line still validates
