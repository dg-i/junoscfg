# Review

Fresh agent session, read-only, against `v0.6.32`.

## Confirmed exact

11,853 and 159 land to the unit. The four `apply-*` names and
`dump-on-panic` are 0 occurrences, as substrings, across all four XSD dumps —
659 MB checked. `AGENTS.md` is exactly 100 lines against its 100-line cap,
with `agent-ready caps` and `budget` both passing. Rule 4's counterpart claims
about `test_set_corpus.py` and `TestTheShippedGrammarKeepsRejecting` are true.
`mkdocs.yml` nav is consistent: 59 `.md` files, all in nav or `not_in_nav`.

## Findings

1. **Rule 3's worked example stated the opposite of what the repository
   does.** It ended "The schema now models it and all three are gone." They
   are not: `set_validator.py`'s docstring calls the bridge temporary, the
   three regexes are still there, and `tests/test_set_validator.py` carries a
   class named `TestTheApplyGroupsStripperIsStillLoadBearing`. The document
   contradicted its own parent commit, `v0.6.29`, which says in terms that the
   compensation stays. For an instruction file whose thesis is "measure, don't
   infer", in the example it chose to prove the rule, this is the worst
   available error. **Fixed in v0.7.0** — and the honest version is a better
   illustration of "fix at the owning layer, *or record why not*".
2. **"Validated for two releases" is five.** `QUOTED_OR_VALUE` carried
   `EXPRESSION` from v0.6.22 through v0.6.26, confirmed by reading the shipped
   grammar at each tag. The how-to avoids the number; `proposal.md` and the
   commit message carry it. Open.
3. **The rule 1 table's second row is not a rendering-vs-rendering
   disagreement.** JSON, set and YAML all agree on `disable`; the divergence
   is between the XSD's folded element name and *every* rendering. A good
   point, in the wrong table, with the wrong "where it shows" column.
4. Rule 1 asks for three renderings; rule 2's capture block gives two. No
   `| display xml` example.
5. The two capture commands are valid Junos CLI — no `|` inside a match
   pattern, no shell-breaking quotes, no `match -A`. The document does not
   warn about those pitfalls either, so there is no "contains the error it
   warns against" finding. Stated plainly rather than manufactured.
6. `retires.md` does not declare that the 100-line cap was met by reflowing
   the opening paragraph from 4 lines to 3. The file now has zero headroom.

## Resolution

Unusually well evidenced — the numeric claims survive to the unit across 659
MB of dumps. Finding 1 was a false claim in an instruction document and is
fixed. 2, 3, 4 and 6 are recorded and left.

## Owner acceptance

The owner asked for the open changes to be archived (2026-10-08) and, shown
the findings in summary, chose to fix the blockers and the over-acceptance
before archiving. They did not review each finding individually. Everything
recorded as fixed was fixed in `v0.7.0` (`validate-own-output`); everything
recorded as accepted is accepted on that basis.

## Measurements superseded

Any real-device rejection figure above was taken against the bundled 24.4R0
artifacts, found defective on 2026-10-08 and replaced in v0.8.0. The numbers
that stand are in `ship-25-2r2-artifacts`; see
`docs/decisions/2026-10-08-superseded-device-measurements.md`.
