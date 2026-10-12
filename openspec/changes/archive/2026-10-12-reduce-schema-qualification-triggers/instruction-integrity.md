## Effective instruction stack

| Source | Scope | Priority | Available | Effect on this change |
|---|---|---|---|---|
| Platform and runtime | All actions | Highest | yes | Sandbox permissions; preserve user work |
| Developer and owner request | This optimization | Above local workflow | yes | Continue implementation after explicit resume; do not pull upstream |
| agent-ready-change phases | Change lifecycle | Local skill | yes | Commit preflight, intent and freeze; independent challenge and fresh review |
| AGENTS.md and ARCHITECTURE.md | Repository | House rules | yes | Isolated worktree; semantic safety; no named surface change |
| tests/CONTRACT.md and tools/schema_verification.CONTRACT.md | Tests and qualification | Module rules | yes | Fail closed; native wrapper owns caching/admission; no fake completion |
| schema-pipeline/verification-evidence spec and existing tests | Existing behavior | Baseline | yes | Preserve actual assertions, generation integrity and explicit qualification |
| graphify graph | Code discovery | Supporting context | unavailable in managed worktree | Use existing contracts, source and codemap without rebuilding graph |

## Conflicts

| ID | Sources and contradiction | Classification | Resolution owner and safe action | Effect |
|---|---|---|---|---|
| C1 | Full-before-review versus owner-approved source review before costly qualification | automatically resolved by precedence | Owner plan; focused tests and fresh source review first | Root coordinates one final full checkpoint |
| C2 | Template whole-tree identity/filename selection versus desired semantic relevance | repository/skill correction | Application-owned normalized dependency fingerprint and truthful cheap consistency tier | Preserve template unchanged; no second cache or fake assertions |

## Assurance

- Standing preference: economy
- Standing record: pyproject.toml [tool.template.assurance] default and trust-boundary; docs/how-to/run-a-batch-of-changes.md#assurance.
- Mandatory risk floor: high, verification selection integrity; independent Test/Challenge and fresh Reviewer required.

## Owner decision batch

None. Owner requests drastically fewer unnecessary qualification runs. Ignore only the local root version; all dependencies and other lock fields remain safety-relevant. No release-only deferral or relaxed dependency coverage.

## Delta log

- Initial preflight: clean master 1bbd7a7, v0.28.3; user resumed existing task. No product edits. Resume phase 1 after validation and commit.
