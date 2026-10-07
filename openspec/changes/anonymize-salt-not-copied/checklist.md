- minimise the exported surface from observed usage: unchanged. `_pseudo_salt`
  is private and nothing is added to any `__all__` or expose list.
- the deprecation policy, stated: not engaged. The declared surfaces are `api`
  and `cli`; no name changes and no signature changes. Anonymizer output does
  change for every hashed password. That is a patch and not a break because
  `src/junoscfg/anonymize/CONTRACT.md` words its determinism invariant
  per-run — "the same input and the same salt produce the same output, every
  run" — and never promised stability across versions. The production consumer
  named in the stage note uses convert, validate and edityaml, not anonymize.
