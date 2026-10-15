<!-- Maintained by the agent-ready template. -->

# Fix and maintenance

Read beside SKILL.md after phase 0; skip the standard phase files.

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
4. Leave a review task open in `tasks.md`. Commit the implementation and run
   the canonical full check before dispatching the fresh Reviewer. It reads the
   proposal, regression or preservation evidence, and diff. Required independent
   Test/Challenge work follows the shared role policy even on a short lane.
5. Record the verdict and command evidence, close the review task, and run the
   lane gate. Apply the shared verification invalidation rules after corrections. Follow **Short-lane
   closure** below; do not load standard phase files.

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
evidence, runs the canonical full check, receives fresh review, and
archives with `--skip-specs`. Every change receives the lightweight fresh review above after the full check. Any changed behaviour, contract, dependency, compatibility
surface, or migration retypes the change into the applicable standard lane.

## Short-lane closure

Resolve the application's archive, version, and integration order at preflight;
its explicit procedure governs. Otherwise, after owner acceptance, merge the
live change and make a separate archive-only commit or pull request. Before
integration, close completed tasks with evidence; leave unresolved tasks open.
Run `npx --yes @fission-ai/openspec@1.13.0 validate <slug> --strict`.
The common graph does not require omitted standard artifacts in these lanes.

Metrics are not a short-lane obligation unless the owner or application requires
them. When required, capture once while the folder is live, with full commit IDs
obtained from Git, using `agent-ready metrics <slug> --base-sha SHA --head-sha SHA`.
Review its output, then commit evidence; keep the capture head at the code commit.
Do not manufacture telemetry for absent roles or omitted phases.

With all applicable tasks complete and acceptance recorded, run `npx --yes
@fission-ai/openspec@1.13.0 archive <slug> --yes --skip-specs` in the resolved
integration order. Use the application's existing version tooling and interpreter
when a bump is required. Stop dependent commands on any failure; confirm the
version files agree before committing. Keep normal hooks enabled. Confirm the
integrated commit, required tag, and worktree status, and retain the evidence paths.
