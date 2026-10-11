# Phase 5 — Implement

## Documentation-only route

Type `docs` follows phase 5 in `types/docs.md` and stops before the code route
below.

## Outcome

Every test and implementation task ticked, review and metrics still open, the
phase-4 tests and full checkpoint green, and no unrequested diff. The continuous
Builder owns specification refinement, implementation, and fixes.

## Process

1. Read the evidence freeze and its delta log. `npx --yes
   @fission-ai/openspec@1.13.0 instructions tasks --change <slug>`,
   then write `tasks.md`: tests first, implementation second, and the shipped
   review and metrics lifecycle tasks last. An interrupted session resumes
   here; phase 5 never ticks the lifecycle tasks.
2. Before touching a module, read its contract and slice block. Read a named
   symbol with `uv run --locked --group dev agent-ready codemap show
   <pkg.mod.symbol>`, which prints the recorded span rather than its whole file.
3. Prefer an existing helper over a new one. The slice names them. A
   layering block is a move to the first answerer's layer or one below,
   never a copy, and the importing module's contract gains a precedent
   pointer to the home.
4. While editing, run the named phase-4 acceptance tests or the affected test
   files; record command and test duration in workflow telemetry. Tick the test
   and implementation tasks, commit code, tests, and the
   live change folder, and require `git status --short` to be empty. At the
   pre-review checkpoint run `uv run --locked --group dev --with griffe --with
   tach --with towncrier --with vulture agent-ready check --set full` once.
   It reads the local change base and includes pre-commit, the application test
   adapter, every pull-request gate, the lane gate, and strict OpenSpec
   validation. Do not run standalone pre-commit or the full application suite
   beside it on an unchanged tree. Record the command and checked `HEAD` in
   `tasks.md`. The explicit default is one full check before review and none on
   an unchanged tree. Run `agent-ready fields` and `agent-ready caps` before
   committing that record. The checkpoint remains valid
   across review, metrics, and evidence-only edits; runtime code, tests,
   generated artifacts, or their configuration invalidate it.
   For several coherent tasks, run targeted tests as each lands and take one
   full checkpoint after the last. Independent changes never share a checkpoint.
   A declared expensive tier runs once when the diff touches its paths, or once
   at a batch boundary for independent changes sharing the exact combined input;
   never per review-fix round. Reuse a cache only when corpus, configuration,
   tool version, and relevant commit match. A cache never replaces a gate.
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

## Classify failures

Classify a failure before retrying. An execution, collection, or environment
failure permits one evidence-backed repair and rerun; if blocked, report it,
because tooling is not semantic evidence against a spec. Diagnose and fix an
executed assertion failure once. If it repeats, challenge approved criteria only
when evidence implicates them; otherwise report the implementation blocker. Do
not make a blind third attempt or weaken the oracle. Record retries,
regenerations, stalls, and durations; zero requires an observed event source.

## Specification challenges

A challenge goes in `openspec/changes/<slug>/review.md` with `Artifact`,
`Counterexample`, `User impact`, `Proposed correction`, and `Decision`; the
owner decides, and only a safe reversible action may proceed while pending.
A concrete counterexample may justify minimal reads outside `codemap.md`'s
slice. Record each extra path as its own row in the existing Field/Value table
in `openspec/changes/<slug>/metrics.md`:
`| Context expansion: <path> | <reason> |`. The archive metrics writer
preserves these rows. Apply phase 2's explicit slice-refresh triggers and keep
`uv run --locked --group dev agent-ready codemap check`.
Run the evidence-freeze delta consistency check for every new instruction or
counterexample before changing affected code, criteria, or tests.

## Stage

Fail loudly in alpha: no fallback, because a fallback hides whether the
concept works. Degradation only where a requirement names it, after alpha. A
bug inside the fix-lane caps is fixed in the fix lane in every stage; one
outside them is, under alpha, a question about the concept first. Rename to the
settled name inside the pivot in alpha; never without deprecation in release,
where the patch is minimal and a rewrite is a design.

## Approval

None here. Risk decides whether phase 6 invokes a fresh isolated Reviewer or
records its omission; the Builder progresses automatically.
