# Instruction integrity

## Effective stack

Platform and developer instructions govern tools, preservation and approval.
The owner invoked agent-ready-refresh, accepted retaining the current hooks,
set a 275-second full-check budget, and authorized commit and merge on 2026-10-13.
AGENTS.md, ARCHITECTURE.md, agent-ready-refresh, agent-ready-change phase 0
and its maintenance route govern this adoption. There are no nested AGENTS.md
files applicable to the planned edits. tools/schema_dependencies.CONTRACT.md
requires regeneration after any parsed lock change except the root version.
Existing tests and verification-evidence.md remain binding.

## Scope and assurance

One low-risk application adoption of template v0.12.0: preserve hook behavior,
regenerate its dependency projection, initialize verification guidance, and admit
this work for the unchanged verification gates. No product behavior, dependency,
public surface, stage, cap or verification mechanism changes in this adoption.
Economy is the standing preference from pyproject.toml [tool.template.assurance],
record docs/how-to/run-a-batch-of-changes.md#assurance. A fresh lightweight
maintenance reviewer is required by the solo-repository route.

## Conflicts and decisions

The updater requires an exact committed diff; the application hook rejects its
stale fingerprint. Classification: repository/skill correction. Preserve the
exact update in ef33c70, with the already-executed failed test recorded; defer
that hook only on the red checkpoint, repair separately here, and require the
full green checkpoint before merge. No success is inferred from a skipped hook.
The owner's approval covers the proposed hook renewal and verification adoption;
no repeated phase approvals are needed. Existing expiry 2027-04-08 is retained.
Unknown stage timing targets remain explicitly unmeasured, not invented.

## Checkpoint

Update base 95585fbf1cd59fe4b9cb15be870f6a5020be49a3; exact updater ef33c70.
Receipt reproduced byte-for-byte in this worktree with local attestation.
Prior hook: 10439 passed, 13 skipped, 20 xfailed, one stale fingerprint failure.
Full check refused unassessed branches before any tests. Next: approved intent,
application edits, focused checks, fresh review and full verification.
