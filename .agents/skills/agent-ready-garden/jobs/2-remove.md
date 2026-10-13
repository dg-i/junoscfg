<!-- Maintained by the agent-ready template. Local edits can conflict with updates.
See docs/how-to/template-ownership.md before editing; review every update diff. -->

# Remove

## Outcome

One PR per artefact type that has gone unread, each proposing its deletion and
stating plainly what would be lost. This is the only job that makes the design
shrink; every other path only ever adds an artefact.

## Process

1. List the artefact types: every glob in `[tool.template.caps]` of
   `pyproject.toml`, plus each artefact of the change schema in
   `openspec/schemas/agent-ready/schema.yaml` — proposal, codemap, specs,
   design, tasks, review, metrics — counted separately, since a reader asks
   for one of them at a time.
2. Take the last 50 archived changes, or every change since the last release,
   whichever is the smaller window. For each artefact type, read `distinct
   files read per phase, by artefact type` from every `metrics.md` in that
   window.
3. A type absent from that field in every one of those records is a candidate.
   Absence for one change proves nothing; absence for the whole window is the
   finding.
4. For each candidate, open a PR that states, plainly:
   - what the type recorded, and what question it used to answer;
   - who could no longer answer that question once it is gone;
   - how to recover it from git history if the removal turns out wrong.
5. Removal is the human's decision, not this job's. The PR proposes; it does
   not merge itself, and it never deletes anything the review does not
   confirm.

## After an approved removal

Drop the type's cap from `[tool.template.caps]` and its artefact from the
change schema, remove any check that named it, and stop whatever generator
produced it. A type that leaves the
schema also leaves every place that schema is enforced — a removal that keeps
the check alive just moves the artefact from unread to unreadable.

## What this job is not

It does not judge whether a type *should* be read, only whether it *was*. A
type nobody has read yet because the workflow just adopted it is not a
candidate; the 50-change or one-release window has to have actually run.
