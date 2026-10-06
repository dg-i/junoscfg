- minimise the exported surface from observed usage: unchanged. No name is
  added or removed; `requires-python` widens, which admits callers rather than
  excluding them.
- the deprecation policy, stated: not engaged. Widening a supported range is
  backwards compatible, so no surface break is declared and no deprecation is
  owed. Anonymizer output does change on 3.10 to 3.12 — but 0.6.0 refuses to
  install there, so no caller on those versions can observe the old behaviour.
