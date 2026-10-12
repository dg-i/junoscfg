## Effective instruction stack

| Source | Scope | Priority | Available | Effect on this change |
|---|---|---|---|---|
| Platform/system/runtime | All operations | Highest | yes | Sandbox approvals; no secrets or destructive actions |
| Developer and owner implementation request | Current change | Higher than local skills | yes | Implement approved optimization plan continuously; no repeated phase permission |
| agent-ready-change phases 0–7 | Workflow | Local skill | yes | Committed checkpoints; independent test/challenge and fresh review |
| AGENTS.md; ARCHITECTURE.md; tests/CONTRACT.md; tools/schema_verification.CONTRACT.md | Repository and changed modules | Local repository | yes | Preserve semantic evidence, named public surfaces, owning layer and verification |
| Approved schema-pipeline/verification-evidence spec, existing acceptance tests | Schema verification | Baseline | yes | Exact coverage, immutable inputs, metadata integrity and truthful completion |
| graphify skill and graph | Context discovery | Local skill | partial: managed worktree has no graph | Use contracts, codemap and source directly; no graph rebuild |

## Conflicts

| ID | Sources and contradiction | Classification | Resolution owner and safe action | Effect |
|---|---|---|---|---|
| C1 | Full before review versus owner-approved harness review before costly qualification | automatically resolved by precedence | Owner approved updated plan; focused tests and fresh review precede coordinated full/schema qualification | No costly schema until root coordinates |
| C2 | Template-owned stability execution versus approved one-suite/two-build plan | repository/skill correction | Application-owned spec/contract migration; retain installed template unchanged | Adapter owns generation-only comparison; remove redundant tier declarations |
| C3 | Prescribed sibling worktree versus desktop managed worktree | automatically resolved by precedence | Runtime managed worktree tool | Isolated codex branch; main remains clean |

## Assurance

- Standing preference: economy
- Standing record: pyproject.toml [tool.template.assurance], default and trust-boundary; docs/how-to/run-a-batch-of-changes.md#assurance.
- Mandatory risk floor: verification integrity is a trust boundary; independent Test/Challenge and fresh Reviewer at least as capable as Builder are required.

## Owner decision batch

None: owner approved the updated plan and implementation. No consumer or CLI change, new dependency, or cache framework. Further parser/API refactoring waits for measured evidence.

## Delta log

- Initial preflight: consistent with owner-approved scope; baseline master 9bdd15d. Resume phase 1 after fields/caps and commit.
