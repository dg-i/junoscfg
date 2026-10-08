- minimise the exported surface from observed usage: nothing is added or
  exposed; `open_artifact_write` keeps its signature and its callers.
- the deprecation policy, stated: not engaged. The compressed artifacts a
  user generated before this still load; only the header's timestamp field
  changes in what is written from now on.
