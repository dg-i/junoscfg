## Terms

<!-- agent-ready:retires:begin -->
<!-- agent-ready:retires:end -->

No vocabulary is retired.

## Symbols

No symbol is removed. `read_structure_tree` is added public in
`junoscfg.validate.artifact_builder`; `_deserialize_node` and
`_BOOL_FLAG_KEYS` are private.

## Dependencies

No dependency is added or released by this change.

## Requirements

No requirement is retired; this change sets `skip_specs: true`.

## Tests and fixtures

No test is retired. `TestBundledGrammarCompiles` loses its `xfail` and
`TestUnknownTokensInsideANamedList` loses its own, both by passing.
`TestListEntryTakesSiblingsOnOneLine` gains one, recording the rejection the
one-continuation rule buys. Twelve test functions are added across
`test_artifact_builder.py`, `test_grammar_generator.py` and the new
`test_set_corpus.py`, which also brings `tests/data/set_corpus.txt`.

## Docs

`docs/guide/validation.md` replaces its "not working" notice with the
limitations that remain. `docs/architecture/schema-internals.md` gains the
rebuild command and what the structure tree cannot carry.
