# Review

Fresh agent session, read-only, against `v0.6.32`. Claims checked by
measurement rather than by reading.

## Confirmed exact

11,853 expression-capable slots before and 159 after; `set system host-name
(foo bar)` rejected and a policy-algebra line accepted, both against the
shipped artifact; `policy-algebra` on 7,636 nodes, every one a leaf; 0 as an
element name against 186/196/201/253 type references across four dumps. Five
assertions confirmed to fail under mutation.

## Findings

1. **"93 of 4,385 rules changed" is 88.** `git show --numstat` gives 89
   insertions / 88 deletions, and 88 distinct rule names carry
   `ALGEBRA_OR_VALUE`. Corrected here; the record is left as written.
2. **"Seven assertions between them" is 10 tests / 11 assertions.** The
   accompanying "five of which fail" is right, confirmed exactly.
3. **`_value_token`'s docstring said 11,854** where the proposal says 11,853.
   Both are right about different things: 11,854 counts the terminal
   definition line. Left, now that the two numbers are reconciled here.
4. **The element enumeration is misleading.** The proposal names `import`,
   `export`, `prefix-policy`, `policy` as though exhaustive; there are 54
   distinct names, and `retention-policy` (1,368) outranks `policy` (346).
5. **Stale reference left in shipped source.** `grammar_generator.py`
   explained the behaviour of `_fix_policy_algebra`, which the *next* commit
   deleted. **Fixed in v0.7.0** — the comment now says the entry was deleted
   for matching nothing. `proposal.md:21` still carries the present tense.
6. The two shipped-grammar negatives only bite once the artifact is
   regenerated; `TestBundledGrammarIsReproducible` is what catches a
   source-only regression. Worth knowing when reading "five fail".

## Resolution

The substance holds. Numbers 1, 2 and 4 are record inaccuracies that do not
change the work; 5 was a live staleness in shipped source and is fixed.

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
