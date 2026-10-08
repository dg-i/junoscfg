# Review

## Outcome

One batch of renew, retire, or keep-open questions, one per decision whose
`review-by` falls before the next scheduled garden run, delivered before CI
would fail on the expiry against an unrelated feature PR.

## Process

1. Read every file in `docs/decisions/`; `agent-ready decisions` already lists
   the ones whose `review-by` has passed. Collect those and the ones whose date
   falls before the next run — the next release, or one month out, whichever is
   sooner. A toolbox trial entry with a `review-by` in that window is a
   decision in this batch too.
2. For each, gather what has actually happened since it was accepted: what its
   `enforced-by` check has recorded, whether a baseline under it has shrunk,
   held, or worsened, and whether the area it covers has changed.
3. Bring all of them to the human as one batch, not one question per decision.
   For each: state the decision, the evidence gathered, and a recommendation —
   one of:
   - **Renew.** Nothing about the decision needs to change, only its
     `review-by` date.
   - **Retire.** The decision no longer applies; name what replaces it.
   - **Keep open.** The evidence does not settle it; this one needs the
     human's own read, not a recommendation from you.
4. On an answer, open one PR per decision, updating `review-by` or `status`
   accordingly and running `agent-ready render decisions` for the index. Five answered decisions are five small PRs, so a reviewer
   approving the renewal of one is not asked to also vouch for the other four.

## Why this runs on a schedule

`review-by` expiry already fails in CI. Waiting for that failure means the
first person to hear about it is whoever opened the next feature PR that
happens to touch the area — the wrong moment to be relitigating a decision.
Running this job on the garden's schedule means every expiry is renewed,
retired, or flagged before it can surprise anyone.

## A cap-raise decision arriving from the audit job

A cap raise proposed by `jobs/1-audit.md` names, in its decision line, the
measurement that justifies it. Fold it into this run's batch like any other
decision needing a human signature, rather than opening it as a separate,
smaller review cycle.
