---
name: agent-ready-onboard
description: Bring a repository under this workflow, one approved phase at a time. Use for a new project or for retrofitting an existing one.
---

# Onboard

Invoke as `agent-ready-onboard <phase>`, one phase per session, each ending in a human
approval. Read this file and the one phase file you are running. Do not read the
others; they cost tokens you will not use.

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

Use no asking mechanism that only one runtime has: Claude Code offers a
structured picker and Codex does not, so a phase that leans on one stops working
for half the adopters.

## Sessions, approval, and the log

A session boundary sits at every approval. The phase table is the ceiling on
how much one session does, not a quota: on a small package phase 3 may pin every
module in one sitting, while on a large one each pinned module is its own pull
request. What never moves is the order: pin, then gate, then contract.

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

`agent-ready` is the check package the template pins. This is its whole
surface, so a gap is found by reading this table rather than by writing a
script; a phase that needs something not listed here reports the gap.

| Subcommand | Checks or writes |
|---|---|
| `scaffold architecture\|zone\|domain\|contract\|decision\|template\|agents` | an artefact, its underivable fields written as sentinels; `template` seeds a brownfield `pyproject.toml` with the shipped tables, the check package's source; hook activation waits for phase 4; `agents` writes the instruction file skeleton and the Claude bridge |
| `fields [--sections N ...] [--base REF]` | sentinels and `[inferred]` markers, the zone vocabularies, contracts, the `onboarded` date, the live changes' fields, the stage key against `stage.md`'s rules and the base ref, the instruction file with its stage block and the Claude bridge |
| `caps [--write-baseline\|--homes]` | document line caps from `[tool.template.caps]` and section caps from `[tool.template.section-caps]`; `--homes` lists the artefact homes no cap covers |
| `gates` | every gate's mode and expiry |
| `toolbox` | a licence per approved tool, a reason and a date per rejection |
| `interfaces [--write-baseline]` | names reached through a module reference, and `__all__` against the expose list |
| `specs [--write-baseline]` | every capability under `openspec/specs/` sits under a declared domain |
| `reconcile [--write-baseline]` | every requirement under `openspec/specs/` names an acceptance test that exists |
| `render codeowners\|toolbox\|decisions\|levers\|stage [--check]` | the renderings from `pyproject.toml` and the decision records, the stage block of `AGENTS.md` among them, or whether they are current |
| `decisions` | decision records and toolbox trial entries: fields answered, `review-by` not passed |
| `stage griffe\|towncrier\|vulture` | the tool, in the mode the declared stage sets |
| `metrics <change>` | the git-supplied fields of a change's metrics record |
| `check [--base REF]` | the slow set in one command: every check the CI workflow runs, the names of the failed ones last |
| `update [--to REF] [--data K=V] [--no-checks]` | the repository brought to the newest template release: `copier update`, the check package's tag, the lock, the conflicts and the failing checks reported |
| `codemap build\|show <symbol>\|slice --change <slug>\|check` | the symbol index from griffe and tach, one symbol's span, the change's code-map slice, the contracts' precedent pointers and the slice against the index |
| `lane [--base REF]` | the live change against its lane: the fix lane's caps, `removes`, the design, the retires list, the declared breaks on touched surfaces |
| `retired [--base REF]` | a live pivot's retired terms outside the allowed homes, each term's count at the base, the record that names them, the removed symbols against its list |
| `budget [--report]` | the always-loaded set against its token budget and Codex's metadata ceiling |
| `skills [--regenerate]` | skill frontmatter, runtime parity, the generated mirror |

## Prerequisites

uv, git, and Python 3.11 or later; Node 20.19 or later for the OpenSpec CLI,
which `npx --yes @fission-ai/openspec@1.13.0` runs; Copier and pre-commit
through `uvx`; griffe, tach, towncrier, and vulture through `uv run --with`,
as the CI workflow does; and clone access to the template repository, whose
git history is where the check package comes from until it is on PyPI.

## Step zero: the template in the repository

Greenfield arrives complete from `copier copy`; `uv lock` pins the check
package and nothing else is needed before phase 0.

Brownfield brings the template in before any phase, from the application root:

1. Run `uvx --from 'git+<template-url>@<checks-tag>#subdirectory=checks' agent-ready --root . scaffold template --dry-run` and present its keep, add,
   merge, and activate-later report. It writes nothing. Confirm the existing
   acceptance command, canonical sources, container route, local instructions,
   measured limits, hooks, and CI with the owner before applying additions.
2. Run `uvx --from 'copier==9.18.2' copier copy --vcs-ref <tag> --defaults --data mode=brownfield
   <template-url> .`. Brownfield hosting defaults are off. If a file collides,
   use Copier's skip for that path and record a merge proposal; preserve the
   application file. Copy inert resources only. Do not install hooks or enable
   hosting before phase 4.
3. Run `uvx --from 'git+<template-url>@<checks-tag>#subdirectory=checks' agent-ready --root . scaffold template` for safe missing seeds. It retains
   existing template tables, test-command argv, dependencies, uv settings,
   tool settings, instructions, hooks, and CI. Review each merge proposal.
   Use the application's native dependency workflow. Run `uv lock` only if
   this application uses uv; otherwise install the check package as a tool
   through the existing workflow.

From here every phase has the tool it names.

## Phases

| Phase | File | Ends with |
|---|---|---|
| 0 Interview | `phases/0-interview.md` | arc42 sections 1 to 3, owners, the stage key |
| 1 Architecture | `phases/1-architecture.md` | section 8, zone and domain tables |
| 2 Toolbox | `phases/2-toolbox.md` | toolbox and dependency policy |
| 3 Pinning | `phases/3-pinning.md` | characterization tests (brownfield only) |
| 4 Gates | `phases/4-gates.md` | the answers file, gates installed, baselines, expiry dates |
| 5 Contracts | `phases/5-contracts.md` | module contracts |
| 6 Specs | `phases/6-specs.md` | OpenSpec configured, every capability under its domain |
| 7 Handover | `phases/7-handover.md` | `AGENTS.md`, `onboarded` dated, first change recorded |

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
