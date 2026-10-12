---
name: agent-ready-change
description: Run one change through the provider-agnostic phased workflow, from instruction-integrity preflight to bounded finalization. Use for every change to this repository, including fix and maintenance lanes.
---

# Change

One change is one branch, one pull request, one change folder under
`openspec/changes/<slug>/`. Invoke as `agent-ready-change <phase>`, and read
this file and the one phase file you are running. Do not read the others; they
cost tokens you will not use.

When the request contains several tasks, read `batches.md` before choosing a
lane or writing intent. It decides whether they are one coherent change or
independent changes and where review and full-check work may be shared. Do not
load it for a single task.

Every lane starts with phase 0. The standard and docs lanes then follow the
remaining phases. The docs lane takes each phase's **Documentation-only
route**. The fix and maintenance lanes follow the shorter route under **Lanes** after phase 0
and do not run the later phase files.

| Phase | File | Ends with |
|---|---|---|
| 0 Preflight | `phases/0-preflight.md` | effective instructions, assurance preference, and material decisions resolved |
| 1 Intent | `phases/1-intent.md` | the proposal, approved |
| 2 Spec and freeze | `phases/2-spec.md` | the code-map and delta, or docs plan, plus the evidence freeze, approved |
| 3 Design | `phases/3-design.md` | the design and the reuse verdict, approved; `feature` and `new-dependency` only |
| 4 Tests | `phases/4-tests.md` | acceptance tests or documentation QA, reviewed |
| 5 Implement | `phases/5-implement.md` | code or documents complete, the checks green |
| 6 Review | `phases/6-review.md` | the risk-required verdict from a genuinely fresh isolated Reviewer |
| 7 Finalize | `phases/7-archive.md` | economical housekeeping, metrics filled, the change archived |

Four types carry a body of their own, read beside the phase from intent on:
`types/stage-up.md`, `types/pivot.md`, `types/spike.md`, `types/docs.md`.

## Lanes

The change's `.openspec.yaml` declares `type`, zone, and the standing owner
`assurance` selected in phase 0; the lane and assurance policy follow.
The fix lane, type `fix`, is a ten-line proposal, one failure mode, one
regression test, and its cohesive repair, with no delta and `skip_specs: true`,
in any zone. File and line counts are review prompts, not classification: a
cross-cutting diff is still a fix when every edit is necessary for that one
failure mode, and is a standard-lane `bug` when it changes several behaviours
or responsibilities. Explicit application `[tool.template.fix-lane]` limits
still apply. Its complete route is:

1. Re-read the committed preflight and run `git status --short`; do not begin
   with governed changes outside `HEAD`.
2. Write the proposal created by phase 0, at most ten lines, and set `type:
   fix`, the zone, `assurance`, and `skip_specs: true` in `.openspec.yaml`.
   Run `agent-ready fields` and `agent-ready caps`, then commit that approved
   intent before code or tests. The common OpenSpec graph
   is type-blind: its other status entries are not fix-lane obligations.
3. Write the one regression test and watch it fail, implement the repair, and
   commit the test and code. `uv run --locked --group dev agent-ready lane`
   also runs the added test against the merge base and rejects one that passed
   there.
4. The zone's tier decides who reviews the test and diff. In a solo repository a fresh agent
   writes a lightweight `review.md` over the proposal, test, and diff; this is
   a second read, not the full phase-6 lifecycle. Apply corrections and return
   them to that reviewer.
5. Run the canonical full-check command under **The tools**. After approval, merge, then archive
   with `npx --yes @fission-ai/openspec@1.13.0 archive <slug> --yes
   --skip-specs` in a separate archive-only commit or pull request.

A fix proposal names the failure mode that remains after the fix: a repair that
turns a loud failure into a quiet wrong answer is worse than the failure. A
spike is a branch that never merges; its outputs reach main on one standard-lane
change.

The maintenance lane, type `maintenance`, is for a non-behavioural, low-risk
change such as typing, comments, formatting, instrumentation that changes no
result, or testability structure that preserves the public behaviour. It uses
the fix route without a pre-fix regression: a ten-line proposal states the
`Preserved behaviour:`, `Verification:`, and `Changelog:` lines with concrete
preservation evidence and a changelog decision; metadata
sets `skip_specs: true`; the agent makes the cohesive edit, runs the focused
evidence, receives zone-selected review, runs the canonical full check, and
archives with `--skip-specs`. A solo repository also receives the lightweight
fresh review above before the full check. Any changed behaviour, contract, dependency, compatibility
surface, or migration retypes the change into the applicable standard lane.

The docs lane, type `docs`, is for a change whose product edits are documents,
not runtime code, tests, executable configuration, or behaviour specs. It sets
`skip_specs: true`, records the reader, authoritative sources, affected pages,
and QA in `docs-plan.md`, and uses the documentation-only route in phases 2–7.
The lane gate accepts Markdown, reStructuredText, plain text, and document image
assets outside the change folder and rejects other suffixes. Documentation that
accompanies a behaviour change stays in that behaviour change. The full check
retains repository integrity and document hooks but skips the application test
adapter; the reviewed QA plan supplies the evidence application tests cannot.

## Sessions

Execution is provider-agnostic: describe roles, isolation, capability, and
evidence, never a provider's session or delegation feature as the policy. One
continuous **Builder** owns specification refinement, implementation, and
accepted fixes. It progresses automatically across every non-decision boundary
and resumes from committed change artefacts after interruption; do not ask the
owner to relay phase output. Compaction is never the checkpoint.

Independent **Test/Challenge** work runs only where the risk floor or assurance
preference requires it. A genuinely fresh isolated **Reviewer** receives the
frozen evidence, diff, tests, and contracts but none of the Builder's private
reasoning. An economical **Finalizer** performs only the bounded housekeeping
in phase 7. It cannot change product code, specifications, acceptance tests, or
review verdicts.

High risk means a red zone, security or trust-boundary work, data migration, a
declared break, a named public-surface change, or a cross-domain change. High
risk always receives independent Test/Challenge work and a fresh Reviewer at
least as capable as the Builder. `economy` adds neither role below that floor;
`balanced` adds Test/Challenge work for behavioural changes and a Reviewer for
yellow zones; `maximum-assurance` uses both for every standard or docs change.
Provider or model unavailability is recorded in the preflight and cannot be
papered over by calling the Builder independent.

After each phase, record the next incomplete phase and last valid evidence in
the change folder and commit it. Resume automatically from that checkpoint.

## The tools

OpenSpec owns the change folder. Invoke it only as `npx --yes
@fission-ai/openspec@1.13.0 ...`; invoke the check package only as `uv run
--locked --group dev agent-ready ...`. The one canonical full checkpoint
is `uv run --locked --group dev --with griffe --with tach --with towncrier
--with vulture agent-ready check --set full`; shorter forms are not workflow
commands because an existing environment may hide missing runtime tools.
Generated or vendored `openspec-*` skills do not govern changes in an
application repository: use this skill for every application repository change and use the
generic skills only to explain OpenSpec itself. OpenSpec `new change
<slug>` creates the folder under the `agent-ready` schema, `status --change
<slug>` shows the common artifact graph, `instructions <artifact> --change
<slug>` prints one template, and `validate <slug> --strict` checks it. Phase 7
applies reviewed main-spec edits while the live folder remains; after merge,
`archive <slug> --yes --skip-specs` moves the folder. `agent-ready` adds `metrics`,
`scaffold decision`, `decisions`, `render levers`, `stage`, `reconcile`, `lane`,
`retired`, and `codemap`, each named in the phase that uses it. A gap is reported, never
scripted around.

The installed `agent-ready-*` skills and their phase files are template-owned,
including this file. Their line counts are report-only in an application
repository. Never edit, split, compact, or truncate them as part of an
application change; report the desired change to the agent-ready-python
repository and let `agent-ready update` replace the installed copy.

## Specification challenges

Approved proposals, specs, tests, and contracts remain the baseline. Concrete
counterevidence goes in `review.md` under `## Specification challenges`, one
entry per challenge with `Artifact`, `Counterexample`, `User impact`, `Proposed
correction`, and `Decision`. State the input, observed or logically demonstrated
result, violated invariant, and whether the evidence was executed or is a
proposed probe. Stay within the declared promise; trust-boundary validation is
correctness, but do not invent compatibility or robustness requirements.

Stop affected work and continue unaffected work. Set `Decision` to `Pending
owner decision`; agents cannot approve their own proposals. The owner records
accept, reject, or clarify with rationale and evidence/reference, and rejected
challenges remain. While pending, take only a safe reversible action fixed by
existing architecture and record that evidence and interim action in
`Decision`. Otherwise report the blocker. Never merge with an unresolved
correctness challenge; accepted corrections return through spec/test approval.

## Asking

Ask the way `agent-ready-onboard` does: in prose and never as a menu, in one
consolidated batch for all material unresolved decisions known at that point,
each question numbered and carrying the evidence, effect, and safe default.
Do not ask about phase transitions or facts the repository establishes. Never
fill a judgement call with a plausible guess; an unanswered material question
is the phase's output.

## Stage

The declared stage in `[tool.template.stage]` sets a default each phase
reverses: alpha specifies the thinnest slice and removes rather than keeps;
beta and release deprecate before removing and declare every break in the
proposal. Each phase file carries the stage paragraph that applies to it, and
`types/stage-up.md` is the change that moves the stage.

## Stopping

Stop and report when the same failure repeats without new evidence or a changed
hypothesis, when a phase's question is unanswered, when a failing existing test
in release looks like a break, or when you are about to write a fact you cannot
point at evidence for. An evidence-driven attempt may continue when it narrows
the cause; repetition alone is not a retry counter.
Before stopping or resuming, update the checkpoint and telemetry.

## Review scope and backlog

All lanes follow `docs/how-to/review-scope.md`: freeze outcome, criteria and
exclusions before implementation; repair outcome-blocking defects and introduced
regressions wherever found. Review follow-ups cover accepted corrections and
consequences. Independent findings receive authoritative backlog dispositions;
binding obligations remain effective. No time or review-round cap applies.
