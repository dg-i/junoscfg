- minimise the exported surface from observed usage: unchanged. `_pseudo_salt`
  is private and nothing is added to any `__all__` or expose list.
- the deprecation policy, stated: not engaged. The declared surfaces are `api`
  and `cli`; no name changes and no signature changes. Anonymizer output does
  change for every `$1$`/`$5$`/`$6$` password, which is a bug fix in the red
  zone rather than a surface break — the old output leaked a correlation handle.
