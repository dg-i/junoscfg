- minimise the exported surface from observed usage: `AnonymizeConfig` gains one
  declared field, which is a narrowing rather than a widening — the attribute
  was already being set and read, just invisibly.
- the deprecation policy, stated: not engaged for a name, but a Python caller
  passing `networks=["auto"]` without `source_text` now gets a `ValueError`.
  Where `auto` was the only spec, they previously got silence; where it sat
  beside an explicit CIDR, they got the explicit half and silently lost the
  auto half. Both now fail loudly until the text is supplied, which is the safe
  direction in the red zone. The field is appended rather than inserted, so no
  positional parameter moves and `stage griffe` reports no api break.
