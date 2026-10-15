<!-- Maintained by the agent-ready template. Local edits can conflict with updates.
See docs/how-to/template-ownership.md before editing; review every update diff. -->

# Phase 5 — Implement

## Documentation-only route

Type `docs` follows phase 5 in `types/docs.md` and stops before the code route below.

## Outcome

Every test and implementation task ticked, review and metrics still open, the phase-4 tests and full
checkpoint green, and no unrequested diff. The continuous Builder owns specification refinement,
implementation, and fixes.

## Process

1. Read the evidence freeze and its delta log. `npx --yes
   @fission-ai/openspec@1.13.0 instructions tasks --change <slug>`,
   then write `tasks.md`: tests first, implementation second, and the shipped
   review and metrics lifecycle tasks last. An interrupted session resumes
   here; phase 5 never ticks the lifecycle tasks.
2. Before touching a module, read its contract and its block in the slice.
   Start a named lookup with `uv run --locked --group dev agent-ready codemap
   show <pkg.mod.symbol>`. Read the containing module and nearby tests whenever
   control flow, shared state, imports, comments, or error handling affect the
   change; phase 2 defines which context is automatic and which is expansion.
3. Prefer an existing helper over a new one. The slice names them. A
   layering block is a move to the first answerer's layer or one below,
   never a copy, and the importing module's contract gains a precedent
   pointer to the home.
4. While editing, run the named phase-4 acceptance tests or the affected test
   files; record command and test duration in workflow telemetry. Tick the test
   and implementation tasks, commit code, tests, and the
   live change folder, and require `git status --short` to be empty. At the
   pre-review checkpoint run `uv run --locked --group dev agent-ready check --set full` once.
   It reads the local change base and includes pre-commit, the application test
   adapter, every pull-request gate, the lane gate, and strict OpenSpec
   validation. Do not run standalone pre-commit or the full application suite
   beside it on an unchanged tree. Record the command and checked `HEAD`:
   under `strategy-a/1` the checkpoint's verification event is that record;
   otherwise add it to `tasks.md`. The explicit default is one full check before
   review and none on an unchanged tree. Run `agent-ready fields` and `agent-ready
   caps` before committing that record. Its command evidence remains valid across
   task ticks, that record, review, metrics, and evidence-only edits; runtime code,
   tests, added, removed or reworded tasks, generated artifacts, or their
   configuration invalidate it. Record and lifecycle gates still rerun.
   For several coherent tasks, run targeted tests as each lands and take one
   full checkpoint after the last. Independent changes never share a checkpoint.
   A declared expensive tier runs once when the diff touches its paths, or once
   at a batch boundary for independent changes sharing the exact combined input;
   rerun whenever its evidence is invalidated, including a review-fix round.
   Reuse evidence only when its authority-specific input and execution identity
   matches validated successful proof. Relevant corpus, configuration, executable
   dependencies and policy participate; version or commit labels alone never
   establish success or invalidation. A cache never replaces a gate. Cheap
   readiness, lane, specification and instruction-integrity checks precede hooks,
   tests and qualification. Repair failed admission before launching expensive work.
   Preserve valid declared-tier and content proof while rerunning affected gates;
   bookkeeping commits alone do not call for another complete suite.
5. Tick each test and implementation task as it lands. `npx --yes
   @fission-ai/openspec@1.13.0 status --change <slug>` shows the common artifact
   graph; `tasks.md` is the lifecycle authority.
6. A function that is the inverse of one that exists is written beside it:
   one table is the only source of field names for both sides, and the
   round-trip of phase 4 is what proves the pair. A second table or a
   hand-written remainder is a split answer: a design question in the
   proposal, never a local copy.
7. Regenerate only artifacts invalidated by the current delta and do it once
   after the source edit settles. A second regeneration for the same unchanged
   delta is a stall to diagnose and record, not a reason to loop. After every
   commit, update the resume point and last valid test/checkpoint evidence.

## Stage

Fail loudly in alpha: no fallback, because a fallback hides whether the concept works. Degradation only where
a requirement names it, after alpha. A single-failure bug is fixed in the fix lane in every stage; a broader
bug is, under alpha, a question about the concept first. Rename to the settled name inside the pivot in alpha;
never without deprecation in release, where the patch is minimal and a rewrite is a design.

## Approval

None here. Phase 6 receives a fresh isolated Reviewer; the Builder progresses automatically.

Under `strategy-a/1`, run `agent-ready readiness` before the full checkpoint. Use
`docs/how-to/verification-evidence.md`: one checkpoint is not a ceiling on required reruns, and generated
artifacts never replace a passing command.
