## Effective instruction stack

| Source | Scope | Priority | Available | Effect on this change |
|---|---|---|---|---|
| Platform and runtime | All actions | Highest | yes | Sandbox permissions; preserve user work |
| Developer and owner request | Supplementary tests | Above local workflow | yes | Finish trigger reduction first; retain real qualification policy |
| agent-ready-change | Change lifecycle | Local skill | yes | Maintenance lane, committed preflight and intent, fresh review then full |
| AGENTS.md and ARCHITECTURE.md | Repository | House rules | yes | Isolated worktree; public doors; synthetic data |
| tests/CONTRACT.md and validate/CONTRACT.md | Tests and generator | Module rules | yes | Test at owning module, real public build, no runtime edits |
| schema-pipeline specs and existing tests | Behavior baseline | Baseline | yes | Supplement coverage without replacing real schema qualification |
| graphify graph | Discovery | Supporting context | unavailable in managed worktree | Use contracts and source; do not rebuild graph |

## Conflicts

| ID | Sources and contradiction | Classification | Resolution owner and safe action | Effect |
|---|---|---|---|---|
| C1 | AGENTS full-before-review versus maintenance lane review-before-full | automatically resolved by precedence | Owner explicitly requests fresh source review before coordinated full | Run focused evidence first; root coordinates full |

## Assurance

- Standing preference: economy
- Standing record: pyproject.toml [tool.template.assurance] default; docs/how-to/run-a-batch-of-changes.md#assurance.
- Mandatory risk floor: schema yellow; supplementary tests preserve behavior and qualification policy, no changed trust boundary. Maintenance lane gets fresh lightweight review.

## Owner decision batch

None. User requests supplementary synthetic generator tests after merged trigger reduction. A five-second target is measured, not a flaky assertion. Real schema policy remains unchanged. Runtime defects return to owner for separate scope.

## Delta log

- Initial preflight: clean master 630a5c9, v0.28.4. Next: maintenance intent. No product edits.

## Changelog gate correction
The first full checkpoint passed 10,427 tests but its mandatory towncrier gate rejected the maintenance no-fragment choice. Add one misc fragment and align metadata; no tests or product behavior change. Preserve the failed receipt and rerun the required full checkpoint.
