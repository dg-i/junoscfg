- minimise the exported surface from observed usage: unchanged. `_value_token`
  is private, `generate_lark_grammar` and `write_lark_grammar` keep their
  signatures, and no name enters `__all__`.
- the deprecation policy, stated: not engaged. The bundled grammar is a
  generated artefact, not a named surface, and this restores what `api` and
  `cli` promised rather than changing it — a validator that accepted
  `set system host-name (foo bar)` was not keeping the promise.
