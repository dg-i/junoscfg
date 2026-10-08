# Phase 0 — Interview

## Outcome

`ARCHITECTURE.md` exists with sections 1, 2, and 3 answered and every
`[inferred` marker in them confirmed or corrected; every area has a named
owner, carried into phase 1's zone table; `[tool.template.stage]` carries
`name`, `surfaces`, `surface-paths`, `owners`, and `review-by`, no scaffold
value left among them. `components` and `break-bumps` are phase 7's, where the
first change has run and the version scheme has been used once. `agent-ready
fields --sections 1 2 3` passes.

## Start

Run `agent-ready scaffold architecture`: it writes the skeleton with a sentinel
in each required section, so nothing left unanswered passes quietly.

## Greenfield — the package first

Copier ships the skeleton at `src/package`, not the name `pyproject.toml`
imports; `agent-ready scaffold package` moves it there, and nothing that reads
the package works before it has run.

## Greenfield

Nothing can be derived, so all of it is asked: work through the sentinels in
order and write the answers in the human's words, not yours.

## Brownfield

Read the keep, add, merge and activate-later report `agent-ready init` printed
first. Present the existing test and acceptance oracle candidates, canonical
configuration and generated relationships, container or other environment
constraints, retained local instructions, existing gates with observed value,
measured caps with their stated reasons, and proposed additions. Distinguish
references from filename candidates and ask for confirmation where the report
is uncertain. The evidence describes current controls; the owner decides intent.

Read first, then ask. The README, the top-level docs, the CI configuration and
the dependency list will answer parts of sections 2 and 3 on their own. Draft
those, mark each claim you concluded rather than read where it stands, as
`[inferred: from the imports]`, and bring the draft to the interview so the
human is correcting a proposal rather than starting from a blank page. The
marker is a sentinel: `agent-ready fields` fails while one remains, whatever
follows the word inside the brackets, so approval is the act of removing them.

Section 1 is the one you cannot draft: the code shows what the system does,
never which quality the team would sacrifice to keep another.

Two documents come out of this onboarding, and nothing but this test tells
them apart: would violating the line produce a wrong artefact, or merely a
badly-written repository? A wrong artefact belongs in `ARCHITECTURE.md`. A
badly-written repository belongs in `AGENTS.md`, which phase 7 writes, however
fixed the rule feels: the language of the code, authoring conventions, the
version-bump procedure, and "every commit leaves the suite green" are all the
second kind, and none of them is a constraint in section 2.

## Questions you must ask

1. When two of these conflict — correctness, latency, cost, simplicity — which
   one wins here? Give an example from this repository if you can find one.
2. What is fixed and not up for discussion: runtime, offline operation, data
   residency, a compliance regime, a customer contract?
3. Where does this system's responsibility end, and who is on the other side of
   each edge?
4. Which areas are frozen, being rewritten, or on their way out? You will need
   this again in phase 1 and it is cheaper to ask once.
5. Who owns each area, going forward? Git blame names who touched it, which is
   not the same thing and is often wrong after a reorganisation.
6. Is there an existing instruction or description document that this
   onboarding replaces? If it goes, list every place that cites it, in code,
   tests and docs, before anything is built on its absence; phase 7 retires it
   from that list.
7. What do you promise whoever depends on this: alpha, beta, or release? I
   would start at alpha unless something already depends on this, because
   alpha is the only stage you can leave without a declared break. A version
   number, a classifier, a tag history, and a user count all describe the
   past, and none of them answers this.
8. Which surfaces does that promise cover: the API, the CLI, the config
   schema, the stored data, the log lines, a wire protocol? Name only what you
   would actually hold still; anything unnamed is regenerated rather than
   migrated.
9. For each surface other than the API, which paths carry it? Propose a glob
   per named surface from the tree; the answer is `surface-paths`, which is
   how the lane gate sees a change touching the surface.
10. Who owns this declaration? It has to be a team or more than one person:
    they become the reviewers of `pyproject.toml`, which holds every cap and
    policy in this template. A repository with one maintainer says so with
    `solo = true` beside `owners`, and drops the flag when a second owner
    arrives; `agent-ready fields` fails the flag the moment one does.
11. When is this re-read? Pick a date you will keep. A self-declared stage is
    otherwise never looked at again, and CI fails on the day the date passes.

## Approval

The human approves `ARCHITECTURE.md` sections 1 to 3, the owner list, and the
part of `[tool.template.stage]` this phase answers, which means every
`[inferred` marker is gone: a confirmed claim loses the marker and a wrong one
is corrected. Do not continue to phase 1 without it, and not in this session:
`agent-ready status` resumes the next one.
