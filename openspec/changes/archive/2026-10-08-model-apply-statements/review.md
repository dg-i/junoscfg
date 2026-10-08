# Review

Fresh agent session, read-only, against `v0.6.32`.

## Confirmed exact

"Nothing ships" is **hard-verified**: metadata still 24.4R0; `apply-groups`,
`universal` and `"u":` are 0 occurrences in the structure tree;
`universal_statement` is 0 in the grammar; a raw parse of `set apply-groups
GLOBAL` still raises. Three independent guards each fail against an in-memory
tree carrying the nodes, so a leak cannot pass CI. The four statements are
absent from all four XSD dumps, as substring, confirmed over 659 MB. 242 bytes
and 97,800 bytes reproduce; 123,769 containers reproduces.

## Findings

1. **"Two tests flip together" was false — only one flipped.** Simulated the
   day the artifacts carry the nodes:
   `test_the_shipped_grammar_does_not_yet_model_apply_groups` fails, and
   `test_the_stripper_makes_it_validate_anyway` *passes*, because it asserted
   `valid is True` and that stays true: the stripper still strips and the
   shortened line still parses. The retirement signal the whole "the bridge
   stays, labelled" argument rests on did not exist, and the surviving green
   test would have read as evidence the bridge was still needed.
   **Fixed in v0.7.0**: the second test now asserts the *difference* stripping
   makes — the raw line must not parse — so it goes red with its sibling. The
   claim in `tasks.md` 1.6 is true as of that commit, not as of this one.
2. **"51,085 containers" is not reproducible** and contradicts this change's
   own 123,769. It was in shipped source. **Fixed in v0.7.0.**
3. **`read_structure_tree`'s docstring does not list `universal`** among what
   `generate_lark_grammar` reads, against the precedent its predecessor set
   for `type_ref`. Open.
4. **`ALL_FIXES` changed without a declared break**; `stage griffe` fails.
5. **The per-container figures are approximations stated as measurements**:
   +25.5 MB measured against "+24 MB", +0.58 MB against "+0.6 MB". The
   argument is unaffected; the declare-once side reproduces exactly.
6. The `universal` `patternProperties` entry maps to `{}`, so once
   regenerated JSON/YAML will accept `apply-groups: 7`. Noted; it is a
   property *name* allowance, and v0.7.0 now ships that allowance from the
   kernel for exactly the round-trip reason.

## Resolution

The "nothing ships" discipline is the strongest part of any record in this
batch and survived a determined attempt to find a leak. Finding 1 was the
serious one — a false forward promise written into shipped source — and is
fixed. 2 is fixed. 3, 4, 5 are recorded and left.

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
