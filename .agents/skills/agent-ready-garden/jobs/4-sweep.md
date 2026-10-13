<!-- Maintained by the agent-ready template. Local edits can conflict with updates.
See docs/how-to/template-ownership.md before editing; review every update diff. -->

# Sweep

## Outcome

One PR per split answer found, carrying its pin and a dated decision
record. A smear (many compensations for one upstream gap) and plain
duplication go into the batch of questions for the human, never into a PR.

## What a split answer is

One question the code answers in two or more places, two branches of one
function included, whose answers differ in what they can do, not in how
they are written. It is not plain duplication: each side reads fine alone,
and the gap shows only when someone needs the capability one side lacks.
Five-part signature:

- one question, several answerers
- capability differs, not style: an override, a parameter, a fallback, an
  error path one side has and the other lacks
- nothing forces agreement: no shared helper, table, type or test drives both
- asymmetric: one side gained a feature, the other was never updated
- the symptom is "it works here but not there": a documented option one
  path honours and another silently ignores

## The questions

Work from questions, not grep patterns. The job always carries:

1. Where a file or resource lives, and who may redirect it.
2. How a thing is written, and how the same thing is read back.
3. What counts as valid, empty, absent, or unknown, and what marks a list
   of allowed values as open rather than exhaustive.
4. How a name is normalised, escaped, quoted, or compared.
5. What is cached, keyed on what, and invalidated when.
6. Which errors are caught, and which are allowed to escape.
7. How a path or a key is resolved against a schema.

Plus this repository's own, `questions` under `[tool.template.garden]`.

## Scope

Where `swept` under `[tool.template.garden]` is absent, the whole codebase.
Otherwise, the files the diff since `swept` touches, widened by one import
edge in each direction from the import map `agent-ready codemap build`
writes under `.agent-ready/codemap/`.

## Process

For each question:

1. Find every place in scope that answers it.
2. Compare the answers for a capability difference: an override, a
   fallback, a parameter, an error path.
3. Demonstrate the difference by running it, not reading it — "setting X
   changes behaviour here and is ignored there" beats any amount of reading.
4. Check whether a test drives both sides against the same expectation, and
   say so; that absence is usually why the split survived.
5. Report every demonstrated gap. One that makes a documented promise true
   of one path and false of another gets a PR; the rest go in the batch.

Rank by severity. Where a split is suspected but cannot be demonstrated,
name the experiment that would settle it; never pad the list.

## The PR

Each PR carries the pin of onboarding phase 3's shape, never the fix: each
answerer's behaviour pinned as usual, and one test that drives every
answerer with the same input, marked `xfail(strict=True)` with a reason
naming a decision record. `agent-ready scaffold decision <slug>` writes the
record; fill it from the finding, `status: proposed`, the answerers as its
scope, the test id as `enforced-by`, and the `review-by` you propose as the
expiry, so the PR review is the human's signature. While the answers differ
the test reports xfail, never a pass; once they agree it passes, which
strict mode fails, so the change that fixes the split removes the marker
and closes the record together. The fix runs through `agent-ready-change`,
never through this job.

## After the run

- Append a finding's question to `questions` when it is not among the
  seven and not already listed.
- Propose a question's retirement in the batch when its answer has one
  named home and every sibling contract carries a precedent pointer to it;
  the human retires it, which keeps the list from growing forever.
- Set `swept` to the commit this run read.

## Self-check

Before the first run on this repository, and again at each release, plant
two split answers on a scratch branch and run the job against it: it must
name both. A self-check opens no PR, appends no question and leaves `swept`
unchanged, and the pair is rotated at each release so no run is calibrated
on the same two.

Every report ends with one line on what the sweep could not see: files
outside the diff and its neighbours, a second reader two import edges away,
behaviour that depends on input this repository cannot commit, and a
resource reached through a path built from `__file__`, which no search for
the question's words finds.
