## 1. Change

- [ ] 1.1 Scaffold the decision record with `agent-ready scaffold decision` and write it (JVD tier out of the instructions and per-change verification, kept as an opt-in manual tool; owner 2026-10-11; cost)
- [ ] 1.2 Write `docs/how-to/run-a-batch-of-changes.md` (rules 1–8, checks 1–6 with source and command, `--schema` tier, worktrees, versioning, lessons, ledger, assurance)
- [ ] 1.3 `AGENTS.md`: link the page from Verification and "Where things are", within 100 lines
- [ ] 1.4 `docs/architecture/developer-guide.md` Testing Architecture and `docs/how-to/solo-review.md`: JVD out of per-change evidence, oracle checks in
- [ ] 1.5 Write `template-follow-ups.md`

## 2. Verification (one per docs-plan QA item)

- [ ] 2.1 Links and anchors: `uv run --locked --group docs mkdocs build --strict` exits 0; the only notice about the new page is that it is not in the nav
- [ ] 2.2 Commands: run every command in the how-to at the checked head; record each result here (the oracle-check node lists collect and pass; the output loop writes 192 outputs; `--schema`/`--regen-schema` run once if a dump is present, otherwise recorded as not run)
- [ ] 2.3 Referenced paths: every path and test node in the changed files exists (`ls`, `uv run --locked pytest --collect-only -q <nodes>`)
- [ ] 2.4 Terminology: `grep -n -i jvd` over the changed files shows the tier only as opt-in or history; terms match `batches.md`
- [ ] 2.5 Placement: the page holds steps and commands; rationale only in the decision record (inspection)
- [ ] 2.6 Rendered output: markdownlint on changed files passes (pre-commit); `agent-ready caps` passes; `wc -l AGENTS.md` ≤ 100
- [ ] 2.7 One full checkpoint: `uv run --locked --group dev --with griffe --with tach --with towncrier --with vulture agent-ready check --set full` passes

## 3. Review and metrics

- [ ] 3.1 Fresh isolated Reviewer report in `review.md`; accepted fixes applied and re-confirmed
- [ ] 3.2 Metrics captured in `metrics.md` and `metrics.json`
