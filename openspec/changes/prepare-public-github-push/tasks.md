## 1. Tests

- [x] 1.1 Confirm that no runtime acceptance or contract test is required for
  repository links and a documentation-only path move.

## 2. Implementation

- [x] 2.1 Link the documented production consumer to its public GitHub repository.
- [x] 2.2 Correct the MkDocs repository URL.
- [x] 2.3 Move the public simplification roadmap to `docs/roadmaps/` and update
  its navigation exclusion.
- [x] 2.4 Run `uv run --locked --group dev --with griffe --with tach --with
  towncrier --with vulture agent-ready check --set full` at
  `dbffde1d39dcbb9a907680fa6238716574cf22d5`; all checks passed, with 1,607
  tests passed and 72 skipped.
- [x] 2.5 Correct the roadmap's provenance pointer after the fresh review found
  that archiving had moved its source proposal.

## 3. Review and evidence

- [x] 3.1 Complete the fresh-session review and write `review.md`.
- [x] 3.2 Capture `metrics.md` and `metrics.json` for the immutable base and code head.
