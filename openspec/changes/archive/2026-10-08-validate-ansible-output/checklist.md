- minimise the exported surface from observed usage: unchanged. `_collect_rules`,
  `_child_reference` and `_strip_apply_groups` are private; `_child_reference`
  gains a keyword-only `spliced` argument with a default, so no caller moves.
- the deprecation policy, stated: not engaged. No public name or signature
  changes. Validation accepts configuration it used to reject, which no caller
  could have depended on.
