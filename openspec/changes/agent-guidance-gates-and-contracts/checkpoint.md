# Checkpoint

- Next incomplete phase: 4 (QA tasks in `tasks.md`; phase 3 is skipped for type `docs`).
- Last valid evidence: the phase-2 commit holding `docs-plan.md`, `evidence-freeze.md` and
  `main-spec-edit.md`; `openspec validate --strict` passed; `agent-ready reconcile` and
  `caps` passed; the 60 cited test ids collected.
- Open repository correction, not this change's: `agent-ready fields` exits 1 on
  `openspec/changes/identifier-key-fields/.openspec.yaml` (no `assurance`, a field the
  v0.7.8 template added after that change was written). Every field of this change is
  answered. The owner decides whether to answer it there or archive that change first.
- Gate note: `agent-ready lane` refuses to run beside the owner's uncommitted `mkdocs.yml`
  and the untracked review; the checks run with both stashed and restored.
- Telemetry: raw events in `private_test_data/agent-guidance-telemetry/telemetry-events.jsonl`
  (gitignored); bound `workflow-telemetry.json` is written in phase 7.
