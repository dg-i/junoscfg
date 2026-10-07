- minimise the exported surface from observed usage: unchanged. `_IP_ANY_TYPES`
  and the new `_IP_OR_NAME_TYPES` are private module constants; no signature
  changes.
- the deprecation policy, stated: not engaged. Field validation accepts values
  it used to warn on. `--strict` turns these into failures, so a caller running
  strict against a real configuration gets fewer errors, never more.
