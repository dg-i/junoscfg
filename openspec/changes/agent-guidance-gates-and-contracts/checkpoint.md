# Checkpoint

- Next incomplete phase: 6 (fresh isolated review plus the post-implementation half of the
  independent Test/Challenge), then 7 (metrics with telemetry, main-spec application; no
  archive, no merge).
- Last valid evidence: change commit 19d05de (the eight deliverables) and the evidence
  commit after it (this file, `tasks.md` 1.1 to 1.8 and 1.11 to 1.21 ticked with evidence,
  2.1 to 2.6 ticked). Full checkpoint at 19d05de in a detached worktree: every check
  passes except `fields` (sibling change, no `assurance`) and `lane` (the owner's commit
  01efe85 on this branch edits two `.agents/skills/agent-ready-garden/` files, which the
  docs lane may not carry).
- Owner decisions pending, none of them blocking phase 6:
  1. Commits 01efe85 (garden skill files) and 306233b (the garden audit review and the
     `mkdocs.yml` nav line, committed at the owner's request) sit on this branch; the docs
     lane may carry neither the two skill files nor `mkdocs.yml`, so the lane gate and the
     full checkpoint cannot pass with them in the pull-request range. Recommended:
     cherry-pick both onto `master` and rebase this branch onto the result (the Builder
     does it on the owner's word). The older untracked review
     `docs/reviews/2026-10-10-identifier-key-fields-agent-guidance.md` stays untracked.
  2. The sibling change's `assurance` field: answer it in
     `openspec/changes/identifier-key-fields/.openspec.yaml` or archive that change; the
     `fields` gate fails until then.
  3. Challenges S1 to S7 in `review.md`: each carries the interim action already applied;
     accept, reject or clarify.
  4. The three open product defects listed in `review.md` (meta on `apply-groups` with
     two names, on a second nokeyword value, and `deactivate` of an absent statement):
     a separate `bug`-lane change with a device artefact first.
- Gates run in a detached worktree of the checked commit
  (`/Users/manon-dev/src/junoscfg-wt-19d05de`, removed at the end); the owner's
  uncommitted files are never stashed. A fresh worktree lacks the gitignored
  `.claude/skills` mirror; `agent-ready skills --regenerate` writes it before the check.
- Telemetry: raw events in `private_test_data/agent-guidance-telemetry/telemetry-events.jsonl`
  (gitignored); bound `workflow-telemetry.json` is written in phase 7.
