- minimise the exported surface from observed usage: nothing is added or
  exposed; `_is_structural_key` is private to the validator.
- the deprecation policy, stated: a break on `api` and `cli`, declared with
  its migration and no deprecation period, because what changes is that a
  silent loss of configuration becomes a reported one. `--no-field-validate`
  and `validate=False` keep the old silence for anyone who wants it.
