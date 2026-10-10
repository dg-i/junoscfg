# Checkpoint

- Next incomplete phase: 5 (change and verify; documentation-only route).
- Last valid evidence: the phase-4 commit holding `tasks.md` (1.1 to 1.21 tightened per the
  challenge), `test-challenge.md`, `review.md` with challenges S1 to S7 and their interim
  actions, `main-spec-edit.md` rebuilt on the sibling delta's wording plus the five ids,
  and the corrected `docs-plan.md` and `evidence-freeze.md`.
- Owner decisions pending (none blocks phase 5; each interim action is a safe reversal to
  owner-approved text or a narrowing to what tests assert): S1 to S7 in `review.md`; the
  three open product defects listed there; whether to move commit 01efe85 to `master`;
  whether to answer `assurance` in the sibling change so the `fields` gate passes.
- Gates run in a detached worktree of the checked commit; the owner's uncommitted files
  are never stashed.
- Telemetry: raw events in `private_test_data/agent-guidance-telemetry/telemetry-events.jsonl`
  (gitignored); bound `workflow-telemetry.json` is written in phase 7.
