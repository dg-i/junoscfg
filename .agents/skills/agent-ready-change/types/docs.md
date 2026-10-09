# Documentation-only change

Type `docs` changes documents, not runtime code, tests, executable
configuration, or behaviour specs. Documentation accompanying a behaviour
change stays in that change. Set `skip_specs: true`; the lane gate restricts
product edits to document formats and requires `docs-plan.md`.

## Phase 1 — Intent

The proposal names the reader, the task the documentation must enable, the
correct documentation home, and the authoritative sources. The normal intent
approval and evidence ledger apply.

## Phase 2 — Plan

Do not build a code-map slice or invent a behaviour delta. Create `docs-plan.md`
from `openspec/schemas/agent-ready/templates/docs-plan.md`. Name each affected
document and the code, configuration, specification, or external source behind
its claims. Define checks for applicable links and anchors, commands and
examples, referenced paths, terminology, Diátaxis placement, and rendered
output. "Not applicable" carries a reason. The human approves the plan. The
common OpenSpec graph is type-blind; codemap and specs are not obligations.

## Phase 3 — Design

Skip. Retype as `new-dependency` if the documentation toolchain changes.

## Phase 4 — QA design

Put one verification task in `tasks.md` for every applicable `docs-plan.md`
check, with the exact command or inspection and expected result. Run useful
baseline probes and record failures; absence of new prose need not fail. Write
no product documentation. The human approves the QA tasks.

## Phase 5 — Change and verify

Edit only named documents and assets. Execute every QA task and record evidence:
commands and examples run against the checked `HEAD`; local links, anchors, and
paths resolve; terminology and placement match their homes; the rendered result
serves the reader's task. Use the project's builder or preview where available.
Run the normal full checkpoint: it retains repository and document gates but
skips the application test adapter. Tick verification and change tasks; leave
review and metrics open.

## Phase 6 — Review

In a fresh session read `docs-plan.md`, its sources, the rendered documents, and
the diff, in that order. Report inaccurate claims, commands or examples that do
not work, broken references, missing steps, terminology drift, wrong placement,
duplicated facts, and failure of the reader's task. Re-run mechanical QA and
independently sample claims against sources. Record what could not be checked.
Edit no product document. Write the verdict and tick the review task.

## Phase 7 — Archive

There is no delta or code-head distinction. Capture metrics against the commit
containing reviewed documents and QA evidence, review them, tick metrics, and
run the lane gate. Ignore the type-blind codemap and specs status entries. Merge,
then run `npx --yes @fission-ai/openspec@1.13.0 archive <slug> --yes --skip-specs`
and commit the archive-only move.
