- minimise the exported surface from observed usage: unchanged. `_rule_name_for`
  and `_LIST_RULE_SUFFIX` are private and appear in no `__all__` or expose list;
  `_RuleInfo.has_non_list` is removed, also private.
- the deprecation policy, stated: not engaged. No public name or signature
  changes. Generated grammars gain `__list` rules and lose required content
  after a container, but the shipped grammar does not compile, so no behaviour
  anyone could depend on changes.
