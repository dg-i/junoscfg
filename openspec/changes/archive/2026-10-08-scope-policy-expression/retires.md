## Terms

<!-- agent-ready:retires:begin -->
<!-- agent-ready:retires:end -->

No vocabulary is retired. `EXPRESSION` keeps its name and its regex; only the
terminal that offers it changes.

## Symbols

Added: `_value_token` and `_POLICY_ALGEBRA_TYPE` in
`junoscfg.validate.grammar_generator`, both private. Added:
`bundled_set_validator`, a session-scoped fixture in `tests/conftest.py`.
No symbol is removed.

## Dependencies

No dependency is added or released by this change.

## Requirements

No requirement is retired; this change sets `skip_specs: true`.

## Tests and fixtures

No test is retired. `TestPolicyExpressionIsOneValue._tree` grows a `typed`
parameter, keeping both of its assertions and adding one.
`TestExpressionsAreScopedToPolicyAlgebra` and
`TestTheShippedGrammarKeepsRejecting` are new, seven assertions between them,
five of which fail without the fix. `tests/test_set_corpus.py`'s module-scoped
validator fixture now delegates to the session-scoped one, which removes a
duplicate four-second grammar compile.

## Docs

None. No document described `EXPRESSION`'s reach; the generator's own comment
did, and it is corrected in place.
