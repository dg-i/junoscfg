# Phase 5 — Implement

## Outcome

Every test and implementation task in `tasks.md` ticked, its review and metrics
tasks still open for phases 6 and 7, the phase-4 tests and recorded full
checkpoint green, and nothing in the diff the proposal did not ask for.

## Process

1. `npx --yes @fission-ai/openspec@1.13.0 instructions tasks --change <slug>`,
   then write `tasks.md`: tests first, implementation second, and the shipped
   review and metrics lifecycle tasks last. An interrupted session resumes
   here; phase 5 never ticks the lifecycle tasks.
2. Before touching a module, read its contract and its block in the slice.
   Read a named symbol alone with `uv run --locked --group dev agent-ready
   codemap show <pkg.mod.symbol>`,
   which prints the span the index records, rather than the file around it.
3. Prefer an existing helper over a new one. The slice names them. A
   layering block is a move to the first answerer's layer or one below,
   never a copy, and the importing module's contract gains a precedent
   pointer to the home.
4. While editing, run the named phase-4 acceptance tests or the affected test
   files. Tick the test and implementation tasks, commit code, tests, and the
   live change folder, and require `git status --short` to be empty. At the
   pre-review checkpoint run `uv run --locked --group dev --with griffe --with
   tach --with towncrier --with vulture agent-ready check --set full` once.
   It reads the local change base and includes pre-commit, the application test
   adapter, every pull-request gate, the lane gate, and strict OpenSpec
   validation. Do not run standalone pre-commit or the full application suite
   beside it on an unchanged tree. Record the command and checked `HEAD` in
   `tasks.md`, then commit that evidence-only edit. The checkpoint remains valid
   across review, metrics, and evidence-only edits; runtime code, tests,
   generated artifacts, or their configuration invalidate it.
5. Tick each test and implementation task as it lands. `npx --yes
   @fission-ai/openspec@1.13.0 status --change <slug>` shows the common artifact
   graph; `tasks.md` is the lifecycle authority.
6. A function that is the inverse of one that exists is written beside it:
   one table is the only source of field names for both sides, and the
   round-trip of phase 4 is what proves the pair. A second table or a
   hand-written remainder is a split answer: a design question in the
   proposal, never a local copy.

## Classify failures

Classify a failure before retrying. Execution/tooling failures such as a wrong
invocation, collection error, or missing environment dependency permit one
evidence-backed repair and rerun. If still blocked, report the cause and
evidence; tooling failures are not semantic evidence against a spec. A semantic
failure is an executed assertion contradicting required behavior: diagnose and
fix once. If the same semantic failure repeats, challenge approved criteria
only when evidence implicates them; otherwise report the implementation blocker.
Do not make a blind third attempt or weaken the oracle. This is skill guidance,
not a runtime-enforced retry counter.

## Specification challenges

Create or update `openspec/changes/<slug>/review.md` under
`## Specification challenges` for a challenge to an approved proposal, spec,
test, or contract. Each subsection has `Artifact`, `Counterexample`, `User impact`, `Proposed correction`, and `Decision`. State the input, observed or
logically demonstrated result, violated invariant, and whether evidence was
executed or is a proposed probe. Include user impact within the declared promise
and corrected criteria/tests without inventing compatibility or robustness
requirements. Stop affected implementation, preserve approved intent and tests,
and continue unaffected work. Agents cannot approve their own proposals; the
owner records accept/reject/clarify, rationale, and evidence/reference, and
rejected challenges remain. While pending, use only the safest reversible
interpretation fixed by existing architecture and record its evidence and
interim action in `Decision`, not as approval. If none exists, behavior would
change, or effects are irreversible, report the blocker and wait. Do not merge
with an unresolved correctness challenge. Accepted corrections return through
existing spec/test approval points. See the review template.

A concrete counterexample may justify minimal reads outside `codemap.md`'s
slice. Record each extra path as its own row in the existing Field/Value table
in `openspec/changes/<slug>/metrics.md`:
`| Context expansion: <path> | <reason> |`. The archive metrics writer
preserves these rows. Refresh the slice when appropriate and keep
`uv run --locked --group dev agent-ready codemap check`.

## Stage

Fail loudly in alpha: no fallback, because a fallback hides whether the
concept works. Degradation only where a requirement names it, after alpha. A
bug inside the fix-lane caps is fixed in the fix lane in every stage; one
outside them is, under alpha, a question about the concept first. Rename to the
settled name inside the pivot in alpha; never without deprecation in release,
where the patch is minimal and a rewrite is a design.

## Approval

None here. The review is the next phase, in a fresh session.
