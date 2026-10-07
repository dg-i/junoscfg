- minimise the exported surface from observed usage: unchanged. No public name
  is added; the artifacts dict gains one key, and that dict is a return value
  rather than a declared surface.
- the deprecation policy, stated: not engaged. Nothing is removed and no
  behaviour a caller relied on changes — `schema generate` writes one more file
  into a directory the caller names, and `validate_xml` raises in exactly the
  cases it raised before.
