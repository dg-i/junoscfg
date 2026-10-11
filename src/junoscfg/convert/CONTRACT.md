# junoscfg.convert — contract

Interface: `__all__` in `__init__.py`, module entry and expose list in `tach.toml`.

## Not for

Not a format-to-format shortcut: every conversion goes through the dict IR; a
second path for a pair is the duplicate `ARCHITECTURE.md` calls a defect.

## Invariants

- Every supported pair round-trips through the IR without losing content —
  enforced by `tests/contract/test_format_matrix.py::TestEveryWriterKeepsTheIr::test_the_output_reads_back_as_the_ir`.
- XML input reuses the display kernel's `xml_to_dict()` walker; YAML and XML apply
  schema-backed leaf-list normalization at the common boundary, while JSON keeps its
  supplied value shapes — enforced by `tests/unit/convert/test_convert_api.py::TestLeafListPromotion`.
- No writer changes the IR it is given; the JSON writer normalizes its own copy — enforced by
  `tests/unit/convert/test_convert_roundtrip.py::TestNoWriterChangesTheIrItIsGiven::test_a_hand_built_ir_is_left_unchanged`.
- One configuration yields one IR whatever format it arrived in — enforced by `tests/contract/test_format_matrix.py::TestEveryReaderGivesTheShapeIr`.
- An incomplete set statement or leaf, a keyed entry without its key from JSON,
  YAML or XML, and a meta command on a partial or surplus key are kept whole and
  reported `UNPLACED`; set input keeps one, as its tokens, in its level's
  `junoscfg:unplaced` record, never at a placed node's key — enforced by
  `tests/unit/convert/test_set_input.py::TestAKeptStatementHasARecordOfItsOwn::test_a_bare_keyword_never_meets_its_placed_node`, `tests/unit/convert/test_field_validator.py::TestAnIncompleteStatementIsUnplaced::test_each_door_reports_it`, `tests/unit/convert/test_field_validator.py::TestAnEntryWithoutItsKeyIsUnplaced::test_each_structured_door_reports_it` and `tests/unit/convert/test_set_input.py::TestAMetaCommandIsNeverPartiallyApplied::test_a_partial_or_surplus_key_is_kept_whole`.

## Precedent

- `junoscfg.convert.pipeline_result` — the implementation door for conversion; string-only `pipeline()` delegates to it and discards diagnostics.
- `junoscfg.convert.output.dict_walker.WalkOutput` — the strategy every new output format implements instead of walking the IR again.
- `junoscfg.input.find_unsupported_set_brackets` — the lower-layer lexical boundary raw set readers apply before constructing the IR.
