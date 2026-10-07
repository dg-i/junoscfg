- minimise the exported surface from observed usage: nothing is exported.
  `tests/jvd_data.py` is test-only and appears in no `__all__`.
- the deprecation policy, stated: not engaged. No runtime code changes, and the
  new tier is opt-in behind `--jvd`, so no existing command behaves differently.
