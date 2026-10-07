## Why

`requires-python` is `>=3.10` and the classifiers declare 3.10 through 3.14,
but CI is a single `ubuntu-latest` job on one interpreter. Nothing exercises
3.10, 3.11, 3.12 or 3.13 ever again.

That is exactly the drift that produced the `crypt` defect: the floor said 3.10,
reality was 3.13-only, and the gap survived seven patch releases until a manual
measurement found it. A declared range nothing tests is a guess.

## What Changes

- A `versions` job derives the matrix from `pyproject.toml` itself — the
  `Programming Language :: Python :: 3.x` classifiers, cross-checked against the
  `requires-python` floor — and emits it as JSON. Adding 3.15 means adding the
  classifier you would add anyway; no workflow edit.
- A `tests` job runs the suite on every derived version. It installs the package
  and pytest only, not the dev group, so it stays cheap: the suite is ~2 seconds.
- The existing `full` job keeps running `agent-ready check --set full` once, on
  one modern interpreter, because the check package itself needs 3.11+.
- A mismatch between the floor and the classifiers fails the `versions` job
  rather than silently testing the wrong set.

## Capabilities

### New Capabilities

No capability is added; this is test infrastructure for behaviour that already
exists.

### Modified Capabilities

No requirement changes, so `.openspec.yaml` sets `skip_specs: true`.

## Non-goals

- Running the gate set on every interpreter. `agent-ready-checks` requires
  3.11+ and the gates are interpreter-independent; running them five times
  would cost four times as much to learn nothing.
- Testing on Windows or macOS runners. The `crypt` defect was platform-specific
  and would have been caught by a macOS runner, but that is a separate decision
  about cost.

## Impact

`.github/workflows/ci.yml` only. No source, no dependencies, no version bump:
nothing a caller can observe changes.
