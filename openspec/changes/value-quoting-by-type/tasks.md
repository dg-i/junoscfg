## 1. Verification

- [x] 1.1 Acceptance tests (fail on the merge base `50b0a10` by design, pins named in `evidence-freeze.md`): `tests/unit/display/test_value_format.py::TestAValueIsSpelledByItsLeaf`; catalogue rows in `tests/support/shapes.py` (`a-one-term-policy-expression`, `a-quoted-policy-name-that-reads-as-an-expression`, `a-quoted-plain-policy-name` (pin), `a-value-holding-an-escaped-quote`, `an-expression-in-a-description`, and the lexing rows `an-escaped-quote-in-a-one-line-block`, `an-escaped-quote-beside-comments`, `an-escaped-quote-in-a-template`, `an-escaped-quote-in-prose`, `address-forms-inside-words-beside-an-escaped-quote`) through `tests/contract/test_format_matrix.py`; `tests/unit/display/test_set_converter.py::TestMalformedTextIsRefused::test_it_raises[a-statement-across-lines-holding-an-escaped-quote]` (pin); `tests/unit/validate/test_grammar_generator.py::TestAnyLeafValueMayBeQuoted`; `tests/corpus/test_shipped_artifacts.py::TestTheShippedGrammarKeepsRejecting` rows; the strict xfail on `tests/unit/anonymize/test_integration.py::TestKeyedEntriesSurvive::test_the_mapping_restores_the_set_output` removed.
- [ ] 1.2 Independent Test/Challenge on these tests (high risk floor): `test-challenge.md`.

## 2. Change

- [ ] 2.1 `display/value_format.py`: `format_value(value, node=None)` writes a `policy-algebra` token as it is, quotes any other value where it must be and escapes `"`; `policy_expression()` goes.
- [ ] 2.2 `convert/output/dict_walker.py`: every call passes the leaf's schema node.
- [ ] 2.3 `convert/input/set_input.py`: a quoted `policy-algebra` value whose text starts with `(` keeps its quotes.
- [ ] 2.4 `validate/grammar_generator.py`: `QUOTED` takes `\"`; schema tier regenerates `validate/data/`; `tools/device_grammar_corpus.py` and `tools/device_differences.py` rebuild their records.
- [ ] 2.5 Changelog fragment, docs; before/after comparison over every capture.

## 3. Review and evidence

- [ ] 3.1 Complete the risk-required fresh isolated review, or record why the assurance policy does not require it.
- [ ] 3.2 Capture `metrics.md` and `metrics.json` for the immutable base and code head.
- [ ] 3.3 Finalizer completes bounded spec application, evidence, and archive housekeeping without product edits.
