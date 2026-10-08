- minimise the exported surface from observed usage: `junoscfg.display` gains
  `artifacts_dir` and `resolve_artifacts_dir`, both reached across modules and
  so added to `__all__` and to `tach.toml`'s expose list, which
  `agent-ready interfaces` holds in step. `set_artifacts_dir` was written and
  withdrawn before commit; a setter with no reset leaks.
- the deprecation policy, stated: not engaged on a named surface. Conversion
  starts honouring two knobs it previously ignored, which can change behaviour
  for anyone who had `JUNOSCFG_ARTIFACTS` set and did not expect it to apply —
  but it was set to be honoured, and validation already did.
