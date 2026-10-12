## ADDED Requirements

### Requirement: Proven hidden lists retain the declared key

WHEN a device-backed hidden list arrives as set, structured, JSON, YAML or XML THEN conversion SHALL retain the device's keyed list IR and omit the hidden XML element name in set and structured output; equal declared key tuples SHALL merge without fusing tokens into a key.
Tests: `tests/unit/convert/test_hidden_list_names.py::TestAHiddenListKeepsItsDeviceKey::test_every_reader_keeps_the_key`, `tests/unit/convert/test_hidden_list_names.py::TestAHiddenListKeepsItsDeviceKey::test_every_writer_omits_the_hidden_name`

#### Scenario: Device proven nested and composite keys

- **WHEN** route-filter-list rf_list address plus match choice, nested DHCP server-group/address, predefined-variable-defaults other-variables, bridge-domains domain or dynamic-tunnels dynamic-tunnel is converted
- **THEN** its IR has the device JSON key fields, and its set output has the capture's statements without XML-only words

### Requirement: Hidden entry identity uses every key component

WHEN hidden route-filter-list entries share an address but have different match choices, or the same complete key occurs twice THEN the reader SHALL keep distinct choices and merge only equal complete keys.
Tests: `tests/unit/convert/test_hidden_list_names.py::TestAHiddenListUsesTheWholeKey::test_choice_keys_remain_distinct`

#### Scenario: Exact versus orlonger

- **WHEN** exact and orlonger occur for one address and exact is repeated
- **THEN** there are two entries with distinct choice fields, no synthetic name

### Requirement: Real keyword children precede hidden entry matching

WHEN a token names a keyword child beside a hidden keyed list THEN the reader SHALL place that keyword child before trying a transparent entry key; a model with no declared key, an ordinary keyworded list, a leaf or an unknown child SHALL retain its existing treatment.
Tests: `tests/unit/convert/test_hidden_list_names.py::TestKeywordChildrenPrecedeHiddenKeys::test_the_keyword_is_not_an_entry_name`, `tests/unit/convert/test_hidden_list_names.py::TestUnrelatedModelsKeepTheirMeaning::test_models_outside_the_hidden_key_rule_are_preserved`

#### Scenario: Preserved boundary

- **WHEN** a keyword child competes with a positional hidden key, or a nonmatching model is read or written
- **THEN** no keyword, value, unknown statement or list entry is silently consumed as a hidden name
