## 1. Tests

- [x] 1.1 The shipped grammar rejects `set system host-name (foo bar)` and
  `set interfaces ge-0/0/0 description (not a policy expression)`.
- [x] 1.2 The shipped grammar still accepts the policy-algebra line, and still
  rejects the three malformed commands `test_set_corpus.py` records.
- [x] 1.3 A generated grammar gives `ALGEBRA_OR_VALUE` only to a node typed
  `policy-algebra`; the same leaf typed `xsd:string` rejects the expression.
- [x] 1.4 All five seen to fail with `_value_token` flattened and `EXPRESSION`
  put back in `QUOTED_OR_VALUE`; tree restored and the suite green again.

## 2. Implementation

- [x] 2.1 `_POLICY_ALGEBRA_TYPE` and `_value_token` in `grammar_generator.py`.
- [x] 2.2 `_child_reference` uses it in its flat, nokeyword-leaf and keyword-leaf
  value slots.
- [x] 2.3 Emit `QUOTED_OR_VALUE: QUOTED | VALUE` and
  `ALGEBRA_OR_VALUE: QUOTED | EXPRESSION | VALUE`.
- [x] 2.4 `read_structure_tree`'s docstring names `type_ref` among what the
  generator reads, because it now does.
- [x] 2.5 Regenerate the bundled `junos-set.lark`.
- [x] 2.6 One session-scoped `bundled_set_validator` fixture in `conftest.py`,
  so the corpus tier and the new negative tests share one four-second compile.

## 3. Verification

- [x] 3.1 Expression-capable slots 11,853 → 159; 93 of 4,385 rules changed.
- [x] 3.2 Three real device configurations, 7,097 set lines: 21 rejected
  before, 21 after. No line changed verdict.
- [x] 3.3 `tests/data/set_corpus.txt`: 106 of 116 accepted before and after,
  the ten recorded rejections unchanged.
- [x] 3.4 Grammar load 4.09s → 4.24s.
- [x] 3.5 `uv run pytest tests/ -q`, `pre-commit run --all-files`,
  `agent-ready check`.
