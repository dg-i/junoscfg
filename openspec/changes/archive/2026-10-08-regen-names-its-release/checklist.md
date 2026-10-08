- minimise the exported surface from observed usage: nothing in `src/`
  changes; two functions and one exception in `tests/conftest.py`, imported
  by one test module.
- the deprecation policy, stated: not engaged; no named surface moves. A
  developer who relied on the newest dump being picked now names it with
  `JUNOSCFG_XSD_SOURCE`, which the error tells them, and a run stops with
  exit code 7, documented in the help text and the private README.
