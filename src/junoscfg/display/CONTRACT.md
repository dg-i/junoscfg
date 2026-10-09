# junoscfg.display — contract

Interface: `__all__` in `__init__.py`, module entry and expose list in `tach.toml`.

## Not for

Display rendering only in name. It is the shared kernel: six of the eight
packages import from it, and `constants.py` and `config_store.py` are a schema
flag table and a tree structure, not display logic.

## Invariants

- Nothing here imports from a higher layer; `display` and `input` are the
  bottom of the DAG — enforced by `tach check`.
- Importing this package pulls in neither lxml nor the schema artifacts:
  `load_schema_tree()` is lazy and cached, and the XML path imports lxml on
  first use — enforced by
  `tests/test_to_yaml.py::TestLazyXmlImport::test_to_yaml_module_level_has_no_lxml`.

## Precedent

- `junoscfg.display.detect_format` — the one content classifier; each caller
  supplies the formats its public contract permits it to infer.
- `junoscfg.display.xml_to_dict` — the one XML walker; XML-to-YAML serialization
  and conversion input consume the same JSON-equivalent mapping.
- `junoscfg.display.constants.load_schema_tree` — the lazy-cached accessor
  pattern every artifact read should copy.
