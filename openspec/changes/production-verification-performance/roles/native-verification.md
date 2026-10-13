# Native verification implementation evidence

Agent-ready-python candidate: `4e8f8faf44a77c1e59fcd351fd00dc02aa677a58`.
Base: `43433b033c0f2dc9565c071ccdda595b2d72a097`.
Branch: `codex/native-verification-production`.
Worktree: `/private/tmp/agent-ready-verification-production`.
State: clean; local commits only; no merge, push, release or tag.

## Final checks

- `uv run --directory checks --locked --group dev pytest -q`: **774 passed in 196.51s**, exit 0. Final command tool session `77032`; final result delivered 2026-10-13.
- `uv run --directory checks --locked --group dev pytest tests/test_verification_challenge.py tests/test_verification_runtime.py tests/test_check.py -q`: **55 passed in 3.45s**, exit 0 on final code.
- `uv run --with pre-commit pre-commit run --all-files --show-diff-on-failure`: every hook passed on final code (ruff-format, ruff-check, strict mypy, deptry, document budgets, always-loaded budget, skill mirror, Markdown lint).
- `uv run --directory checks --locked --group dev mypy`: **38 source files**, success. Also rerun by final root pre-commit.
- `uv run --directory checks --locked --group dev deptry src`: no dependency issues. Also rerun by final root pre-commit.
- `uv run --project checks --locked --group dev python scripts/release.py verify`: package/source/template version parity at **0.16.2**, no version changes or release tags.
- `bash scripts/doc-budgets.sh`: exit 0, including unchanged 110-line design-record budget.
- `sh scripts/render-template.sh /private/tmp/agent-ready-verification-final-greenfield greenfield`: exit 0; rendered full gate, six skeleton tests, onboarding/update/schema checks pass.
- `sh scripts/render-template.sh /private/tmp/agent-ready-verification-final-brownfield brownfield`: exit 0; render/preservation/update checks pass.

Final rendering tool session: `72524`. Earlier complete source suite at `464bdfb`: 770 passed in 183.78s. An initial evolving-code run had two identity-change refusals while formatting changed source and one ordinary command-spy compatibility failure; those were fixed/rechecked before the final settled result.

## Identity and review controls

The independent challenge file includes 38 cases: cached and sourceless bytecode, actual malicious-cache execution, source-equivalent cache creation, ephemeral-prefix semantic literals, complete environment and import-path order, duplicate selector keys, selection fallbacks, capacity ownership, admission, worker/gate barriers and failures, scoped hook suppression, corrupt/failed receipts, and real external import-source mutation.

Final fresh-review corrections bind symlink target paths and linked code using cycle-aware traversal; ignored namespace modules and ignored application import shadows participate. New controls execute linked packages and ignored namespaces before/after source mutation and require changed native identity. Per-action runtime/identity refusals fail the checkpoint while remaining selected tier actions are attempted.

Two normal canonical uv driver invocations produced exactly equal entire driver and normalized environment observations on settled source. Retained local evidence: `/private/tmp/native-driver-five.json` and `/private/tmp/native-driver-six.json`; environment values in diagnostic files are individually hashed. These observations preceded the final import-tree corrections, which received final focused/full tests and fresh review. No production timing claim derives from these upstream test durations.

Fresh independent review approval was reported by the parent orchestrator. The parent owns merge/integration and application timings. The implementation retains native capacity/readiness/checkpoint/lifecycle logic, conservative scheduling defaults and application ownership of full-suite/selection declarations.
