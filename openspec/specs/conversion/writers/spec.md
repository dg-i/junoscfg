# conversion/writers Specification

## Purpose

A writer renders the dict IR as one output format. It reads the IR and never
writes into it, so a caller can render the same IR to several formats, or keep
it, and every rendering starts from the IR the caller built. What a format
needs that the IR does not hold, such as native Junos JSON spellings, the
writer applies to its own copy.

## Requirements

### Requirement: A writer leaves the IR it is given unchanged

WHEN any writer (set, structured, JSON, YAML) renders an IR through
`junoscfg.convert.from_dict`, wrapped or with `wrap=False`, THEN the system SHALL leave that IR, every nested
mapping and list in it, its values and its key order exactly as the caller
passed them; the output is the same as when the writer was handed its own
copy. This holds for the IR every reader gives (`junoscfg.convert.to_dict`)
and for the spellings a caller may build by hand that the JSON writer
normalizes for the device: a presence flag as `true` or `{}`, tagged or four
lists deep, a single leaf as a one-element list, and `groups` in its `group`
wrapper or as a list; for these the JSON output stays the device's spelling
(`[null]` flags, scalar leaves, native `groups`), and a leaf-list with one
value stays a list. A presence flag inside a list (`[true]`, which the JSON
and YAML readers give) is held only to the IR staying unchanged and the output
equalling the copy's; which output the device expects for it is open
(NEW-R2, change 13).
Tests: `tests/unit/convert/test_convert_roundtrip.py::TestNoWriterChangesTheIrItIsGiven::test_a_hand_built_ir_is_left_unchanged`, `tests/unit/convert/test_convert_roundtrip.py::TestNoWriterChangesTheIrItIsGiven::test_the_json_writer_writes_the_device_spelling`, `tests/unit/convert/test_convert_roundtrip.py::TestNoWriterChangesTheIrItIsGiven::test_a_read_ir_is_left_unchanged`

#### Scenario: A presence flag written as true

- **WHEN** `{"system": {"services": {"ssh": true}}}` is rendered to JSON
- **THEN** the output holds `"ssh": [null]` and the caller's IR still holds `"ssh": true`

#### Scenario: A single leaf as a one-element list

- **WHEN** a login user with `"class": ["super-user"]` is rendered to JSON
- **THEN** the output holds `"class": "super-user"` and the caller's IR still holds the list

#### Scenario: Every reader's IR and every writer

- **WHEN** a catalogue configuration is read from each of its sources and the IR is rendered by each writer in turn
- **THEN** the IR after the last writer is the IR the reader gave, the set reader's `{}` presence flags and `groups` wrapper included

### Requirement: JSON output writes groups as the device does

WHEN the IR holds configuration groups, in the set reader's
`{"group": [...]}` wrapper or as a list THEN the JSON writer SHALL write
`"groups"` as the list of group entries, with no `group` wrapper, while every
other transparent container (`interfaces`, `routing-instances`, `vlans`) keeps
its wrapper. Device evidence: native JSON from a vMX on 23.2R2-S7.5
(`tests/data/device/jvd/vmx-23.2R2-S7.5/mdr1_acx7509.json.gz`,
`tests/data/device/synthetic/vmx-23.2R2-S7.5/junoscfg-oracle.json.gz`) and a
QFX5120 on 25.2R2-S1.5
(`tests/data/device/synthetic/qfx5120-25.2R2-S1.5/junoscfg-oracle.json.gz`).
Tests: `tests/contract/test_format_matrix.py::TestEveryReaderGivesTheShapeIr::test_the_source_reads_as_the_ir`

#### Scenario: Groups from set input

- **WHEN** `set groups mygroup system host-name r1` is converted to JSON
- **THEN** the output holds `"groups": [{"name": "mygroup", "system": {"host-name": "r1"}}]`

### Requirement: Writers retain keyworded leaves and nested triggers

WHEN any of the Set, structured, JSON, YAML or XML readers supplies keyworded timeout, limit, path or filename leaves or nested optical trigger content THEN each of the Set, structured, JSON and YAML writers SHALL preserve the independently specified IR; Set output SHALL retain each required keyword. Genuine positional traceoptions filenames and maximum-prefixes limits SHALL retain their supported spelling. Existing event-options trigger after/count behavior SHALL remain supported without claiming device Set equivalence.
Tests: `tests/contract/test_format_matrix.py::TestEveryReaderGivesTheShapeIr::test_the_source_reads_as_the_ir`, `tests/contract/test_format_matrix.py::TestEveryWriterKeepsTheIr::test_the_output_reads_back_as_the_ir`

#### Scenario: A keyworded timeout is retained

- **WHEN** a radius-server has timeout 10 or IS-IS overload has timeout 300
- **THEN** rendered Set and structured output retains timeout and readers recover that leaf

#### Scenario: An unrelated trigger retains its nested content

- **WHEN** otn-options trigger oc-los holds hold-time up 100
- **THEN** writers retain oc-los, hold-time and up 100

### Requirement: Flattening never silently discards richer child shapes

WHEN a flat-dict container carries a nested mapping or a list with values THEN the Set and structured writers SHALL preserve all child content by normal traversal rather than emitting a truncated flattened statement.
Tests: `tests/unit/convert/test_convert_roundtrip.py::TestAFlatHintPreservesRicherContent::test_nested_content_is_not_discarded`

#### Scenario: A flat hint encounters a nested child

- **WHEN** a container marked flat-dict contains nested child hold-time up 100
- **THEN** both writers retain that complete child independently of the hint

### Requirement: A writer notes a per-value leaf-list tag it cannot write

WHEN the IR tags one value of a leaf-list (`"@domain-search": [null, {"inactive": true}]`, as
JSON or YAML input may give it) THEN the set and structured writers SHALL write every value
and SHALL give one note, "N tag(s) on single values of a leaf-list dropped: set and
structured text have no form for one", counting each tag of each value (a comment is none),
instead of dropping the tag silently; the json, yaml-new and yaml
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
