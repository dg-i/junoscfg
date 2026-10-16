## 1. Verification (one per docs-plan QA item)

- [ ] 1.1 Links: `uv run --locked --group docs mkdocs build --strict` reports no warning outside `BACKLOG.md`; every warning beyond master's 48 is a `BACKLOG.md` link outside `docs/`, and `ls` finds each new target
- [ ] 1.2 Commands and examples: `run-probes.sh` at the change head gives the results the entries state, and the same output as `probes-716a9d1.txt` apart from the HEAD line
- [ ] 1.3 Referenced paths: `ls` on every path and `git grep -n` on every test name the new text names
- [ ] 1.4 Terminology: `grep -c "Owner ruling 2026-10-16: backlog" docs/BACKLOG.md` counts the eleven new entries and the four extensions; each new entry has the five fields
- [ ] 1.5 Coverage: `grep -n` per brief ID finds each pending item once; P1, P2, P3, A5 and R2-A2 appear only in the non-goals
- [ ] 1.6 Privacy: the diff names `private_test_data/device-probe-2026-10-16/README.md` by path and quotes no `private_test_data` content; every value is synthetic
- [ ] 1.7 Rendered output: `pre-commit run markdownlint --files docs/BACKLOG.md changelog.d/+backlog-open-findings.doc.md` passes

## 2. Change

- [ ] 2.1 Eleven new entries in `docs/BACKLOG.md` after YAML-BREAKS-001
- [ ] 2.2 YAML-BREAKS-001, DEVICE-EVIDENCE, MAKEOVER-19 and XML-INPUT extended
- [ ] 2.3 Changelog fragment `changelog.d/+backlog-open-findings.doc.md`

## 3. Review and evidence

- [ ] 3.1 Fresh isolated review recorded in `review.md`
- [ ] 3.2 One full checkpoint passes: `uv run --locked --group dev --with griffe --with tach --with towncrier --with vulture agent-ready check --set full`
- [ ] 3.3 Capture `metrics.md` and `metrics.json` for the immutable base and head
- [ ] 3.4 Archive, patch bump, merge and tag without pushing

## Evidence

- Baseline at 716a9d1: `mkdocs build --strict` exit 1, 48 warnings, all `BACKLOG.md` links outside `docs/` (`private_test_data/makeover-work/backlog-open-findings/mkdocs-base.txt`); reproducers in `probes-716a9d1.txt` beside it. The new entries do not exist yet, so 1.4 and 1.5 find nothing.
