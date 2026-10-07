- minimise the exported surface from observed usage: unchanged.
  `_safe_rule_name` and `_RESERVED_RULE_NAMES` are private and appear in no
  `__all__` or expose list.
- the deprecation policy, stated: not engaged. No public name or signature
  changes. Generated grammars change — rule names become lowercase and a
  `start` element is renamed — but a grammar that does not compile had no
  behaviour anyone could depend on.
