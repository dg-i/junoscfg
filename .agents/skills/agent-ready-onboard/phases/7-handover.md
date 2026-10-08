# Phase 7 — Handover

## Outcome

`AGENTS.md` under 100 lines, the always-loaded set under budget, the human
guides adapted, `[tool.template.stage]` completed with `components` and
`break-bumps`, `onboarded` dated, and the first workflow change recorded.

## Instructions and guides

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
agreed policy. CODEOWNERS routes review; hosting settings make it mandatory, and
`docs/how-to/hosting.md` holds what to configure with the operator and what no
check here can see. For solo mode, record owner acceptance plus a fresh agent review:
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

Phase 0 declared the stage, its named surfaces and its owners. `components` and
`break-bumps` are answered here, because nobody can answer them before a change
has run: the scheme is whatever the first release used, and a break on a named
surface raises whichever component the owner has now seen raised. Write them
widest to narrowest in the owner's own scheme, one `break-bumps` entry per named
surface, `none` where its breaks raise nothing. The scheme's meaning is prose in
`AGENTS.md`; the key is what the lane gate reads.

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
