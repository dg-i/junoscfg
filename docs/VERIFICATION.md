# Testing and verification

Application-owned record. Initialise during onboarding or the first refresh
that supplies this file. Follow `docs/how-to/improve-verification.md`.
UNMEASURED means evidence is unavailable, not that a requirement is satisfied.

## Cadence state

- Integration branch: UNSET — choose the application's integration branch.
- Interval: 10 first-parent commits.
- Cadence anchor SHA: UNSET — initialise at the observed integration head.
- Last reviewed SHA: NONE.
- Last declined SHA: NONE.
- Pending assessment head: NONE.
- Invitation status: not due; initialise before counting.

## Feedback stages

Replace each provisional row with commands, comparable measurement conditions,
revision/evidence links, observation count and tolerance. For unused stages,
record the reason. Keep baseline, accepted budget and target separate.

| Stage | Commands / required risks | Observed baseline | Accepted budget | Target / tolerance | Evidence / conditions |
|---|---|---|---|---|---|
| Local fast | UNSET | UNMEASURED | UNSET | UNSET | UNMEASURED |
| Pull request | UNSET | UNMEASURED | UNSET | UNSET | UNMEASURED |
| Scheduled / release | UNSET or reason unused | UNMEASURED | UNSET | UNSET | UNMEASURED |

## Quality dimensions

| Dimension | Current evidence / gaps | Target / success check |
|---|---|---|
| Behavioural assurance | UNMEASURED — critical behaviours, failure paths and detecting checks | UNSET |
| Reliability | UNMEASURED — flakes, reruns and diagnostic waste | UNSET |
| Corpus organisation | UNMEASURED — locations, levels, fixtures, independence, duplication, readability and ownership | UNSET |

## Selected improvements and accepted gaps

For each selected item: stable ID, problem/risk, owner, action, expected benefit,
success check, review point, evidence and observed result. Link independent work
to the authoritative backlog instead of duplicating its status. Record explicit
owner acceptance of regressions or budget/target revisions with reasons.

## Review outcomes

Append compact entries: date, assessed SHA, evidence links, observations,
agent judgment, user feedback or decline, decisions and prior improvement results.
Keep raw logs in their existing evidence source. Preserve historical decisions;
keep the tables and cadence state above current.
