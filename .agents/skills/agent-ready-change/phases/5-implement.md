# Phase 5 — Implement

## Outcome

Every task in `tasks.md` ticked, the tests of phase 4 green, the fast set and
the slow set green, and nothing in the diff the proposal did not ask for.

## Process

1. `openspec instructions tasks --change <slug>`, then write `tasks.md`: tests
   first, then implementation, in steps an interrupted session can resume.
2. Before touching a module, read its contract and its block in the slice.
   Read a named symbol alone with `agent-ready codemap show <pkg.mod.symbol>`,
   which prints the span the index records, rather than the file around it.
3. Prefer an existing helper over a new one. The slice names them.
4. Run the fast set with `pre-commit run --all-files`, then the slow set in
   one command, `agent-ready check --base origin/main`, which runs every gate
   the pull request will meet, the lane gate among them, and `openspec
   validate <slug> --strict`.
5. Tick each task as it lands. `openspec status --change <slug>` shows what
   remains.

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
`agent-ready codemap check`.

## Stage

Fail loudly in alpha: no fallback, because a fallback hides whether the
concept works. Degradation only where a requirement names it, after alpha. A
bug inside the fix-lane caps is fixed in the fix lane in every stage; one
outside them is, under alpha, a question about the concept first. Rename to the
settled name inside the pivot in alpha; never without deprecation in release,
where the patch is minimal and a rewrite is a design.

## Approval

None here. The review is the next phase, in a fresh session.
