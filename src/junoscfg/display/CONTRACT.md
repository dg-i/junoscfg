# junoscfg.display — contract

Interface: `__all__` in `__init__.py`, module entry and expose list in `tach.toml`.

## Not for

Display rendering only in name: the shared kernel six of the eight packages
import; `constants.py` and `config_store.py` are a schema flag table and a tree.
Nor for placing a tag: schema-free `SetConverter.to_set()` gives a one-line
statement's tag to its last node; conversion reads `statements()` through the
schema, where an entry ends (`tests/unit/convert/test_meta_tags.py`).

## Invariants

- Nothing here imports from a higher layer; `display` and `input` are the bottom of the DAG — enforced by `tach check`.
- Importing this package pulls in neither lxml nor the schema artifacts:
  `load_schema_tree()` is lazy and cached, and the XML path imports lxml on
  first use — enforced by
  `tests/unit/display/test_to_yaml.py::TestLazyXmlImport::test_importing_the_package_loads_no_lxml`.
- `entry_keys()` and `statement_children()` are the one answer for an entry's key
  fields and a statement's children, and no module reads a retired key spelling
  (`fe`, `values-only`, `community-name`, `_v<n>`) — enforced by `tests/unit/display/test_entry_keys.py::TestEntryKeys::test_the_helper_answers_the_key_tuple`, `tests/unit/display/test_entry_keys.py::TestStatementChildren::test_statement_children_drop_the_key_fields` and `tests/tooling/test_entry_key_spellings.py::TestEntryKeysComeFromTheTree::test_no_module_keeps_its_own_key`.

## Precedent

- `junoscfg.display.detect_format` — the one content classifier; each caller
  supplies the formats its public contract permits it to infer.
- `junoscfg.display.xml_to_dict` — the one XML walker; XML-to-YAML serialization
  and conversion input consume the same JSON-equivalent mapping.
- `junoscfg.display.load_schema_tree` — the lazy-cached accessor every artifact read copies.
