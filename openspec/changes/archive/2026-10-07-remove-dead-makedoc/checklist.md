- minimise the exported surface from observed usage: done — the command had no
  observed usage because it could not run; its removal shrinks the `cli`
  surface by one name and leaves `generate` and `info`, which both work.
- the deprecation policy, stated: the beta stage says a removal is deprecated
  first. Waived here with the reason recorded in `.openspec.yaml`: there is no
  behaviour to deprecate, since every invocation raised ModuleNotFoundError, and
  a deprecation warning on a command that cannot execute would reach nobody.
