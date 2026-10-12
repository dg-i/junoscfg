# Tooling performance preservation evidence

Matched runs used Python 3.13.15, pytest 9.0.2, pytest-cov 7.1.0 and the same installed lock dependencies in this isolated worktree.
Command: `uv run --locked --group dev pytest tests/tooling --cov=junoscfg --cov-branch --cov-fail-under=0 --cov-report= --junitxml=<report> --durations=15`.

| Run | Outcome | Time |
|---|---|---|
| Before | 192 passed | 102.62s |
| After | 193 passed | 83.10s |

This is 19.52s (19.0%) less tooling elapsed time; single matched runs, not a full-suite claim.
JUnit comparison: every original classname/name and outcome preserved; only the isolated-input/no-success-evidence test was added.
Raw logs and XML: `/tmp/tooling-before.log`, `/tmp/tooling-before.xml`, `/tmp/tooling-after.log`, `/tmp/tooling-after.xml` (local diagnostic artefacts).
Both focused runs reported the existing coverage module-not-measured warning; final full-suite coverage remains a separate required gate.

A representative profile found runtime preparation 0.70s and fresh runtime verification 0.44s. The change shares only immutable bytes from real prepare_runtime; each test still creates and commits its own Git repository. Every runtime comparison, child pytest session, candidate snapshot, output report and generation invocation stays fresh. Mutable dictionaries and files are never shared. The new test corrupts one copy, verifies another, and confirms both repositories contain only the prepared runtime input in .agent-ready, no successful execution records.

A four-run synthetic child startup probe measured plugin autoload at 0.128s enabled and 0.119s disabled; no plugin configuration was changed because the saving was negligible.

Next: independent maintenance review and parent-coordinated canonical full checkpoint on the integrated candidate. No runtime behavior, dependencies, collection obligations or production verification policy changed.
