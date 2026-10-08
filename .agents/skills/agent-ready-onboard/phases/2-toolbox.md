# Phase 2 — Toolbox and policy

## Outcome

`[tool.template.toolbox]` lists every approved library and system tool with
purpose, minimum version, and licence, and the considered-and-rejected list
carries a reason and a date per entry. `agent-ready toolbox` passes and
`docs/TOOLBOX.md` is rendered from the table.

## Greenfield

Propose the defaults the template ships and record each with its licence. A
rejected alternative is recorded the first time somebody asks why it was not
chosen, which is cheaper than answering twice.

## Brownfield — evidence to gather

The lockfile, the dependency groups, the CI configuration, and anything invoked
by a shell script or Makefile. System tools are the ones people forget: a binary
the tests shell out to is a dependency whether or not it appears in a manifest.

Report, per entry: last release date, open issue count, and licence. The first
two need the network and the licence often does. Where the session has none,
say so, and record the licence as the installed package's metadata or its
LICENSE file on disk states it; an entry you could only assert is marked as
such in the friction log. `agent-ready toolbox` reports a licence string it
does not recognise so the human knows which rows to verify themselves. A tool
with no licence recorded fails the check, because the licence decision is made
from this table and a blank column silently shrinks the evidence.

Read a minimum version from what is actually tested, the lockfile or the
container image, never from what a manifest declares and nothing exercises.

## Questions you must ask

1. Which of these is load-bearing and which is here by accident? A dependency
   used once in a script is a different decision from one in the request path.
2. Which of them are you already trying to remove?
3. Is any licence here a problem for how this code is distributed?
4. For a tool that looks unmaintained: is it replaced, or is it finished?

## Approval

The human approves the toolbox and the dependency policy. A library on
probation is a trial entry, `[tool.template.toolbox.trial]`, with a `review-by`
date that `agent-ready decisions` validates until it is confirmed or removed.
`docs/TOOLBOX.md` is rendered from the approved table with `agent-ready render
toolbox`, never hand-edited; `agent-ready render toolbox --check` is the gate
that keeps it so. Stop here: the next phase is a new session, and `agent-ready status` resumes it.
