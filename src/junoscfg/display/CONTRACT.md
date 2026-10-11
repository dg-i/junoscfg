# junoscfg.display — contract

Interface: `__all__` in `__init__.py`, module entry and expose list in `tach.toml`.

## Not for

Display rendering only in name: the shared kernel six of the eight packages import. Nor for
placing a tag: conversion reads the curly lexer's `statements()` through the schema
(`tests/unit/convert/test_meta_tags.py`); the deprecated `SetConverter.to_set()` tags a last node.

## Invariants

- Nothing here imports from a higher layer; `display` and `input` are the bottom of the DAG — enforced by `tach check`.
- Importing this package pulls in neither lxml nor the schema artifacts: both load
  lazily — enforced by `tests/unit/display/test_to_yaml.py::TestLazyXmlImport::test_importing_the_package_loads_no_lxml`.
- `entry_keys()` and `statement_children()` are the one answer for an entry's key
  fields and a statement's children, and no module reads a retired key spelling
  (`fe`, `values-only`, `community-name`, `_v<n>`) — enforced by `tests/unit/display/test_entry_keys.py::TestEntryKeys::test_the_helper_answers_the_key_tuple`, `tests/unit/display/test_entry_keys.py::TestStatementChildren::test_statement_children_drop_the_key_fields` and `tests/tooling/test_entry_key_spellings.py::TestEntryKeysComeFromTheTree::test_no_module_keeps_its_own_key`.
- `schema_child()` resolves a statement valid at every level from the root; no
  flag helper or module keeps their names, and the floor serves only a tree that
  declares none — enforced by `tests/unit/display/test_universal_statements.py::TestTheFloorIsForATreeThatDeclaresNone::test_conversion_never_answers_from_the_floor` and `tests/tooling/test_universal_statement_names.py::TestUniversalStatementsComeFromTheTree::test_no_module_keeps_their_names`.
- `format_value()` spells a value by its leaf's type, never its look, and readers keep as written exactly the `policy-algebra` tokens it writes as they are, so every value written reads back — enforced by `tests/unit/display/test_value_format.py::TestEveryValueReadsBackAsWritten::test_every_short_value_reads_back` and `tests/unit/display/test_value_format.py::TestEveryValueReadsBackAsWritten::test_a_policy_algebra_value_reads_back`.

## Precedent

- `junoscfg.display.detect_format` — the one content classifier; each caller
  supplies the formats its public contract permits it to infer.
- `junoscfg.display.xml_to_dict` — the one XML walker; XML-to-YAML serialization
  and conversion input consume the same JSON-equivalent mapping.
- `junoscfg.display.load_schema_tree` — the lazy-cached accessor every artifact read copies.
