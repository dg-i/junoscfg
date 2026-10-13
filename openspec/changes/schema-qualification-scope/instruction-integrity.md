# Effective instructions and preflight

Platform/developer constraints, owner request, AGENTS.md, agent-ready-change,
module contracts and approved specs govern this change. The owner explicitly
requests implementation, independent review, upstream release/adoption and local
integration/versioning; no push. No further outcome decision is outstanding.

Base: 901ddc0ca220c7610edda8e01c4bc3d20e38f85d on master. Dedicated branch
codex/schema-qualification-scope and isolated junoscfg-wt worktree; clean at entry.
Upstream reusable implementation belongs in agent-ready-python under its own
self-application workflow; application classification stays local. Existing
worktrees and unrelated work are preserved.

Standing assurance: economy, pyproject.toml and
run-a-batch-of-changes.md#assurance. Evidence validity is a trust boundary:
independent Test/Challenge and fresh isolated Reviewer are required. No product
consumer or CLI surface changes, no new Junos acceptance; device artefacts are
not needed for classification changes. Existing private schema dumps supply
qualification, physically copied to this root; evidence is never copied.

Conflict: current contracts require whole-lockfile/configuration/tooling scope
and exempt validator bodies; owner explicitly requests execution-path scope and
validation algorithms. Classification: automatically resolved by precedence;
update implementation, contracts, specs and regression expectations together.
Installed template-owned instructions are updated only through upstream adoption.

Lane: standard bug; zone schema; domain schema-pipeline. One application outcome
with an upstream dependency. Ordinary tests, integrity, coverage, independence
and canonical full command remain unchanged. No blanket skip override.

Commands: focused tooling pytest while editing; canonical full uv run --locked
--group dev --with griffe --with tach --with towncrier --with vulture agent-ready
check --set full --base BASE; final fast and focused checks after review fixes.
Measure native command evidence and wall time. Read docs/VERIFICATION.md at entry:
400/200/95 second cold/warm/no-schema happy-flow targets remain; pending cadence
invitation remains pending. No new budget or general improvement is inferred.

Integration: upstream reviewed checks release then separate template tag; adopt
immutable local tags, complete Junoscfg full/review/finalization, merge locally,
archive and bump both version files from master, tag vVERSION. Never push.
Evidence: old selector, source boundary and fingerprint inspected; graph traversal
provided architectural orientation but lacks current selector details, so actual
source/contracts are authoritative. Resume: phase 1; outstanding decisions: none.

Owner steering on 2026-10-14: reuse valid completed assurance, finish only binding
obligations, batch bookkeeping, resolve cheap gates before one final combined-base
full run, freeze verification snapshots, retain the successful 83.88s demonstration,
and finish local merge/archive/version/tag without pushing. This narrows execution
work without changing tests, coverage, integrity, hooks or independent review.
