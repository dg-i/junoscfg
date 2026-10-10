<!-- Complete at the end of phase 2. Later instructions or evidence require a delta consistency check before affected work continues. -->

## Resolved instructions

- Scope (C1, owner-resolved 2026-10-10 "use the default and continue"): the five
  reconstructed measures in `instruction-integrity.md` and the telemetry exercise.
- Lane: type `docs`, `skip_specs: true`, zone `anonymize` (C10), assurance `balanced`, risk
  floor high. Documentation-only route for phases 2 to 7; phase 3 skipped.
- Owner limits: no product code, generated artifact, test behaviour, `pyproject.toml` or
  template-managed skill edit; no second telemetry collector; no merge, tag, archive,
  publish or release; no device-probe timing claim.
- Contracts stay at or under 30 lines (C5); the spec edit travels as `main-spec-edit.md`,
  reviewed in phase 6 and applied verbatim by the finalizer in phase 7, because OpenSpec
  refuses a `specs/` delta beside `skip_specs` (C4); C6 and C7 are recorded, not edited.
- The untracked review is evidence of intent only and is cited by no deliverable (C3).

## Requirements

- `openspec/specs/conversion/entry-keys/spec.md`, "A statement the reader cannot complete is
  kept whole": MODIFIED for traceability, behaviour unchanged; text frozen in
  `main-spec-edit.md` as the sibling live delta's owner-approved wording (commit 211a165,
  never applied to the main spec) plus the five `TestAMetaCommandIsNeverPartiallyApplied`
  ids (challenges S1 to S3). No other requirement changes.

## Evidence

- The 24 ids of `main-spec-edit.md` collect as 60 nodes (`uv run pytest --collect-only -q`,
  2026-10-10); the phase-4 challenge found one dead id in `docs-plan.md` (S4, corrected);
  task 1.2 re-collects every id the deliverables cite and expects exit 0, not a count.
- Tier flags and help text: `tests/conftest.py` `pytest_addoption`; the schema tier is
  `tests/test_schema_data.py` (`pytestmark = pytest.mark.schema`).
- Contract lengths today: display 27, validate 24, convert 30, anonymize 28 lines; cap 30.
- Current tier section: `docs/architecture/developer-guide.md` lines 726 to 750.
- `agent-ready fields` exits 1 on the sibling live change `identifier-key-fields`
  (no `assurance`); it passes for this change's `.openspec.yaml`. Pre-existing on `master`.
- `openspec validate` passed at phase 1 with `skip_specs` set.
- Repository graph updated in `graphify-out/` (7,245 nodes) before the audit-style reads.

## Non-goals

- Product code, generated artifacts, test behaviour, `pyproject.toml`, template-managed skill
  files, a second telemetry collector, device-probe timing.
- The guide's stderr and "safe fallback" sentences (C7) and the Hypothesis mismatch (C6).
- Merge, tag, archive, publish, release.

## Acceptance criteria

- Every `docs-plan.md` QA check has a `tasks.md` verification task that passes with recorded
  evidence against the checked `HEAD`.
- `agent-ready reconcile` exit 0 with the delta live; `agent-ready caps` passes; strict MkDocs
  build clean; markdownlint clean on changed files; `git diff --check` clean; one full
  `agent-ready check --set full` at the pre-review head.
- Independent Test/Challenge (high floor): a fresh agent challenges the QA tasks before
  implementation and independently executes them and samples claims against sources after.
- A genuinely fresh Reviewer (phase 6) returns a verdict; findings are corrected and re-read.
- `workflow-telemetry.json` imports through `agent-ready metrics` with no estimated value.

## Performance expectations

none, because no runtime code changes; the tier mapping cites the existing timing guard and
the recorded large-case baseline rather than measuring anything new.

## Outstanding decisions

none for this change. One repository correction outside it is open for the owner: the
sibling change's missing `assurance` makes the `fields` gate, and so the full checkpoint,
fail until it is answered there or that change is archived.

## Execution and checkpoint

- Assurance preference: balanced
- Risk floor: high, with evidence: `src/junoscfg/anonymize/CONTRACT.md` lies under the red
  zone's paths, and the documents span every domain.
- Roles required: Builder (this session); independent Test/Challenge (fresh agent, QA plan
  challenge and execution); fresh Reviewer (`junoscfg-reviewer`, `claude-fable-5-1`, high
  effort, no Builder report); Finalizer (`junoscfg-finalizer`, bounded housekeeping only).
- Resume point: phase 4 (QA tasks); last valid evidence is the phase-2 commit holding this
  freeze, `docs-plan.md` and the delta.

## Delta log

<!-- Append source, change, consistency result, invalidated work, and rerun required. -->

- Freeze established: the phase-2 commit on `change/agent-guidance-gates-and-contracts`
  (`docs-plan.md`, `evidence-freeze.md`, `main-spec-edit.md`), on top of phase-1 commit
  f3bd902 and phase-0 commit 384acc3.
- 2026-10-10, phase 2: the lane gate refuses to run beside the owner's two uncommitted files;
  the checks will run with them stashed and restored (instruction-integrity delta log).
- 2026-10-10, phase 4, independent Test/Challenge (`test-challenge.md`): seven challenges S1
  to S7 recorded in `review.md`, each with the interim safe action; eleven checks added as
  tasks 1.11 to 1.21 and tasks 1.1 to 1.10 tightened. Invalidated: the frozen clause of
  `main-spec-edit.md` (replaced by the sibling's wording plus ids), docs-plan rows for the
  display, validate, convert and timing claims and one dead test id (corrected), the "60
  nodes" evidence line (reworded). Reruns required: every phase-4 check runs after the
  edits; the challenger's behaviour probes are re-run in 1.16.
- 2026-10-10, phase 4, repository state: the owner committed 01efe85 ("Update garden
  instruction audit modules", two template-managed files under
  `.agents/skills/agent-ready-garden/`) on this branch between phase 0 and phase 1, and a
  second untracked review (`docs/reviews/2026-10-10-instruction-audit.md`) appeared. The
  owner works in this checkout concurrently, so no stash: every gate runs in a detached
  worktree of the checked commit. The pull-request range now carries 01efe85; the owner may
  move it to `master` or leave it. Consistent with the freeze; nothing else invalidated.
- 2026-10-10, phase 5: the owner asked for the garden audit output to be committed; 306233b
  adds `mkdocs.yml` and a review page to the range, which the docs lane gate also refuses.
  The owner then accepted moving both commits to `master` and answering the sibling's
  `assurance` as balanced; the permission classifier blocked the Builder from committing on
  `master` or editing the sibling change, so the owner runs those commands. Nothing of this
  change is invalidated; the full checkpoint reruns on the rebased head.
- 2026-10-10, phase 6: fresh review (two Medium, six Low, new challenge S8) and the
  post-implementation challenge (19 checks re-run, 0 mismatches; 20 claims sampled, 2
  failed, 4 partial). Fix pass applied as recorded in `review.md`; invalidated and re-run:
  tasks 1.1, 1.2, 1.4, 1.6, 1.8, 1.11 to 1.17, 1.19 to 1.21 on the fix commit; the same
  isolated Reviewer re-reads the corrections.
- 2026-10-10, phase 7: the owner authorised moving the garden commits and answering the
  sibling's `assurance`; the branch was rebased onto master 7117e3a. The docs lane gate
  refuses a behaviour spec in the range, so the reviewed main-spec edit (C4) lands on
  master as its own commit after the merge (from e6a0c2a). The owner also directed the
  merge, which records their acceptance of the interim actions on S1 to S8. Full
  checkpoint green at d1cc626; nothing else invalidated.
