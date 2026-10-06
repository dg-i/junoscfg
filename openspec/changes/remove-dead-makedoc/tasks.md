## 1. Tests

- [x] 1.1 Replace `TestSchemaMakedocIsDead`, which pinned the ModuleNotFoundError,
  with `TestSchemaMakedocIsGone`, which pins the command's absence and the fact
  that `generate` and `info` still work. Seen red against the merge base and
  green after the removal.
- [x] 1.2 Drop `makedoc` from the help-text assertions in `tests/test_cli.py`.

## 2. Implementation

- [x] 2.1 Remove the `makedoc` command, its seven options and its dead
  `junoscfg.validate.schema_doc` import from `src/junoscfg/cli.py` (50 lines),
  and its entry from the `fullhelp` registry.
- [x] 2.2 Remove the `### schema makedoc` section from `docs/guide/cli.md`
  (26 lines), which documented it with worked examples.
- [x] 2.3 Bump the minor component to 0.6.0 in the three version sites, as
  `break-bumps` requires for a declared `cli` surface break.
- [x] 2.4 Add the towncrier fragment under `changelog.d/`.
