- minimise the exported surface from observed usage: nothing is added. Two
  private helpers and an early return leave `validate/set_validator.py`;
  `SetValidator` keeps its signature.
- the deprecation policy, stated: a break on `api` and `cli`, declared in
  `.openspec.yaml` with its migration and no deprecation period, because the
  old artifacts are defective and a user who needs them selects them with
  `JUNOSCFG_ARTIFACTS` or `--artifacts` exactly as before.
