## Purpose

A writer renders the dict IR as one output format. It reads the IR and never
writes into it, so a caller can render the same IR to several formats, or keep
it, and every rendering starts from the IR the caller built. What a format
needs that the IR does not hold, such as native Junos JSON spellings, the
writer applies to its own copy.

## ADDED Requirements

### Requirement: A writer leaves the IR it is given unchanged

WHEN any writer (set, structured, JSON, YAML) renders an IR through
`junoscfg.convert.from_dict` THEN the system SHALL leave that IR, every nested
mapping and list in it, its values and its key order exactly as the caller
passed them; the output is the same as when the writer was handed its own
copy. This holds for the IR every reader gives (`junoscfg.convert.to_dict`)
and for the spellings a caller may build by hand that the JSON writer
normalizes for the device: a presence flag as `true` or `{}`, a single leaf
as a one-element list, and `groups` in its `group` wrapper.
Tests: `tests/unit/convert/test_convert_roundtrip.py::TestNoWriterChangesTheIrItIsGiven::test_a_hand_built_ir_is_left_unchanged`, `tests/unit/convert/test_convert_roundtrip.py::TestNoWriterChangesTheIrItIsGiven::test_a_read_ir_is_left_unchanged`

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
