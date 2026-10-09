## Why

The README only documents installation from PyPI, so contributors working from
a checked-out repository do not have an installation command at hand.

## What Changes

- Add `pip install .` as the checked-out-repository installation example beside
  the existing PyPI command in the README Installation section.
- Keep the published-package installation command unchanged.

## Capabilities

No capability requirements change; this is documentation for an existing
development workflow, so the change skips delta specs.

## Non-goals

- Changing package metadata, dependencies, or runtime behavior.
- Documenting contributor setup beyond installing the checked-out package.

## Impact

Only `README.md` and the change-workflow artifacts are affected. No API or CLI
surface changes, and no dependency is added.
