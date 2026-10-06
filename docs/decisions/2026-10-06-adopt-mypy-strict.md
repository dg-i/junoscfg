---
status: accepted
scope: ["src/**", "tool.mypy", ".pre-commit-config.yaml"]
enforced-by: ci
review-by: 2027-04-06
---

# Adopt mypy strict behind a CI report, not a commit hook

## Context

`[tool.mypy] strict = true` has been configured since before this onboarding
and `src/junoscfg/py.typed` ships, so the package advertises itself as fully
typed. mypy was in no dependency group and ran nowhere, so nothing had ever
checked that claim. Onboarding phase 2 installed it and measured the gap:
**102 errors across 25 of 68 files**, concentrated in `validate/validator.py`
(25), `edityaml/ansibilize.py` (12) and `convert/input/set_input.py` (9).

The template ships mypy as a blocking pre-commit hook. That would fail every
commit from the first one. `agent-ready` cannot help: its warn-mode baselines
are restricted to `caps`, `interfaces`, `specs` and `reconcile`, so there is no
mechanism to record 102 errors as declared debt the way the `caps` gate records
`AGENTS.md`.

## Decision

mypy stays out of `.pre-commit-config.yaml` and runs in CI as a reported step
that does not fail the build. The deadline is this record's `review-by`, which
`agent-ready decisions` fails once it passes — so the debt expires even though
no gate can hold it.

The `py.typed` marker stays. Removing it would be the honest alternative to
fixing the errors, but the Ansible collection imports four names from this
package and a typed package is the more useful promise to keep.

## Evidence it matters

The first change through the workflow removed `junoscfg schema makedoc`, dead
since the initial public release because it imported a module that never
existed. mypy names that import at the merge base
(`cli.py:727: Cannot find implementation or library stub for module named
"junoscfg.validate.schema_doc"`). The defect survived seven patch releases
because mypy was installed nowhere, not because it was undetectable. That is
the strongest argument for ending this record early rather than renewing it.

## Consequences

- A new type error cannot be caught at commit time until the backlog is clear;
  CI reports it and a reviewer has to read the step.
- The cleanup is a change of its own, and it is large enough to split by
  module. `validate/validator.py` alone is a quarter of it.
- When the count reaches zero, mypy moves into the hook and this record is
  superseded rather than renewed.
