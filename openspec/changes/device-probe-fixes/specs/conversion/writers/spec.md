## ADDED Requirements

### Requirement: A writer notes a per-value leaf-list tag it cannot write

WHEN the IR tags one value of a leaf-list (`"@domain-search": [null, {"inactive": true}]`, as
JSON or YAML input may give it) THEN the set and structured writers SHALL write every value
and SHALL give one note, "N tag(s) on single values of a leaf-list dropped: Junos tags a
leaf-list only as a whole", instead of dropping the tag silently; the json, yaml-new and yaml
writers SHALL keep the tag as before. The QFX5120 25.2R2-S1.5 refuses `deactivate
routing-options static route 198.51.100.0/24 community 64496:2` ("syntax error, expecting
';', [Enter], or '|'") and prints `"community": ["64496:1", "64496:2"]` with no per-value
annotation (probe A2), so set and structured text have no form for such a tag. Whether a
device loads a per-value tag from JSON is unproven.
Tests: `tests/unit/convert/test_meta_tags.py::TestAPerValueLeafListTagIsNoted::test_set_and_structured_note_it`, `tests/unit/convert/test_meta_tags.py::TestAPerValueLeafListTagIsNoted::test_json_yaml_and_yaml_new_keep_it`

#### Scenario: One deactivated domain-search value

- **WHEN** `{"configuration": {"system": {"domain-search": ["a.example", "b.example"],
  "@domain-search": [null, {"inactive": true}]}}}` is written as set and as structured
- **THEN** both values are written, no `deactivate` line or `inactive:` tag is written, and
  one note counts one dropped tag

#### Scenario: The same IR written as JSON

- **WHEN** the same input is written as json, yaml-new and yaml
- **THEN** `"@domain-search"` keeps the per-value tag and no note is given
