## Why
Expensive qualification follows whole-lock, tooling and configuration identity,
so updater-only dependency releases force schema work. Validator body exemptions
also fail to represent schema-validation algorithm changes.

## What Changes
Bind qualification to producers, execution dependencies, inputs, generation
options and validation algorithms; keep unrelated workflow and release edits out.
Project dependency identity onto actual schema dependencies and reuse valid native
proof across irrelevant changes, explaining concrete selection failures.
Update contracts and enforcement together, adopt reviewed shared runtime support.
Search readers: tools/schema_selection.py, tools/schema_dependencies.py,
tools/schema_verification.py, tests/support/schema_data.py, pyproject.toml and
native verification modules. No blanket skip option or alternate evidence store.

## Capabilities
### Modified Capabilities
- `schema-pipeline/verification-evidence`: execution-scoped qualification.

## Non-goals
No Junos syntax, generated artifacts, consumer/CLI behaviour, ordinary test,
coverage, integrity, review or performance-budget reduction; no push.

## Completion
Focused bidirectional regressions, updater-only release regression, independent
challenge/review, measured full checkpoint and selection demonstration; upstream
workflow/release then local application integration/archive/version/tag.
