# Review

Fresh agent session, read-only, against `v0.6.32`. This change loosened what
junoscfg accepts in nine places, so the review hunted over-acceptance.

## Confirmed exact

7,097 lines = 7,093 `set` + 4 `deactivate`; 21 rejected at 0.30%, per device
12/0/9; residuals exactly `hop-limit` 18, `analyzer` 2, `dump-on-panic` 1;
corpus 100 to 106 of 116. Every node count — 5,808 presence lists across 193
names, 3,456 oneliner, 108 flat-dict, 46 flat-entry, 6,436 positional-key, 135
transparent with one non-nokeyword — exact.

## Findings

1. **The either-order rule leaked across merged rules.** `either_order` was
   decided per node and written per merged rule: 2,094 qualifying nodes landed
   in 52 rules, 16 of which also carried alternatives from nodes that did not
   qualify — 11,676 child settings pulled in front of an entry name.
   `interface__list` was the worst, 6 qualifying nodes against 1,050 that
   were not. `set interfaces mtu 9192 ge-0/0/0` and `set protocols bgp group
   G neighbor peer-as 64496 10.0.0.1` validated. **Fixed in v0.7.0** by giving
   either-order nodes their own rule, the way `__list` already solves this.
2. **`QUOTED_OR_VALUE` on every leaf widened quotable slots 82 to 11,855**, a
   145x widening the record costs at nothing. Mutating the 619 lines both
   grammars accept: 70.4% of "quote the last value and add words" mutants
   still validate, against 1.6% before. **Partly fixed in v0.7.0**: scoping by
   type tightened 1,225 slots, but the measure moved only to 70.3%, because
   124,227 of 179,773 leaves carry no type at all. Recorded there as an open
   non-goal rather than claimed closed.
3. **The "507 to 21" baseline is measured from inside the change.** From the
   parent commit with its own stripper: 6,484 of 7,097 rejected, 91.4%. The
   507 figure reproduces at `f75c01a`, the change's *third* commit. The real
   before/after is 91.4% to 0.30% — the record understates the work by 12x,
   and a reviewer re-measuring from the parent gets a number that looks
   nothing like it.
4. **`tasks.md` 1.2 is checked and names nine adversarial commands that exist
   nowhere in the repository.** This is the exact failure `test_set_corpus.py`
   was created to end. Open: either commit them or uncheck the task.
5. `flat-dict`/`flat-entry` emit an unbounded `+` run — `within 1800 trigger
   after 1 bogus garbage here` validates. Recorded, not fixed.
6. The bare-`set` early return accepts `set apply-flags replace` and
   `deactivate apply-groups foo`, beyond what the record justifies.
7. `docs/guide/validation.md` said 104 accepted (it is 106) and still listed
   policy algebra as a known over-rejection, which `scope-policy-expression`
   had fixed. **Both fixed in v0.7.0.** `tasks.md` 1.1 says four fewer
   rejections; it is six.
8. Its `proposal.md` non-goal still names `accepts-bracket`, a term
   `symmetric-structure-tree` retired, and its commit asserts that flag was
   set by `_fix_policy_algebra` — which matched nothing in four releases.

## Resolution

Every headline number is true and reproduces. The defects are in what the
record *omits*: a real over-acceptance regression (1, fixed), an unpriced 145x
widening (2, partly fixed and now recorded), a baseline that flatters nothing
but confuses everyone (3), and a checked task naming a test that does not
exist (4). 4, 5, 6 and 8 are left open and recorded.

## Owner acceptance

The owner asked for the open changes to be archived (2026-10-08) and, shown
the findings in summary, chose to fix the blockers and the over-acceptance
before archiving. They did not review each finding individually. Everything
recorded as fixed was fixed in `v0.7.0` (`validate-own-output`); everything
recorded as accepted is accepted on that basis.
