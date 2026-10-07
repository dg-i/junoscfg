- minimise the exported surface from observed usage: unchanged. `xml_to_yaml`
  keeps its signature; it raises `ValueError` where it previously let an lxml
  exception through, which is what the other input paths already do.
- the deprecation policy, stated: not engaged. A caller catching
  `XMLSyntaxError` from `xml_to_yaml` would now see `ValueError`, but the
  exception was undocumented and the CLI never caught it — it printed a
  traceback.
