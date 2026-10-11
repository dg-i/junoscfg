## 1. Change

- [x] 1.1 Scaffold the decision record with `agent-ready scaffold decision` and write it (JVD tier retired from the instructions and verification, its code removal the follow-up `retire-jvd-tier`; owner 2026-10-11; cost)
- [x] 1.2 Write `docs/how-to/run-a-batch-of-changes.md` (rules 1–8, checks 1–6 with source and command, `--schema` tier, worktrees, versioning, lessons, ledger, assurance)
- [x] 1.3 `AGENTS.md`: link the page from Verification and "Where things are", within 100 lines
- [x] 1.4 `docs/architecture/developer-guide.md` Testing Architecture and `docs/how-to/solo-review.md`: JVD out of per-change evidence, oracle checks in
- [x] 1.5 Write `template-follow-ups.md`

## 2. Verification (one per docs-plan QA item)

- [x] 2.1 Links and anchors: `uv run --locked --group docs mkdocs build --strict` exits 0; the only notice about the new page is that it is not in the nav
- [x] 2.2 Commands: run every command in the how-to at the checked head; record each result here (the oracle-check node lists collect and pass; the comparison template records and diffs base and head; `--schema`/`--regen-schema` run once if a dump is present, otherwise recorded as not run)
- [x] 2.3 Referenced paths: every path and test node in the changed files exists (`ls`, `uv run --locked pytest --collect-only -q <nodes>`)
- [x] 2.4 Terminology: `grep -n -i jvd` over the changed files shows the tier only as retired or history; terms match `batches.md`
- [x] 2.5 Placement: the page holds steps and commands; rationale only in the decision record (inspection)
- [x] 2.6 Rendered output: markdownlint on changed files passes (pre-commit); `agent-ready caps` passes; `wc -l AGENTS.md` ≤ 100
- [x] 2.7 One full checkpoint: `uv run --locked --group dev --with griffe --with tach --with towncrier --with vulture agent-ready check --set full` passes

## 3. Review and metrics

- [x] 3.1 Fresh isolated Reviewer report in `review.md`; accepted fixes applied and re-confirmed
- [ ] 3.2 Metrics captured in `metrics.md` and `metrics.json`

## Evidence

- 2.1 at db38a5e: `mkdocs build --strict` exit 0; INFO only: `how-to/run-a-batch-of-changes.md` (expected, nav in `batch-process-config`) and the pre-existing `how-to/hosting.md` not in nav. Reviewer re-ran it at 417e969 (confirmation pending in `review.md`).
- 2.2 the focused device-evidence command: 3,664 passed, 5 xfailed, 17.6 s (Builder at 29bbfe8) and 17.4 s (Reviewer at db38a5e); `compare-template.py record` 96 conversions in 3.4 s, `--anonymize` 1,152 in about 40 s, no exception, `diff` of a run against itself "0 of 96 conversions differ"; schema tier in a scratch worktree of db38a5e: first `--regen-schema` 272 s (7,555 passed, 45 skipped, 18 xfailed), second run likewise, `git diff --stat` shows only `junos-schema-meta.json.gz` (its `generated_at`), so the documented check now excludes it and prints nothing; `--schema tests/corpus/test_schema_data.py` over the three dumps under `private_test_data/schemas/`: 34 passed, 2 skipped in 2,021 s (about 11 minutes per dump).
- 2.3: 3,696 tests collected for every node the changed files name; every named path exists.
- 2.4: `grep -n -i jvd` over the changed files: the tier appears only as retired, as history, or as the follow-up `retire-jvd-tier`; "device-evidence checks" in every product document (review finding 12).
- 2.5: steps and commands in the how-to; rationale in the decision record (review finding 15 kept as recorded).
- 2.6: pre-commit markdownlint and document caps passed on every commit; `wc -l AGENTS.md` = 100.
- 2.7: full checkpoint at db38a5e: first run failed only `skills` (no `.claude/skills` mirror in a fresh worktree, untracked); after `agent-ready skills --regenerate`, "every check passed". Review fixes changed documents only, so no rerun.
