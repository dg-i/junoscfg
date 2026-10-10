# Checkpoint

- Next incomplete phase: 6, the re-read of the fix pass by the same isolated Reviewer; then
  7 (metrics with telemetry, main-spec application by the Finalizer; no archive, no merge).
- Last valid evidence: the fix-pass commit after b20ca29 (review.md "Fix pass", tasks.md
  3.1 ticked, the corrected deliverables) with the QA checks re-run on it; `agent-ready
  check --set fast` on that commit in a detached worktree.
- Owner actions pending, blocked for the Builder by the permission classifier: cherry-pick
  01efe85 and 306233b onto `master`, append `assurance: balanced` to
  `openspec/changes/identifier-key-fields/.openspec.yaml` on `master`, commit. The Builder
  then rebases this branch onto `master` and reruns the full checkpoint. Until then the
  full checkpoint fails on `fields` and `lane` only. The older untracked review
  `docs/reviews/2026-10-10-identifier-key-fields-agent-guidance.md` stays untracked.
- Owner decisions pending, none blocking: S1 to S8 in `review.md` (each with its interim
  action applied); the three open product defects (meta command on `apply-groups` with two
  names, on a second nokeyword value, `deactivate` of an absent statement) for a `bug`-lane
  change with a device artefact first.
- Gates run in a detached worktree of the checked commit; the owner's uncommitted files
  are never stashed. A fresh worktree lacks the gitignored `.claude/skills` mirror;
  `agent-ready skills --regenerate` writes it before the check. The Builder's worktree
  `/Users/manon-dev/src/junoscfg-wt-19d05de` is removed at the end.
- Telemetry: raw events in `private_test_data/agent-guidance-telemetry/telemetry-events.jsonl`
  (gitignored); bound `workflow-telemetry.json` is written in phase 7.
