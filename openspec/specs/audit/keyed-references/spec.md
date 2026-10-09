# audit/keyed-references Specification

## Purpose
The unused-object audit reads a keyed entry's reference from the key fields
the structure tree names, so a field that names an object counts as its use
and a discriminator never does.

## Requirements

### Requirement: A key field that names an object is the reference

WHEN the audit walker meets an entry keyed by several fields THEN it SHALL
walk each key field as a leaf under its own tree node, so an enum key field
such as `list-type` records no occurrence and `list-name` records one for the
object it names, and `find_unused` SHALL count it as a use of the `as-list`
or `as-list-group` of that name.
Tests: `tests/test_audit/test_walker.py::TestKeyedEntries::test_list_name_is_the_reference`, `tests/test_audit/test_walker.py::TestKeyedEntries::test_list_type_is_no_reference`, `tests/test_audit/test_regressions.py::TestKeyedReferences::test_an_as_list_used_by_as_path_neighbors_is_not_unused`, `tests/test_audit/test_walker.py::TestKeyedEntries::test_the_device_json_gives_the_same_reference`, `tests/test_audit/test_regressions.py::TestKeyedReferences::test_a_name_used_by_one_list_type_does_not_use_the_other`, `tests/test_audit/test_types.py::TestUsed::test_reference_removes_finding`

#### Scenario: AS-list reference

- **WHEN** the IR holds `from as-path-neighbors as-list AS-LIST-A`
- **THEN** the walker records exactly one occurrence of `AS-LIST-A` and none
  of `as-list`

#### Scenario: A used and an unused AS list

- **WHEN** `policy-options as-list AS-LIST-A` and `AS-LIST-B` are defined and
  only `AS-LIST-A` is referenced through `as-path-neighbors`
- **THEN** `find_unused` reports `AS-LIST-B` and not `AS-LIST-A`

### Requirement: A single value key field is the entry key

WHEN the audit walker meets an entry keyed by one value field, beside any key
choice THEN it SHALL read that field from `entry_keys()` as the entry key,
record nothing for the key choice's keyword, and fall back to neither `name`
nor `community-name` nor `fe`.
Tests: `tests/test_audit/test_walker.py::TestEntryKeys::test_a_single_key_other_than_name`, `tests/test_audit/test_walker.py::TestEntryKeys::test_a_community_action_is_keyed_community_name`, `tests/test_audit/test_walker.py::TestEntryKeys::test_named_list_entry_key`

#### Scenario: Keys other than name

- **WHEN** the IR holds `from prefix-list-filter plf-a orlonger` and
  `then community add comm-a`
- **THEN** `plf-a` and `comm-a` are each recorded once as entry keys, and
  `orlonger` and `add` not at all

#### Scenario: A list keyed name

- **WHEN** the IR holds `policy-statement FOO`
- **THEN** `FOO` is recorded once as an entry key, as before
