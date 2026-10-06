# Type spike

A choice under research is made in a spike, never as an abstraction on main.

## The branch

A spike is a branch with no spec gate, no contracts, and an expiry date in its
proposal. The lane gate refuses to merge the branch itself. It is deleted when
its outputs merge; git keeps it, and nothing stays on disk to anchor on.

## The outputs

They reach main on one separate standard-lane change, cherry-picked from the
spike:

- a decision record with at least two options considered and the observed
  reason the loser lost;
- a toolbox rejected entry with the date;
- the spec delta for the winner.

The winner is then implemented by a standard change in a fresh session that
reads the spec and the decision and never opens the spike, for the reason
review starts fresh: context anchors on the code it has seen.

## Approval

The human approves the decision record and the delta on the standard-lane
change; the spike branch is never approved, only expired.
