# Phase 7 — Handover

## Outcome

`AGENTS.md` under 100 lines, the always-loaded set under budget, the human
guides adapted, `onboarded` dated, and the first workflow change recorded.

## Instructions and guides

Codex reads `AGENTS.md` directly. Claude Code 2.1.274 loads it through the
one-line `CLAUDE.md` bridge, `@AGENTS.md`. `agent-ready scaffold agents` writes
both. Once onboarded, `agent-ready fields` rejects missing files, placeholders
and an incorrect bridge. `agent-ready budget` leaves the bridge uncounted.

Every root instruction is paid for in every session. Name existing pointer
targets and the rule to read a module's contract and graph entry before editing
and prefer an existing helper. Use the phase 0 test: would violating a line
produce a wrong artefact or merely a badly-written repository? Only the second
kind belongs here rather than in `ARCHITECTURE.md`.

Keep `<!-- agent-ready:stage:begin -->` and `<!-- agent-ready:stage:end -->`
on their own lines and run `agent-ready render stage`. The generated block
carries the promise, ban step and pointers. Fields checks the ban step;
`agent-ready render stage --check` detects drift. Run `agent-ready caps` and
`agent-ready budget`, including skill descriptions and Codex's 8,000-character
metadata ceiling. Its token estimate uses the measured Claude Code ratios.

Adapt `docs/how-to/work-with-agents.md` and `docs/how-to/solo-review.md` to the
agreed policy. CODEOWNERS routes review; hosting settings make it mandatory.
Configure protected branches, code-owner reviews, approval counts and bypass
restrictions with the operator; GitLab enforcement requires Premium/Ultimate.
The template cannot verify remote protection or reviews without a hosting
integration. GitHub requires any one listed owner, not every owner group.
For solo mode, record owner acceptance plus a fresh agent review:
fresh agent review is a second read, not a second human. Document hosting
exceptions needed for author-owned work, without claiming human independence.

## Ownership and retirement

Explain that agent-ready skills and CI workflows are template-owned. In
`.agent-ready/template.toml`, the template owns `checks-tag` and the
application owns `[local-policy.<id>]` decisions. `agent-ready update` prints
the exact scope and id for a hook recommendation; an owner records the local
adapter, upstream issue URL or `local-only: <reason>`, and review date. A
matching decision stays accepted while its review date is valid; fields
rejects invalid or expired policy, and all correctness checks still run.
Point the owner to `docs/how-to/remove-agent-ready.md` for a reversible exit.
Report desired changes upstream; `agent-ready update`
updates unedited copies and exposes edited copies as conflicts for refresh.
Seeds are application-owned: `pyproject.toml`, `.pre-commit-config.yaml`,
`ARCHITECTURE.md`, `tach.toml`, source, tests and the two human guides. Updates
preserve them; refresh assesses changed checks and `agent-ready scaffold template`.
Retain concise local helper and hazard instructions in AGENTS.md for Codex, and custom CLAUDE.md content for Claude Code.
Retire an instruction document only with phase-0 owner approval. If the bridge
validation conflicts with existing content, present the conflict for reviewed
resolution. Record retained policy, the active check adapter, and the active
hosting platform. Repair citations for any approved retirement.

## First change and baseline

Run a typical real change end to end. Its record belongs in
`openspec/changes/<name>/metrics.md` and travels with the archive. A change is
one merged pull request, or one commit where this repository has no requests.
Record per applicable phase: prefix and work tokens, distinct files read by
artefact type, findings by severity and survival, human minutes and artefacts
read, wall-clock, lines added/removed, dependency count and hook timings.
Apply reviewed delta edits to main specs while the live folder exists. Commit
the code and main specs, then capture full immutable base and code-head SHAs
and run `agent-ready metrics <name> --base-sha SHA --head-sha SHA` before merge.
After merge, archive with `openspec archive <name> --yes --skip-specs`.
Unavailable session-log fields stay sentinels, never estimates.

Brownfield comparison uses the paired task protocol in
`docs/experiments/minimum-comparative-pilot.md`: ten independent pairs provide
directional cost evidence and twenty pairs inform review policy. Historical
git can supply diffs but cannot reconstruct session tokens or human effort.
If comparable old-workflow observations are absent, collect prospective pairs;
the initial git-only record is descriptive, not an efficiency baseline.

## Questions and approval

Ask which typical change to run, who notices warn-mode expiries and how, and
what the human accepted despite disagreeing (the first garden-audit candidate).
The human approves `AGENTS.md` and sets `onboarded = YYYY-MM-DD` under
`[tool.template]`; `agent-ready fields` validates it. Hand the friction log to
the template project as its input, not as this repository's document.
