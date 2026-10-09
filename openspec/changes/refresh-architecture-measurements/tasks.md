## 1. Verification

- [ ] 1.1 Run `uv run --locked --group dev --with griffe --with tach --with
  towncrier --with vulture agent-ready check --set full`; expect every
  documentation and repository check to pass, including Markdown links and
  anchors.
- [ ] 1.2 Inspect `git diff master...HEAD -- ARCHITECTURE.md`; expect no user
  command or example to be added or changed.
- [ ] 1.3 Run `test -d src/junoscfg/validate/data` and
  `uv run --locked --group dev agent-ready codemap check`; expect both the
  referenced artifact directory and fresh code-map pointers to resolve.
- [ ] 1.4 Compare the edited layering text with `AGENTS.md`, `tach.toml`, and
  `src/junoscfg/display/CONTRACT.md`; expect “shared kernel,” zone names, and
  dependency direction to agree without another transient count.
- [ ] 1.5 Inspect `git diff --name-only master...HEAD`; expect
  `ARCHITECTURE.md` to be the only product document and the remaining paths to
  belong to this change record.
- [ ] 1.6 Inspect the edited sections in rendered Markdown; expect intact list
  numbering, code fences, links, paragraphs, and headings.

Baseline: `rg -n '36 MB|runtime edges|1337 lines|constants.py.*194'
ARCHITECTURE.md` finds the four stale or unsupported measurements. The artifact
directory, fresh code-map check, and `tach check` already pass.

## 2. Change

- [ ] 2.1 Edit only `ARCHITECTURE.md`: remove the transient measurements while
  retaining the cost ranking, compressed-artifact policy, shared-kernel role,
  dependency direction, and their enforceable checks.

## 3. Review and evidence

- [ ] 3.1 Complete the fresh-session review and write `review.md`.
- [ ] 3.2 Capture `metrics.md` and `metrics.json` for the immutable base and code head.
