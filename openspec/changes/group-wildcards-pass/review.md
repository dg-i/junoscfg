## Findings

<!-- Written by the fresh Reviewer after phase 5. -->

## Already provided

- Python's `fnmatch.fnmatchcase` matches the Junos wildcard characters `*`, `?`, `[...]` and
  `[!...]` (Junos OS "Configuration Groups", wildcards), so the selection check needs no matcher
  of its own.

## Specification challenges

### S1: a wildcard name with literal text cannot keep selecting the same names under a renaming rule

- Artifact: the inventory's sketch for ANON-P3 (`private_test_data/makeover-work/inventory-a.md`, G5: "owner decides wildcards with literal text (`<EBGP-*>`): keep verbatim (leaks the literal) or rewrite the literal part with the same pseudonym table the referenced names use"); this change's requirement "A wildcard name is a pattern, not a name" (`specs/anonymization/placed-values/spec.md`), whose reporting half is the interim rule.
- Counterexample: executed on `1ebeed9` (`private_test_data/makeover-work/group-wildcards-pass/repro.py`, `repro-base.out`): `groups GR-BGP protocols bgp group <EBGP-*>` with `protocols bgp group EBGP-A` under `--anonymize-groups`. The group rule replaces each name by a hash of the whole name (`group_<24 hex>`), so no pseudonym of `EBGP-A` shares a prefix with a pseudonym of anything: kept verbatim, `<EBGP-*>` leaks `EBGP` and selects nothing; rewritten (`group_…` on the base, `<group_…>` here) it leaks nothing and selects nothing. The same holds for the identity and community rules, for the IP rule on `<203.0.114.*>` (an address pattern is not an address, so the rule leaves it as written beside renamed neighbours), and for a sensitive word inside a character class (`"<[A-E]BGP*>"` stops selecting `word_…`). Device evidence holds no such wildcard: the captures' wildcards are `<*>` at a BGP group and patterns at interface, unit and routing-instance names no rule renames (vMX 23.2R2-S7.5 and QFX5120 25.2R2-S1.5 `junoscfg-oracle`, JVD vMX `mdr1_acx7509`).
- User impact: an anonymized configuration whose group applies a wildcard with literal text to renamed names applies it to nothing; it loads, and the group silently stops contributing its statements.
- Proposed correction, for the owner to choose: (a) the interim rule below, permanently; (b) prefix-keeping pseudonyms (`EBGP-A` to `<p>-A` where `<p>` replaces the literal `EBGP`) for every name a wildcard with literal text selects, which keeps the selection but leaks the structure of names; (c) refuse to anonymize such a configuration unless the caller opts in. Tests to follow the choice: `TestAWildcardNameIsAPattern::test_a_wildcard_that_selects_other_names_is_reported` and its scenarios in the delta.
- Decision: Pending owner decision. Interim action: a wildcard of `*` alone passes every rule (no value in it, same selection); any other keeps its brackets while its text goes to the rules as a name of that key field, which keeps a wildcard that spells one name (`<EBGP>`, `<203.0.114.7>`) selecting its renamed name and leaks nothing a rule claims; a wildcard whose anonymized selection over the configuration's names at that place differs from the original's, or whose text a rule claims and leaves as written, is named by schema path in `AnonymizeResult.patterns` and an `anonymize:` warning (path and count, no value), so a caller can stop on it. Reversible: remove the report, or replace the wildcard branch of the walker by the chosen correction (owner intake 2026-10-11: merge with recorded interim action).

## Verdict

<!-- Written by the fresh Reviewer. -->
