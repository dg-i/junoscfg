# Review

Fresh agent session, read-only, against `v0.6.32`. Mutation testing done on a
copy of `src/` outside the tree.

## Confirmed exact

1,535 files / 4,945,686 lines; 0.97720 conversion rate (35 of 1,535 failing);
217 field warnings = 0.0439 per 1k. All three guards' assertions are
substantively correct and each fails with its fix reverted. Nothing from the
corpus is committed; `git check-ignore` confirms the clone is ignored; the
default suite is unaffected and skips the tier cleanly.

## Findings

1. **The tier did not pass at HEAD.** `tasks.md` 3.1 says all seven pass.
   The oneliner guard built `data/junos-set.lark` by hand instead of going
   through `find_artifact`, so `ship-compressed-artifacts` broke it and the
   opt-in tier hid that. **Fixed in v0.7.0**; it now takes the shared
   `bundled_set_validator` fixture. 7 passed in 177s.
2. **"Each taking its example from the corpus rather than from a literal" is
   false for all three guards** — claimed in `proposal.md`, `tasks.md` 1.3,
   the commit message, the class docstring and the developer guide. Guard 1
   uses the corpus only as a skip predicate; guard 2 takes the fixture and
   never references it; guard 3 does not take it at all. The assertions are
   right; the provenance claim is not. Open.
3. **Guard 3 did not skip cleanly without the corpus** — it did not request
   `jvd_corpus`, so it ran anyway and errored. Fixed as a side effect of 1;
   it is now a shipped-grammar guard that needs no corpus, which is arguably
   where it belonged.
4. **Two of three thresholds are close to decorative.** The conversion floor has 2.2x
   slack and the warning budget 11.4x — it trips at ~2,473 warnings against
   217 observed. It catches the `nokeyword` enum defect (21x over) and would
   **not** catch the `ipaddr-or-interface` one (215 warnings, well inside).
   The load-bearing assertion is
   `test_every_failure_is_a_file_that_is_not_configuration`. Recorded.
5. **The not-configuration escape list has a hole.** `"## SECRET-DATA"`
   excuses exactly one failure today but is a ubiquitous Junos annotation on
   secret-bearing lines, so any future genuine parse failure on such a line is
   waved through. `"Unknown statement: AN"`/`"MA"` are 2–3 character prefixes.
   Open.
6. **The corpus pass never exercises the validator**, but the developer guide
   says to run `--jvd` after a grammar change. For field-validator changes
   that is true; for grammar changes the only coverage is guard 3. Open.
7. `retires.md` omits the `conftest.py` additions and the changelog fragment,
   and understates the developer-guide edit.

## Resolution

The tier is real and its central assertion is the right one. Finding 1 was a
red test tier nobody knew about and is fixed. 2 is a provenance claim that
should be corrected or made true; 4, 5, 6 and 7 are recorded and left.

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
