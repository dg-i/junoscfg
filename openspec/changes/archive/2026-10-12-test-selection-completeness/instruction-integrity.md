## Effective instruction stack

| Source | Scope | Priority | Available | Effect |
|---|---|---|---|---|
| Platform, developer and runtime | All actions | Highest | yes | Preserve work; escalate managed-worktree writes |
| Owner request and orchestrator assignment | Optimization batch | Above local workflow | yes | Repair selection, commit and merge; parent coordinates merge and full checks |
| agent-ready-change | Lifecycle | Local skill | yes | Standard bug lane, committed intent/freeze, fresh review |
| AGENTS.md and tests/CONTRACT.md | Repository and tests | House rules | yes | Focused tests while editing; keep public runtime behavior |
| Existing selection implementation and tests | Tooling behavior | Baseline | yes | Preserve package/importer selection and direct test selection |
| graphify skill and graph | Discovery | Supporting | graph unavailable in managed worktree | Read source, contracts and codemap without rebuilding |

## Conflicts

| ID | Sources | Classification | Resolution owner and safe action | Effect |
|---|---|---|---|---|
| C1 | No declared zone owns selector tooling; phase requires zone | automatically resolved by precedence | Orchestrator follows batch-process-config precedent: surface zone with explicit tooling grouping | No public surface changes or new ownership table |
| C2 | User authorizes optimization/commit/merge; local approval boundaries | automatically resolved by precedence | Owner's approved plan covers concrete selection repair | Continue without repetitive permission requests |

## Assurance

Economy from pyproject.toml [tool.template.assurance], record docs/how-to/run-a-batch-of-changes.md#assurance.
This change adds coverage to ordinary pre-commit pytest selection; it changes no qualification evidence admission, trust boundary, named surface, migration or runtime domain.
Independent Test/Challenge is not required below the mandatory risk floor; fresh isolated Reviewer remains required in this solo repository.

## Owner decision batch

None. Standard bug lane because required files exceed explicit fix-lane limits. Parent coordinates activation and full-check admission.

## Checkpoint

Phase 0 complete at clean base a7da186; next phase 1. No implementation or tests changed.
