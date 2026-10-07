- minimise the exported surface from observed usage: `AnonymizeConfig` gains one
  declared field, which is a narrowing rather than a widening — the attribute
  was already being set and read, just invisibly.
- the deprecation policy, stated: not engaged for a name, but a Python caller
  passing `networks=["auto"]` without `source_text` now gets a `ValueError`
  where it previously got silence. That is deliberate: the old behaviour
  returned a configuration the caller believed was anonymized and was not, in
  the red zone. An error is the safe direction and no migration exists for
  "you were getting nothing".
