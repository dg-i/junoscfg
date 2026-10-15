<!-- Maintained by the agent-ready template. Local edits can conflict with updates.
See docs/how-to/template-ownership.md before editing; review every update diff. -->

# Phase 7 — Handover

## Outcome

`AGENTS.md` under 100 lines, the always-loaded set under budget, the human
guides adapted, `[tool.template.stage]` completed with `components` and
`break-bumps`, `onboarded` dated, and the first workflow change recorded.

## Instructions and guides

Keep the template ownership warning and pointer to
`docs/how-to/template-ownership.md` in `AGENTS.md` and link that guide from
`docs/how-to/work-with-agents.md` when adapting it for the human contributors.

Codex reads `AGENTS.md`; Claude Code 2.1.274 loads it through the one-line
`CLAUDE.md` bridge, `@AGENTS.md`, and `agent-ready scaffold agents` writes both.
Onboarded, `agent-ready fields` rejects a missing file, a placeholder or a wrong
bridge, and `agent-ready budget` leaves the bridge uncounted.

Every root instruction is paid for in every session. Name existing pointer
targets and the rule to read a module's contract and graph entry before editing
and prefer an existing helper. Use the phase 0 test: would violating a line
produce a wrong artefact or merely a badly-written repository? Only the second
kind belongs here rather than in `ARCHITECTURE.md`.

Keep `<!-- agent-ready:stage:begin -->` and `<!-- agent-ready:stage:end -->`
on their own lines and run `agent-ready render stage`; the block carries the
promise, the ban step and pointers, and `--check` detects drift. `agent-ready
caps --report` shows every governed file against its cap; `agent-ready budget`
counts the skill descriptions against Codex's 8,000-character ceiling.

Adapt `docs/how-to/work-with-agents.md` and `docs/how-to/solo-review.md` to the
agreed policy. CODEOWNERS routes review; `docs/how-to/hosting.md` holds settings
the operator must enforce and what no check can see. In solo mode, record owner
acceptance plus fresh agent review: a second read, not a second human. Document
author-owned hosting exceptions without claiming human independence. The human
guide says phases may share a session until approval, while implementation and
review never do; it copies the change skill's canonical full-check command.
Repository changes use `agent-ready-change`. Do not install OpenSpec skills or OPSX commands; use its CLI for artifact operations.

## Ownership and retirement

Agent-ready skills are template-owned. CI workflows are template-maintained in
greenfield; existing brownfield workflows are preserved. See the ownership guide. In
`.agent-ready/template.toml`, the template owns `checks-tag`; the application owns
`[local-policy.<id>]`. For each update recommendation, record its scope, id,
adapter, upstream issue or `local-only` reason, and review date. Fields rejects invalid or expired
policy, and all correctness checks still run.
Point the owner to `docs/how-to/remove-agent-ready.md` for a reversible exit.
Report desired changes upstream; `agent-ready update` updates unedited copies
and may merge local edits or expose conflicts for refresh. Review every update diff.
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
`openspec/changes/<name>/metrics.md`, whose template lists the fields, and
travels with the archive. A change is one merged pull request, or one commit
where this repository has no requests.
Apply reviewed delta edits to main specs while the live folder exists. Commit
the code and main specs, then capture full immutable base and code-head SHAs
and run `agent-ready metrics <name> --base-sha SHA --head-sha SHA` before merge.
After merge, archive with `openspec archive <name> --yes --skip-specs`.
Unavailable session-log fields stay sentinels, never estimates.

The first record is descriptive, not an efficiency baseline: historical git
supplies diffs and never session tokens or human effort, and the paired
comparison `docs/how-to/work-with-agents.md` asks for needs its own sample.

Check each consumer phase 0 named against the onboarded tree: install or
import it the way that consumer does and run what it runs. A consumer that
broke is a finding for the first change, never a note.

## The version scheme

Phase 0 declared the stage, surfaces and owners. Answer `components` and
`break-bumps` after a change has run: use the first release's scheme and the
component a named-surface break actually raised. Write components widest to
narrowest, one `break-bumps` entry per surface, `none` where breaks raise
nothing. Explain the scheme in `AGENTS.md`; the lane gate reads the key. A
change declares its bump; release execution moves all version locations and
creates the tag unless the owner documents a different model.

`agent-ready fields` reports them rather than failing until `onboarded` is set,
so setting `onboarded` is the moment they stop being optional: both happen
here, not in two phases. Run `agent-ready fields` once before setting the
date, because afterwards every deferred report is a blocked commit.

## Questions and approval

Ask which typical change to run, who notices warn-mode expiries and how, what
the human accepted despite disagreeing (the first garden-audit candidate), and,
now a change has run, the versioning components and what each surface's break
raises. The human approves `AGENTS.md` and sets `onboarded = YYYY-MM-DD` under
`[tool.template]`; `agent-ready fields` validates it. `agent-ready status`
reports what each phase still has outstanding, which is how an owner reads the
state later without opening a phase file. Hand the friction log to the template
project as its input, not as this repository's document.

## Discoverable backlog

Confirm `docs/BACKLOG.md` exists and identifies the single authoritative destination;
create it if absent, preserving any existing contents. Link it from the application's
working guidance. A declared tracker stores items and status; the file points to it.
Use `docs/how-to/review-scope.md` for required fields and scope dispositions.
Consolidate deferred findings without cancelling dependencies or binding carries.

## Verification continuity

Confirm `docs/VERIFICATION.md` contains the agreed dimensions, stages and targets.
Initialise its cadence anchor at the observed integration head. Add a short
AGENTS.md instruction to check this record at session entry and job completion,
following `docs/how-to/improve-verification.md`; preserve it on later scaffolding.
Explain the optional ten-commit invitation and unattended-job deferral. Review
state is application-owned and survives template updates.
