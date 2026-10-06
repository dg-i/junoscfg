# Audit

## Outcome

Every document is at or under its cap, and free of duplicates, dead pointers,
contradictions between a spec and a contract, unused helpers, and contract
prose outside its permitted kinds of line; every spec passes OpenSpec's
validation with a Purpose someone wrote; every `stage-up` checklist is
answered.

## Size

Run `agent-ready caps`. For each document it reports over its cap, work this
ladder in order, stopping the moment the document is at or under the target
the failure message names:

1. **Lossless.** Move duplicated or misplaced content to the artefact that
   owns it. This alone clears most findings, because a document over its cap
   is usually carrying a fact that belongs elsewhere, not saying too much.
2. **Compact.** Cut restated interface facts, resolved ambiguity, and dead
   pointers — see Soundness below; running that check first often shrinks the
   document before you reach this rung.
3. **Split or remove.** A spec splits by capability, never truncated. Nothing
   else in the template is truncated either: a document that cannot be made
   smaller without losing a fact is not over its cap, it is under-served by
   the cap.

If no rung reaches the target, the conclusion is that the cap is wrong, not
that the document needs deeper cuts. Put a cap-raise decision record in the
batch for `jobs/3-review.md` to carry forward, naming the measurement that
justifies the new number, and stop cutting.

## Soundness

Read specs, contracts, and their pointers together, and raise one finding for
each of:

- **Duplicate content.** The same fact stated in two documents: keep it in the
  one that owns it, replace the other with a pointer.
- **Dead pointer.** A pointer that resolves to nothing: fix it, or drop it if
  the target is gone for good.
- **Contradiction.** A spec and a contract that disagree: this is a design
  question, not yours to settle by picking one. Quote both passages and put it
  in the batch for a human.
- **Unused helper.** A helper the code-map slice shows nothing else calling:
  propose its removal in its own small PR, separate from the document fixes.
- **Spec validation.** Run `openspec validate --specs` and `openspec validate
  --archived`. A Purpose still at the placeholder `archive` wrote is a finding:
  draft it from the capability's requirements and have the human confirm it. An
  archived change with open tasks is a question for the human, never a tick.
- **Contract prose out of shape.** A `CONTRACT.md` line that is not an
  invariant naming a check id, a precedent pointer that still resolves, or a
  "not for" line whose ambiguity persists: cut it. A "not for" line whose
  ambiguity has gone is deleted outright, never kept as a standing note. A
  line saying the module is deliberately unpinned is not a kind of line either:
  that fact is a `stage` override on the module's zone, so move it there, then
  cut the line.
- **Stage-up checklist.** Where the `name` in `[tool.template.stage]` changed
  since the previous garden run, or since `onboarded` where no run precedes
  this one, read that change's `checklist.md` under `openspec/changes/archive/`.
  A stage declared with no `stage-up` change has no checklist, which is itself
  the finding; an unanswered item is a finding; an answer the repository
  contradicts is a question for the human, not a fix.

## PRs

Group by document: one PR per document touched, carrying every fix that
document needs this run, so a reviewer sees one coherent diff rather than three
overlapping ones. A helper removal is its own PR, because it touches code, not
documents.
