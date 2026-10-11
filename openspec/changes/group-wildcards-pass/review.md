## Findings

A fresh, isolated Reviewer read the freeze, the delta, `anonymize/CONTRACT.md`, the Test/Challenge
record and S1-S3, the tests and the diff `1ebeed9..a4eb20e` (code `e0b9d95`); executed probes with
synthetic values in `private_test_data/makeover-work/group-wildcards-pass/roles/`
(`review_probe{,2,3}.py`, `review_fix_probe.py`, `keyed_plugin.py`, CLI door `cli_*`), the full
report `roles/review.md`. Verdict at `a4eb20e`: **CHANGES REQUIRED**. Every ruling relayed by the
orchestrator on 2026-10-11 was accepted; dispositions:

1. R1, HIGH, the change removed exact revert. `SensitiveWordRule.wildcard` keyed the mapping by the
   text inside the brackets, which a value differing only in case shares once folded: P1 `<ebgp>`
   beside group `EBGP` and P1b `<EBGP>` beside `description ebgp` reverted to the other case; the
   base was exact. Fixed: the rewrite is keyed by the whole wildcard as written (the Reviewer's
   verified fix), the strict xfail is a plain test with rows P1, P1b and same-case
   (`test_a_word_in_two_cases_reverts_to_each`), and the delta's exception is narrowed to plain
   values (NEW-R13, change 7).
2. R2, HIGH, the strings passes ran after the walk's report. P2 `<peer-203.0.114.*>` beside
   `peer-203.0.114.7` with `ips_in_strings`: the name was rewritten, the wildcard kept `203.0.114`
   and selected nothing, unreported (base alike). Fixed: the walk records each name and wildcard
   by its entry and key and the report is read in `anonymize()` after both strings passes, from
   the final values; `IpRule.pattern_in_string` rewrites a whole-octet fragment of two or more
   octets through its prefix (unless the walk wrote it already) and leaves any other address
   fragment beside a wildcard character unvouched; revert restores such a fragment through the
   prefix mapping. Rows `ip-in-string` (reported) and `ip-in-string` (rewritten, not reported),
   a `strings-passes` revert row. Recorded as S4.
3. R3, MEDIUM, an AS number behind `?` or a class (P3b `<AS6449?-*>`) leaked unreported under
   `as_numbers_in_strings`. Fixed: the AS strings pass leaves such a wildcard unvouched; row
   `as-number-class`. S4.
4. R4, MEDIUM, docs claimed exact revert. Made true by R1; the changelog, the CLI guide and the
   developer guide name the strings passes and the AS case.
5. R5, LOW, an address pattern over a partly preserved prefix was vouched for. Fixed:
   `IpRule._octet_pattern` rewrites only when no preserved prefix, kept block or range-preserved
   block (`ipanon.ranges`, as the flags leave them) cuts the prefix; rows
   `ip-prefix-cut-by-a-kept-block` (`<203.0.*>` holds `203.0.113.0/24`) and
   `ip-prefix-cut-by-a-preserved-prefix`. The `<203.0.*>` row of
   `test_an_address_pattern_takes_its_prefixs_replacement` becomes `<198.0.*>`.
6. R6, LOW, `_pattern` was a second copy of `_try_rules`. Fixed: one loop; a wildcard's text
   consults `Rule.wildcard` first and returns whether it is vouched for; an enum value stops the
   loop and a `keeps_text` rule chains through `lexical`, as for any name.
7. R7, LOW, the warning said "left as written" of a rewritten wildcard. Reworded: "N wildcard
   name(s) here select other names once anonymized, or could not be rewritten as a pattern".

The Reviewer's probes rerun on the fixed head: every case reverts exactly; every case left as
written is reported (`review-probes-after-fix.out`). Carried forward by the Reviewer: Junos's
reading of `[^...]`, `\` and an unclosed `[` (F8), probe P10, and whether Junos accepts `<...>` at
a key field outside `groups` (the change treats it as a wildcard everywhere).

## Already provided

- Python's `fnmatch.fnmatchcase` is the selection check's matcher (ruling on Test/Challenge F8).
  That it reads Junos's wildcards as the device does is unverified: they agree on `*`, `?`,
  `[...]`, `[!...]`, `]` first and `-` first or last, and `*` crosses `/` as the device's `<ge-*>`
  does on `ge-0/0/0`; they may differ on `[^...]` (Python reads `^` literally, FreeBSD fnmatch(3)
  negates), on `\` (literal in Python, an escape in FreeBSD) and on an unclosed `[`. The same
  matcher reads before and after, so a difference changes a verdict only for renamed names in
  such a class.
- The IP rule's prefix-preserving replacement (`ipanon`) gives the prefix of a pattern of whole
  octets: `203.0.114.0/24` to `203.211.226.0/24`, beside `203.0.114.7` to `203.211.226.136`.

## Specification challenges

### S1: a wildcard name with literal text cannot keep selecting the same names under a renaming rule

- Artifact: the inventory's sketch for ANON-P3 (`private_test_data/makeover-work/inventory-a.md`, G5: "owner decides wildcards with literal text (`<EBGP-*>`): keep verbatim (leaks the literal) or rewrite the literal part with the same pseudonym table the referenced names use"); this change's requirement "A wildcard name is a pattern, not a name" (`specs/anonymization/placed-values/spec.md`), whose reporting half is the interim rule.
- Counterexample: executed on `1ebeed9` (`private_test_data/makeover-work/group-wildcards-pass/repro.py`, `repro-base.out`): `groups GR-BGP protocols bgp group <EBGP-*>` with `protocols bgp group EBGP-A` under `--anonymize-groups`. The group rule replaces each name by a hash of the whole name (`group_<24 hex>`), so no pseudonym of `EBGP-A` shares a prefix with a pseudonym of anything: kept verbatim, `<EBGP-*>` leaks `EBGP` and selects nothing; rewritten (`group_…` on the base, `<group_…>` here) it leaks nothing and selects nothing. The same holds for the identity and community rules (address patterns are S2, a sensitive word behind a class S3). Device evidence holds no such wildcard: the captures' wildcards are `<*>` at a BGP group and patterns at interface, unit and routing-instance names no rule renames (vMX 23.2R2-S7.5 and QFX5120 25.2R2-S1.5 `junoscfg-oracle`, JVD vMX `mdr1_acx7509`).
- User impact: an anonymized configuration whose group applies a wildcard with literal text to renamed names applies it to nothing; it loads, and the group silently stops contributing its statements.
- Proposed correction, for the owner to choose: (a) the interim rule below, permanently; (b) prefix-keeping pseudonyms (`EBGP-A` to `<p>-A` where `<p>` replaces the literal `EBGP`) for every name a wildcard with literal text selects, which keeps the selection but leaks the structure of names; (c) refuse to anonymize such a configuration unless the caller opts in. Tests to follow the choice: `TestAWildcardNameIsAPattern::test_a_wildcard_that_selects_other_names_is_reported` and its scenarios in the delta.
- Decision: Pending owner decision. Interim action: a wildcard of `*` alone passes every rule (no value in it, same selection); any other keeps its brackets while its text goes to the rules as a name of that key field, which keeps a wildcard that spells one name (`<EBGP>`, `<203.0.114.7>`) selecting its renamed name and leaks nothing a rule claims; a wildcard whose anonymized selection over the configuration's names at that place differs from the original's, or whose text a rule claims and leaves as written, is named by schema path in `AnonymizeResult.patterns` and an `anonymize:` warning (path and count, no value), so a caller can stop on it. Reversible: remove the report, or replace the wildcard branch of the walker by the chosen correction (owner intake 2026-10-11: merge with recorded interim action).

### S2: an address pattern is rewritten through its prefix, or reported

- Artifact: this change's requirement "A wildcard name is a pattern, not a name" as first frozen (`1fefa9b`): the IP rule left `<203.0.114.*>` as written, and the change reported it only when the selection changed.
- Counterexample: executed by the Test/Challenge role (`roles/challenge_probe.py`, C1): `groups GR-BGP protocols bgp group <*> neighbor "<203.0.114.*>"` under `--anonymize-ips` with no neighbour at its place: no address token, an empty selection before and after, no report, and `203.0.114` in the output.
- User impact: an anonymized output publishes the /24 of the operator's peers, unannounced.
- Proposed correction (ruling on F1): an IPv4 pattern of whole octets becomes the pattern of its prefix's replacement, which keeps the selection because replacements keep their prefixes; any other address pattern (`203.0.11*`, an IPv6 pattern) is left as written and reported. Tests `test_an_address_pattern_takes_its_prefixs_replacement`, `test_a_wildcard_that_selects_other_names_is_reported[ip-not-whole-octets, ip-v6]`, `test_a_preserved_address_is_not_reported`.
- Decision: Pending owner decision. Interim action: the proposed correction (`IpRule.wildcard`; revert through the prefix's mapping); reversible by removing the hook, which reports every address pattern instead (owner intake 2026-10-11: merge with recorded interim action).

### S3: a sensitive word behind wildcard syntax is reported

- Artifact: the same requirement as first frozen: the sensitive-word rule claims a wildcard's text only where a substring search finds the word.
- Counterexample: executed by the Test/Challenge role (C2): `"<[Aa]cme-*>"` (the usual Junos idiom for either case) under `--anonymize-sensitive-words acme` with no `acme` name at its place: not claimed, selection unchanged, not reported, `cme` in the output. C3: `<acme-*>` beside `ACME-A`: the rule folds case, so the rewritten wildcard selects `word_…-A`, which Junos, matching case, did not; reported by the selection check, and revert of a word written in two cases restores one case (NEW-R13, change 7, strict xfail `test_a_word_in_two_cases_reverts_to_each`).
- User impact: a protected word survives behind a class; or a group starts to apply to names it did not.
- Proposed correction (ruling on F2): a word the text holds in literals is replaced as in any name; a word it can spell only through a class or `?`, classes read in either case, leaves the text as written and is reported; with a sensitive pattern on, any class or `?` is reported, since a regular expression cannot be checked against a class. Tests `test_a_sensitive_word_behind_a_class_is_reported`, `test_a_wildcard_that_selects_other_names_is_reported[sensitive-word-class, sensitive-word-other-case]`.
- Decision: Pending owner decision. Interim action: the proposed correction (`SensitiveWordRule.wildcard`); reversible by removing the hook (owner intake 2026-10-11: merge with recorded interim action).

### S4: the strings passes treat a wildcard's text as a pattern, or report it

- Artifact: the delta's trigger as first frozen ("a rule claims text ... and leaves it as written"), judged at walk time.
- Counterexample: executed by the Reviewer (`roles/review_probe2.out`, P2, P3b): `<peer-203.0.114.*>` beside `peer-203.0.114.7` under `--anonymize-ips-in-strings`, and `<AS6449?-*>` beside `AS64496-A` under `--anonymize-as-numbers-in-strings`: the strings passes are not walker rules, so the names were rewritten after the report, the wildcards kept `203.0.114` and `6449`, and nothing was reported.
- User impact: a /24 or an AS prefix is published unannounced, and the group silently stops applying.
- Proposed correction (rulings R2, R3): the report is read from the final values after every pass; the IP strings pass rewrites a whole-octet fragment of two or more octets through its prefix and leaves any other address fragment beside a wildcard character as written, reported; the AS strings pass reports digits beside `?` or a class.
- Decision: Pending owner decision. Interim action: the proposed correction; reversible by removing the wildcard branches of `_replace_ips_in_strings` and `_replace_as_in_strings` (owner intake 2026-10-11: merge with recorded interim action).

## Verdict

CHANGES REQUIRED at `a4eb20e` (R1-R7, all accepted and applied). Confirmation by the same Reviewer next.
