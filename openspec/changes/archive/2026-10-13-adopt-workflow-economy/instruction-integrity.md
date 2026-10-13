# Instruction integrity

Effective instructions: platform/developer tool and preservation rules; owner
request to release/tag upstream and adopt here without pushing; AGENTS.md and
ARCHITECTURE.md; agent-ready-refresh; agent-ready-change phase 0 and maintenance
route; run-a-batch-of-changes.md; verification-evidence.md; tests/CONTRACT.md,
src/junoscfg/CONTRACT.md and tools/schema_dependencies.CONTRACT.md. No nested
AGENTS.md applies to these edits. Unavailable native session telemetry is not
inferred. Commands and raw logs are retained in private_test_data/workflow-refresh-2026-10-13.

The upstream agent owns release commits/tags; this Builder owns junoscfg.
The exact updater and its receipt remain separate from application-owned fixes.
This maintenance change only refreshes the generated dependency projection,
admission inventory, verification record and integration bookkeeping. It does
not change product behavior, dependencies, hooks, schema assertions or selection
policy; the independently released dependency update belongs to the updater.

Assurance: economy, from pyproject.toml [tool.template.assurance] and the standing
record in docs/how-to/run-a-batch-of-changes.md#assurance. No new public surface,
trust boundary, migration or declared break is introduced by application
bookkeeping. The solo maintenance route requires fresh lightweight review;
standard spec/design/new-test phases are omitted. Existing preservation tests,
full verification, archive and patch version/tag remain required.

Conflicts resolved by precedence: the application archive/bump-before-fast-forward
procedure governs the generic post-merge archive instruction. Temporary worktree
placement respects sandbox paths while retaining isolation. The maintenance gate
requires review.md before full verification, so the short-lane order governs the
generic full-before-review instruction. Owner authorization covers routine release
and adoption decisions; no phase-transition approvals are needed.

Repository/skill correction: a lock update can invalidate the application-owned
projection while the updater requires an exact committed diff. If observed,
preserve the failed focused fingerprint check, commit the exact red updater with
only affected-tests deferred, then repair in the next application commit and
require all checks green before integration. This follows the recorded refresh
precedent; no red evidence is reported as passing and no receipt is rewritten.

Entry master: 362301f834db3559f0f86f7ae0f6e378905dc3ad, clean. Cadence anchor
95585fbf1cd59fe4b9cb15be870f6a5020be49a3 has 52 first-parent commits; retain the
pending invitation. Current Python is 3.14.7; installed caches are reused.
Historical native receipts are copied unchanged for provenance, not reattributed
to this worktree. The engine decides reuse and qualification after the update.

Material unresolved owner questions: none. Upstream release identity is pending
execution, not an owner decision. Next: committed intent, tagged updater, bounded
application repair, fresh review, canonical full, metrics and local integration.

## Approved scope delta

The owner approved upstreaming reusable guidance and retaining application rules
in companion pages, then installing the tagged template. The two shared pages
return to their exact recorded v0.12.0 baseline before the updater is rerun. All
local additions are preserved verbatim in companions at this checkpoint; after
the reusable protocol ships, its local duplicate becomes a reference plus local
cohort settings. Navigation and current links move with their owning guidance.
The failed updater output is preserved in the ignored evidence bundle. Its stale
fingerprint check failed as expected; no successful receipt was claimed.

## Released adoption evidence

Template v0.13.1 is a41925e16f53044aa48c8ad986c25b5eebad4969; checks-v0.17.1 is 4facc558a34acfdacae913b7f0e4cccbe3277a51. The checks source diff from production 4e8f8faf44a77c1e59fcd351fd00dc02aa677a58 changes only update.py. Verification engine, product and tooling sources are unchanged. The consumer-boundary delta is exactly pyproject.toml and uv.lock; refreshing that reviewed inventory preserves conservative selection. Existing native evidence is not relabelled. Qualification follows actual validity.
