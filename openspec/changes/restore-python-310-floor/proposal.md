## Why

Onboarding phase 4 raised `requires-python` from `>=3.10` to `>=3.13`. Measured
afterwards, nothing in the package needed it:

- `datetime.UTC` (3.11+) in `validate/artifact_builder.py` was introduced by the
  onboarding itself, when raising ruff's target made UP017 fire.
- `agent-ready-checks` requires `>=3.11`, but it is a development tool and has
  no business setting the floor of the published package.
- The only real gap is six tests in `tests/test_anonymize/test_password_rule.py`.
  `_make_crypt_hash()` calls `crypt.crypt()`, which macOS answers with a
  13-character DES hash instead of the requested `$1$`/`$5$`/`$6$` format. From
  3.13 the module is gone and the deterministic fallback runs, so the floor made
  the tests pass by removing the broken branch from reach.

The cost lands downstream: `dg-i/ansible-collection-junos-config` declares
`requires-python = ">=3.10"`, so on 3.10 to 3.12 its users silently resolve to
an old junoscfg instead of seeing an error.

## What Changes

- Restore `requires-python = ">=3.10"`; classifiers, ruff target and mypy config
  follow. Widening is backwards compatible, so no surface break is declared.
- Delete the `crypt` branch in `_make_crypt_hash()`. The deterministic fallback
  becomes the only path, so output is identical on every platform and
  interpreter — which is what an anonymizer owes its caller. 3.13+ already
  behaves this way; this makes 3.10 to 3.12 agree with it instead of diverging
  by libc.
- Revert `datetime.UTC` to `timezone.utc`.
- Scope `agent-ready-checks` to `python_version >= '3.11'` in the dev group.
- Drop the now-unneeded `[tool.deptry.per_rule_ignores] DEP001 = ["crypt"]`.

## Capabilities

### New Capabilities

None; this restores a supported range and removes a platform-dependent branch.

### Modified Capabilities

No capability changes, so `.openspec.yaml` sets `skip_specs: true`.

## Non-goals

- Producing a *real* crypt hash. The fallback keeps the prefix, the salt and the
  crypt64 charset, which is what the tests require and what 3.13+ already ships.
- Raising the collection's own floor. That becomes unnecessary once this lands.

## Impact

`src/junoscfg/anonymize/rules/password.py` (red zone),
`src/junoscfg/validate/artifact_builder.py`, `pyproject.toml`,
`.copier-answers.yml`, `uv.lock`. Anonymizer output on 3.10 to 3.12 changes to
match 3.13+; no caller on those versions can be running 0.6.0 today, since it
refuses to install there.
