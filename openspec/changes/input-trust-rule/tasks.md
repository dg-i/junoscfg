## 1. Verification (one per docs-plan QA item)

- [x] 1.1 Links: `uv run --locked --group docs mkdocs build --strict` gives no new warning
- [x] 1.2 Referenced paths and decision slugs exist: `ls` on every path the changed text names
- [x] 1.3 Caps: `ARCHITECTURE.md` at or under 200 lines
- [x] 1.4 Terminology: `git grep -n "not hostile" -- ':!openspec/changes' ':!docs/reviews'` lists only C2/C3 places and pointers to the rule
- [x] 1.5 Rendered output: markdownlint passes on every changed document

## 2. Change

- [x] 2.1 `ARCHITECTURE.md` section 8 rule and yaml-new pointer
- [x] 2.2 Decision record and rendered index
- [x] 2.3 Pointers from the guide, API page, contracts and the 64-level record

## 3. Review and evidence

- [x] 3.1 Fresh isolated review recorded in `review.md`
- [x] 3.2 One full checkpoint passes: `uv run --locked --group dev --with griffe --with tach --with towncrier --with vulture agent-ready check --set full`
- [x] 3.3 Capture `metrics.md` and `metrics.json` for the immutable base and code head
- [ ] 3.4 Archive, patch bump, merge and tag without pushing

## Evidence

- 1.1 at f3a8913: `mkdocs build --strict` exits 1 with 49 warnings, every one a BACKLOG.md link; master 037e012 gives the same 49 (baseline run in a detached worktree), so no new warning. The new link in `docs/guide/conversion.md` resolves.
- 1.2 at f3a8913: `ls ARCHITECTURE.md changelog.d/+input-trust-rule.doc.md docs/api/input.md docs/decisions/2026-10-15-configuration-input-is-trusted.md docs/decisions/2026-10-15-yaml-nests-at-most-64-levels.md docs/decisions/index.md docs/guide/conversion.md src/junoscfg/convert/CONTRACT.md src/junoscfg/input.CONTRACT.md tests/contract/test_every_message.py docs/reviews/2026-10-15-trusted-input-retirement.md src/junoscfg/convert/output/json_output.py docs/BACKLOG.md` exits 0.
- 1.3: 200 lines; `agent-ready caps` passes.
- 1.4: four hits: the 64-level record (now citing the rule), the main spec (C3), `src/junoscfg/input.py` and `tests/unit/input/test_input.py` docstrings (C2).
- 1.5: `pre-commit run markdownlint` on the eight changed documents passes.
- 3.1: Reviewer verdict Merge at c542bc0 (`review.md`).
- 3.2 at 433bf4d: canonical command, "every check passed", 337 s (schema-25.2 tiers selected by the two `src/junoscfg/**/CONTRACT.md` edits, after `tools.schema_verification prepare` with physical dumps). Earlier attempts stopped before any test: branch unassessed in the shared activation (assessed on master 1afcd29, `readiness --activate`), verification metadata absent, product tasks unticked, the gitignored skills mirror absent in the fresh worktree (`agent-ready skills --regenerate`), the run's own events log uncommitted, and the schema runtime unprepared.
- 3.3: `agent-ready metrics input-trust-rule --base-sha 1afcd29… --head-sha 433bf4d…` (full IDs in `metrics.json`); base 1afcd29 excludes the merged-in activation commit.
