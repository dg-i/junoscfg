- minimise the exported surface from observed usage: the `artifacts` return
  value loses a key that existed for one version and never worked.
- the deprecation policy, stated: not engaged. The key was introduced in v0.6.4
  and is removed before any release depended on it; `validate_xml` behaves
  exactly as it did before v0.6.4, which is to raise when no cleaned XSD is
  supplied.
