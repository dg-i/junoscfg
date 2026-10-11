## 1. Change

- [x] 1.1 `pyproject.toml`: serialized-paths, the `schema` expensive tier, the assurance record
- [x] 1.2 `mkdocs.yml` nav and the how-to's three pointers to `pyproject.toml`

## 2. Verification

- [x] 2.1 `tomllib` reads the batch and assurance tables with the values in the proposal
- [x] 2.2 `uv run --locked --group docs mkdocs build --strict` exits 0 and no longer lists the how-to as outside the nav
- [x] 2.3 One full checkpoint passes

## 3. Review and metrics

- [x] 3.1 Review omission recorded in `review.md` (economy, normal floor)
- [x] 3.2 Metrics captured

## Evidence

- 2.1 `tomllib`: batch `max-builders` 3, four serialized paths, tier `schema` (five paths, the `--schema` command); assurance record `docs/how-to/run-a-batch-of-changes.md#assurance`, values `economy`, `zones` empty.
- 2.2 `mkdocs build --strict` exit 0; "not in nav" lists only the pre-existing `how-to/hosting.md`.
- 2.3 full checkpoint at 8f9879e: 7,558 passed, 45 skipped, 18 xfailed; "every check passed" (187 s).
