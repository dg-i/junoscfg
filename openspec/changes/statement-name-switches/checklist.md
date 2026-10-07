- minimise the exported surface from observed usage: unchanged.
  `_is_statement_name` is private and `set_to_dict` keeps its signature.
- the deprecation policy, stated: not engaged on a named surface, but this does
  change `convert -e json` and `-e yaml` output for any configuration carrying
  `disable`. The previous output named a statement no device accepts, so a
  caller depending on it was depending on a defect.
