## Why

The non-blocking `mypy src tests` report has grown from the 102 errors recorded
by decision `2026-10-06-adopt-mypy-strict` to 374 errors in 63 of 143 files, so
it neither blocks regressions nor provides a maintainable debt-reduction signal.

## What Changes

- Replace that report with a blocking mypy command over the largest coherent,
  clean scope of stable public interfaces and caller-visible result/configuration
  models established by measurement during this change.
- Keep diagnostics for invalid calls, missing symbols/imports, incompatible
  returns and unsafe optional values; exclude tests and dynamic Junos-tree
  internals unless measurement shows they add useful, clean coverage.
- Add a policy check that rejects a non-blocking or known-failing whole-repository
  mypy invocation, supersede decision `2026-10-06-adopt-mypy-strict`, and align
  CI, toolbox documentation and configuration comments.

## Capabilities

No capability changes; `.openspec.yaml` sets `skip_specs: true`.

## Non-goals

- Statically modelling the Junos configuration tree or changing string-valued IR semantics.
- Changing conversion, validation, anonymization, audit, API or CLI behaviour.
- Clearing the repository-wide typing backlog or adding runtime dependencies.

## Impact

CI, `pyproject.toml`, policy tests and documentation only unless investigation
finds a small genuine interface defect; no named surface break or resource override.
