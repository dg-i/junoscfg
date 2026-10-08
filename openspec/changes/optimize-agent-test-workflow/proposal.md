## Why

The completed expected-failures review exposed duplicated full-suite work,
misleading test-tier guidance, a collision-prone randomness assertion, stale
generated policy, and a local base that measures 115 unrelated commits.

## What Changes

- Make exact nodes or affected files the implementation loop, with one full
  pre-review checkpoint and a conditional final full checkpoint.
- Record measured fast/full costs and grammar-specific focused tests.
- Let the Python matrix own complete application-suite coverage while the
  governance job runs the non-application-test check set after that matrix.
- Control blank-salt randomness at `secrets.token_hex`, its owning boundary.
- Refresh generated CODEOWNERS and stage levers through supported renderers.
- Make local checks compare with local `master`; CI keeps passing the pull
  request target explicitly. Search: `rg` found the fallback only in
  `[tool.template]`, agent guidance, CI's explicit `--base`, and archived data.

## Capabilities

No product capability changes; `skip_specs: true` records that this is a
workflow, CI, generated-policy, and test refactor.

## Non-goals

- No generic agent-ready template or checks-package changes.
- No weakened application coverage, ref rewriting, remote push, or runtime API/CLI change.

## Impact

Repository guidance, CI wiring, generated policy, one anonymization test, and
the patch version change. Baseline timings come from the two documented pytest
commands on this checkout: 43.80s fast versus 43.77s full wall time.
