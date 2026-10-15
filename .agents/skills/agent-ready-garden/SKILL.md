---
name: agent-ready-garden
description: Audit application instructions, documentation, contracts and decisions; run monthly or before release.
---

<!-- Maintained by the agent-ready template. Local edits can conflict with updates.
See docs/how-to/template-ownership.md before editing; review every update diff. -->

# Garden

The garden is the only scheduled writer of shared documents; everywhere else, a
document changes because a change PR touched it. Run this before each release
or monthly, whichever is sooner.

Invoke as `agent-ready-garden <job>`, one job per session. Read this file, the
one job file you are running, and only the support file that job explicitly
requires. Do not read the other jobs; they cost tokens you will not use.

## Jobs

| Job | File | Produces |
|---|---|---|
| Audit | `jobs/1-audit.md` | sound documents, contracts, symbol index, and live code-map slices |
| Remove | `jobs/2-remove.md` | one PR per unread artefact type, proposing deletion |
| Review | `jobs/3-review.md` | one PR per decision renewed or retired |
| Sweep | `jobs/4-sweep.md` | one PR per split answer, pinned and dated |
| Instructions | `jobs/5-instructions.md` | a coverage report, safe mechanical repairs, and owner-decided semantic findings |

Instruction audits may read other jobs and skills as audit material; the selected
job controls the procedure, not the evidence it may inspect.

## The rule that governs every job

**One small PR per finding, never one sweeping rewrite.** A run that turns up
five findings opens five PRs. Each is reviewable on its own, and each is
revertable on its own without touching the other four.

Template-owned `agent-ready-*` skills, including this skill and its job files,
are not garden findings. Their line counts are report-only. Never edit, split,
compact, or truncate them in an application repository; report a desired
change to the agent-ready-python repository for the next template update.

## Asking

Some findings need a person's judgement, not more digging: whether a cap is
wrong rather than the document, whether debt is deliberate, whether an artefact
nobody read is truly dead. Ask the way `agent-ready-onboard` does: in prose and
never as a menu, in one batch at the end of a job, each question numbered and
carrying the evidence you derived and what you would do, so the answer is a
correction rather than an essay. Never fill a judgement call with a plausible
guess; an unanswered question is the job's output, not a blocker to work around.

## Stopping

Stop and report, rather than pushing on, when:

- a finding needs evidence a metrics record, a spec, or a decision file does
  not carry — a gap is the finding, not a guess to fill it;
- the fix is a cap raise or an artefact's retirement, both of which are a
  decision record only a human signs;
- the same failure repeats without new evidence or a changed hypothesis, which
  is more often a contract or spec problem than a documents problem.

Run `agent-ready caps` and `agent-ready skills` before opening any PR that
touches a capped document or a skill body. Both runtimes run the same checks
the same way; nothing in this skill depends on a feature only one of them has.

## Verification feedback

At entry and job completion, read only `Cadence state` in `docs/VERIFICATION.md` and the guide’s
`Routine cadence check` section.
Load `docs/how-to/improve-verification.md` when due, unknown, pending, or changing verification. This commit-based invitation is independent
of the garden cadence. Use existing evidence, consolidate unattended invitations,
and keep optional improvement proposals separate from authorised garden repairs.
