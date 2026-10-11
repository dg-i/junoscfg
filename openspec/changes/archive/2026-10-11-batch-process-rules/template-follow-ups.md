# Template follow-ups

Upstream-owned rules this batch could not set locally. Template v0.9.0 (checks 0.15.11) is
installed and is the latest release, so there was no refresh to run. Report each one upstream.

| ID | Rule | Gap in v0.9.0 | Local stand-in |
|---|---|---|---|
| TF1 | A docs change that adds a page also adds it to the site navigation | The docs lane refuses `mkdocs.yml` (non-document suffix), so the nav entry needs a second change | `batch-process-config` carries the nav entry |
| TF2 | Merge-time versioning: the version is bumped at merge in the archive commit, not by the Builder | `batches.md` says "choose the version from the current default branch at merge time" but the lane gate and phase files do not say which commit carries the bump | `docs/how-to/run-a-batch-of-changes.md`, Version and merge |
| TF3 | An expensive tier with several ordered steps (regenerate, regenerate again and expect no diff, then the schema tests) | `expensive-tiers` takes one `command` | the steps are written in the how-to; the tier's `command` names the schema tests |
| TF4 | Worktrees of a repository whose scratch directory is tracked (`private_test_data/` with its `.gitignore` and README) | `batches.md` gives no hook for linking untracked scratch into each worktree | the per-entry link loop in the how-to |
| TF5 | The maintenance lane (type `maintenance`) for non-behavioural configuration changes such as `[tool.template.batch]` | present in the upstream working tree, not released; 0.15.11 knows no `maintenance` type | `batch-process-config` is typed `refactor` |
