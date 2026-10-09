## Why

Contributors rely on `ARCHITECTURE.md` to understand repository trade-offs and
layering, but its embedded size, line-count, and import-edge measurements no
longer describe the checked-in tree or lack reproducible evidence.

## What Changes

- Replace transient measurements with durable architectural facts and the
  commands or checks that enforce them.
- Keep the existing cost ranking, generated-artifact policy, and dependency
  direction unchanged.

## Capabilities

No product capability changes; this corrects contributor documentation and
therefore skips delta specs.

## Non-goals

- Changing runtime behavior, package contents, dependencies, or named surfaces.
- Recomputing an import-edge figure whose original measurement is not recorded.

## Impact

The reader is a contributor deciding where code belongs. `ARCHITECTURE.md` is
the documentation home; the committed compressed artifacts, fresh code map,
source tree, and `tach check` are authoritative. Only that document and this
change record are affected.
