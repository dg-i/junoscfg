# junoscfg.validate — contract

Interface: `__all__` in `__init__.py`, module entry and expose list in `tach.toml`.

## Not for

Two pipelines share this directory: the build-time XSD pipeline and the runtime
validators. They are separate domains in `pyproject.toml`; do not let a runtime
validator import an `xsd_*` module.

## Invariants

- Schema corrections live in `xsd_fixes.py` as Python, never edited into the
  generated artifacts, so they survive regeneration — enforced by
  `tests/unit/validate/test_xsd_fixes.py::TestFixRegistry::test_all_fixes_have_metadata`.
- `ArtifactBuilder` and `JunosValidator` resolve lazily through `__getattr__`:
  importing this package must not pull lxml or the schema artifacts.
- A JSON-schema message names the path and keys, never a value — enforced by
  `tests/unit/validate/test_json_yaml_validator.py::TestAMessageNamesThePathAndTheKeys::test_no_message_reprints_a_value`.
- Any `maxOccurs` other than 1 makes a list, however the dump bounds it
  — enforced by `tests/unit/validate/test_xsd_parser.py::TestCardinality::test_a_numeric_max_occurs_is_list` and `tests/unit/validate/test_xsd_parser.py::TestCardinality::test_unbounded_is_list`.

## Precedent

- `junoscfg.validate.xsd_fixes` — one `XsdFix` per correction, applied to the one
  tree every artifact comes from; a rename keeps the XML/JSON name (`x`).
- `junoscfg.input.find_unsupported_set_brackets` — the lower-layer lexical
  boundary set validation reports through normal `ValidationError` results;
  `junoscfg.display.meta_target` judges a verb line from the tree beside the grammar.
