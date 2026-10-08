---
name: agent-ready-onboard
description: Bring a repository under this workflow, one approved phase at a time. Use for a new project or for retrofitting an existing one.
---

# Onboard

Invoke as `agent-ready-onboard <phase>`, one phase per session, each ending in a
human approval. Read this file and the one phase file you are running,
`phases/<phase>-<name>.md`. Do not read the others; they cost tokens you will
not use. `agent-ready status` says what each phase still has outstanding, and
on greenfield which phase comes next.

## Two stances

**Greenfield** is a sequence. Nothing exists to survey, so every fact comes from
the interview and the structure is not up for discussion. Follow the phases in
order.

**Brownfield** is a guideline. Repositories differ in maturity, in scope, in
which tools they already run well, and in which parts are load-bearing, so a
fixed route is wrong for most of them. Each phase states the artefacts it must
produce, the evidence you must gather, and the questions you must ask. Order and
depth are yours to choose against the repository in front of you. One ordering
is fixed: pin, then gate, then contract.

## The rule that governs every phase

**The repository knows the past. The person importing it knows the future.**

Everything you can derive — imports, layers, cycles, churn, the existing
toolchain — describes what this code has been. Whether any of it should continue
is not in the repository. Churn cannot tell you whether a module changes
constantly because it is fragile or because it is being rewritten: the first is
a red zone, the second is about to stop existing.

So: derive what you can, present it as a proposal with the evidence behind it,
and ask for the rest. Never fill an underivable field with a plausible guess.
`agent-ready scaffold` writes those fields as sentinels and `agent-ready fields`
fails while they are unanswered, so a guess is not a shortcut — it is the one
thing that makes the artefact wrong in a way nobody can see later.

Ask in prose, in one batch at the end of a phase: not one question at a time,
and not as a menu. A menu presumes your options are the right ones, and the
answers worth most are the ones that reject the framing — that the question is
wrong, that two of your options are the same thing, or that the word you used
means something else here. Number the questions so a short reply can name one,
give each the evidence you derived, and say what you would do, so the answer is
a correction rather than an essay. An answer that arrives sideways, correcting
the question instead of choosing from it, is the most useful kind.

Where the options differ in what they would tell you, recommend the one that
produces evidence, not the one that saves work. Be most suspicious of
recommending that a step be skipped because you already know what it would
find: that is exactly when it is cheap, and exactly when being wrong goes
unnoticed. Deriving a boundary set you believe is already clean costs minutes
and either confirms your reading or contradicts it; skipping it leaves your
reading unchecked, and your reading is the thing under test.

Ask in prose first. Where the runtime offers a structured picker, as Claude
Code does and Codex does not, offer it after the prose with the same numbered
options: the prose stands on its own on the runtime that has none, and the
picker is a convenience a phase never leans on.

## Sessions, approval, and the log

A session boundary sits at every approval, and the boundary is the cost
control: a session that carries every phase re-reads its whole context on every
turn, and on the second brownfield adoption 43 percent of the run's cache-read
tokens were spent above 850k of context. Each phase ends with the same line:
stop here, the next phase is a new session, and `agent-ready status` resumes
it. A phase is the ceiling on how much one session does, not a quota: on a
small package phase 3 may pin every module in one sitting, while on a large
one each pinned module is its own pull request. What never moves is the order:
pin, then gate, then contract.

Approval is a human act on the artefact, never a field the agent writes. Where
the repository has pull requests, it is the CODEOWNERS review. Where it has
none, the agent stages and the human commits; a phase whose changes the agent
committed has approved itself.

Keep a friction log at a path the repository's `.gitignore` excludes; the
template uses `scratchpad/`. Record every question asked and its answer, every
check seen to fail, and every place this skill or its tool got in the way,
numbered so the template project can act on each. The log is feedback on this
skill, not a document of the repository being onboarded: it is never committed
there and never counted against its caps, and it is handed to the template
project at the end of phase 7.

## The tool

`agent-ready` is the check package the template pins, and `agent-ready --help`
is its whole surface: read it rather than writing a script, and report a gap
rather than working around one. The flags the phases pass are
`--write-baseline`, `--check`, `--base`, `--sections` and `--regenerate`.

`agent-ready status` prints what each phase still has outstanding, read from
this repository. It is a report over the other checks' audits, never a gate,
and it says `not applicable` and `nothing outstanding` but never `done`:
approval is a human act on an artefact, and nothing in a tree records one.

Run the check package's own internals, when a check has to be reproduced
against its source, with `uvx --from <source> ...`, never `uv run` in this
repository's tree: `uv run` syncs the project environment first and rebuilds
it around what it was given. The template adds files under `docs/`, the
how-to guides, `TOOLBOX.md` and the decision records; a site generator with a
navigation list needs them listed or excluded.

## Prerequisites

uv, git, and Python 3.11 or later; Node 20.19 or later for the OpenSpec CLI,
which `npx --yes @fission-ai/openspec@1.13.0` runs; Copier and pre-commit
through `uvx`; griffe, tach, towncrier, and vulture through `uv run --with`,
as the CI workflow does; and clone access to the template repository, whose
git history is where the check package comes from until it is on PyPI.
`agent-ready init` checks the first four before it writes anything.

## Stopping

Stop and report, rather than trying again, when:

- a phase's questions are unanswered — an unanswered question is the phase's
  output, not a blocker to work around;
- the same check or test fails twice in a row, which is more often a contract or
  a spec problem than a code problem;
- you are about to write a fact you cannot point at evidence for.

Run checks with `agent-ready` and the repository's own `pre-commit`. Both
runtimes run them the same way; nothing in this skill depends on a feature only
one runtime has.
