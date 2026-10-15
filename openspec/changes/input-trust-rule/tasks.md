## 1. Verification (one per docs-plan QA item)

- [ ] 1.1 Links: `uv run --locked --group docs mkdocs build --strict` exits 0 with no new warning
- [ ] 1.2 Referenced paths and decision slugs exist
- [ ] 1.3 Caps: `ARCHITECTURE.md` at or under 200 lines
- [ ] 1.4 Terminology: `git grep -n "not hostile"` lists only C2/C3 places and pointers to the rule
- [ ] 1.5 Rendered output: markdownlint passes
- [ ] 1.6 One full checkpoint passes

## 2. Change

- [x] 2.1 `ARCHITECTURE.md` section 8 rule and yaml-new pointer
- [x] 2.2 Decision record and rendered index
- [x] 2.3 Pointers from the guide, API page, contracts and the 64-level record

## 3. Review and evidence

- [ ] 3.1 Fresh isolated review recorded in `review.md`
- [ ] 3.2 Capture `metrics.md` and `metrics.json` for the immutable base and code head
- [ ] 3.3 Archive, patch bump, merge and tag without pushing
