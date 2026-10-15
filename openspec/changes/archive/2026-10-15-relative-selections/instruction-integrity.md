## Effective instruction stack

| Source | Scope | Priority | Available | Effect on this change |
|---|---|---|---|---|
| Platform and runtime (Claude Code, Opus 5.5, offline) | Tools, filesystem | Highest | yes | Isolated worktree `/private/tmp/junoscfg-relative-selections`; no network, no device calls, no push |
| Organisation policy (DG-i) | All output | Highest | yes | Synthetic values only |
| Owner rule 2026-10-15, as relayed in the Orchestrator's task brief | This batch | Owner (relayed) | yes | "I do not want to fix PyYAML problems; if this is a genuine junoscfg problem fix it, if not leave it." |
| Owner ruling 2026-10-15 on PO-1 leftovers, as relayed in the same brief | Relative path selections | Owner (relayed) | yes | "Do what you deem best", under the rule: fix (a) skipped schema-context coercion (recommended: render the selection from the absolute object), (b) relative `set` of a selected list printing a Python repr, (c) a selected `None` writing nothing, (d) an annotation-key selection writing `[null]`, each with a regression test observed failing first; (e) keys holding a dot: fix only without new `--path` syntax and without a cli break, else report as a pending owner decision |
| AGENTS.md, ARCHITECTURE.md | Repository | Repository | yes | Equivalent-not-identical output, fix at the owning layer, measure the blast radius, docs checklist, beta stage rules |
| agent-ready-change skill, batches.md and phases | Workflow | Skill | yes | Second of two independent changes, after yaml-depth-ceiling (merged `c21e7b8`, v0.28.19); standard lane, type bug, tests first, one full checkpoint, fresh Reviewer |
| src/junoscfg/convert/CONTRACT.md, tests/CONTRACT.md | Modules, tests | Repository | yes | No writer changes the IR it is given; writers are the owning layer of spellings |
| openspec/specs/conversion/path-filtering | Approved spec | Specs | yes | Its exclusions (annotation selections, groups wrapper, coercion, dotted keys) are what this change covers; "the renderer receives the contents below `system`" changes |
| Archived review `openspec/changes/archive/2026-10-15-relative-null-flags/review.md` (C5, TC8, TC12, R1, R5) | Evidence | Evidence | yes | The five defects (a) to (e) |

## Conflicts

| ID | Sources and contradiction | Classification | Resolution owner and safe action | Effect |
|---|---|---|---|---|
| C1 | Path-filtering spec: "the renderer receives the contents below `system`" and "preserve the existing relative ... semantics"; ruling (a) recommends rendering the selection from the absolute object | automatically resolved by precedence | Builder: the renderer receives the path-wrapped IR and the path, and writes the selection without it; the requirement is modified | Spec delta |
| C2 | Measured at base (private_test_data/makeover-work/relative-selections/probe_all.py): the context skip also spells relative set and structured wrongly for mapping selections (`--path interfaces --relative` writes `set interface et-0/0/2 ...`, which Junos does not load under `edit interfaces`); the ruling names coercion, lists, null and annotations | automatically resolved by precedence | Builder: one rule for every writer (the selection as absolute output writes it, without its path), the blast radius measured and recorded; within "do what you deem best" and the rule (a genuine junoscfg defect) | Relative set and structured output change for selections whose spelling depends on the schema context |
| C3 | (e) is fixable with no new syntax: a dotted key is resolved against the keys present, exact key first, so only paths that selected nothing before change | automatically resolved by precedence | Builder fixes it; recorded as additive | None for paths that matched |
| C4 | Brief: worktree under `/private/tmp`, Builder merges and archives | automatically resolved by precedence | Builder | Location and finalisation order |
| C5 | Device question C8 of relative-null-flags | owner decision required | Not acted on | Reported |

## Assurance

- Standing preference: economy (`pyproject.toml` `[tool.template.assurance]`, record
  docs/how-to/run-a-batch-of-changes.md#assurance; key `default`).
- Required roles: Builder; independent Test/Challenge; fresh isolated Reviewer at least as
  capable as the Builder; Finalizer (Builder, bounded).
- Mandatory risk floor: high. Named surfaces (`consumer`: `convert_config(path=, relative=)`;
  `cli`: `--path --relative`) change their output.

## Execution checkpoint

Base `d3ed627` (master, v0.28.19). Standard lane, type bug. Command: `uv run --locked --group
dev --with griffe --with tach --with towncrier --with vulture agent-ready check --set full
--base d3ed627`; physical schema dumps copied into the worktree. Evidence folder:
`private_test_data/makeover-work/relative-selections/`. Integration: merge `--no-ff`, archive
commit with the version bump, VERIFICATION.md note, activation park, annotated tag; no push.

## Owner decision batch

None blocking.

## Delta log

- Initial preflight: consistent after C1 to C5. Resume: phase 1 proposal.
