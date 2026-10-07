- minimise the exported surface from observed usage: nothing is exported.
  `tests/schema_data.py` is test-only and in no `__all__`; `promote_staged`
  gains an optional keyword, so existing callers are unaffected.
- the deprecation policy, stated: not engaged. No runtime code changes. A dump
  already promoted keeps its name; only newly staged ones gain the suffix.
