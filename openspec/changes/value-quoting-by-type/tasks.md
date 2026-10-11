## 1. Verification

- [x] 1.1 Acceptance tests (fail on the merge base `50b0a10` by design, pins named in `evidence-freeze.md`): `tests/unit/display/test_value_format.py::TestAValueIsSpelledByItsLeaf`; catalogue rows in `tests/support/shapes.py` (`a-one-term-policy-expression`, `a-quoted-policy-name-that-reads-as-an-expression`, `a-quoted-plain-policy-name` (pin), `a-value-holding-an-escaped-quote`, `an-expression-in-a-description`, and the lexing rows `an-escaped-quote-in-a-one-line-block`, `an-escaped-quote-beside-comments`, `an-escaped-quote-in-a-template`, `an-escaped-quote-in-prose`, `address-forms-inside-words-beside-an-escaped-quote`) through `tests/contract/test_format_matrix.py`; `tests/unit/display/test_set_converter.py::TestMalformedTextIsRefused::test_it_raises[a-statement-across-lines-holding-an-escaped-quote]` (pin); `tests/unit/validate/test_grammar_generator.py::TestAnyLeafValueMayBeQuoted`; `tests/corpus/test_shipped_artifacts.py::TestTheShippedGrammarKeepsRejecting` rows; the strict xfail on `tests/unit/anonymize/test_integration.py::TestKeyedEntriesSurvive::test_the_mapping_restores_the_set_output` removed.
- [x] 1.2 Independent Test/Challenge on these tests (high risk floor): `test-challenge.md`; findings F1-F10 and SC1-SC3 ruled by the orchestrator, all accepted and applied (chain rows, nodeless escaping, audit rendering, SC2/SC3 interim pins, P11/P13 strict xfails).

## 2. Change

- [x] 2.1 `display/value_format.py`: `format_value(value, node=None)` writes a `policy-algebra` token the reader keeps as written as it is, quotes any other value where it must be and always escapes `"`; `policy_expression()` goes.
- [x] 2.2 `convert/output/dict_walker.py`: every call passes the leaf's schema node.
- [x] 2.3 `convert/input/set_input.py`: a quoted `policy-algebra` value whose text starts with `(` keeps its quotes.
- [x] 2.4 `validate/grammar_generator.py`: `QUOTED` takes `\"` and keeps a trailing backslash (SC2); schema tier regenerates `validate/data/` (ef06855; second run byte-identical except `junos-schema-meta.json.gz`); `tools/device_grammar_corpus.py` (false rejections 66 -> 65) and `tools/device_differences.py` (928 -> 716 lines, four classes gone) rebuild their records.
- [x] 2.5 Changelog fragments (bugfix, removal), docs (`design-decisions.md` Value Quoting, `guide/audit.md`), `display/CONTRACT.md` invariant; before/after comparison over every capture: plain 36 of 96 conversions differ, anonymized 432 of 1,152 (the same 36 under each of 12 rule sets), every changed line a policy-algebra token (DEV-4/5/6) or an escaped quote (DEV-7), no diagnostic, field-validation or exception difference.

- [x] 2.6 Full checkpoint: `uv run --locked --group dev --with griffe --with tach --with towncrier --with vulture agent-ready check --set full` at `4fafc72`: every check passed; application tests 8,351 passed, 37 skipped, 20 xfailed.

## 3. Review and evidence

- [ ] 3.1 Complete the risk-required fresh isolated review, or record why the assurance policy does not require it.
- [ ] 3.2 Capture `metrics.md` and `metrics.json` for the immutable base and code head.
- [ ] 3.3 Finalizer completes bounded spec application, evidence, and archive housekeeping without product edits.
