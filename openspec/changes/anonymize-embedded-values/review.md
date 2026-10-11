## Findings

None yet: the fresh Reviewer runs at STOP-R.

## Already provided

- `junoscfg.anonymize.rules.address_tokens` and `replace_addresses`: the one answer to where an
  address stands in text (change 5); the IP rule's shape, the revert's address pass.
- `junoscfg.anonymize.rules.sensitive_word._glob_positions` and `_spells_through_syntax`: whether a
  wildcard's `?` or class can spell a word (change 6); NEW-R14 reuses them for AS numbers.
- `junoscfg.display.schema_child` and `entry_key_names`: where a keyword leads and which key fields
  an entry has; the `apply-path` reader uses them as the walker does.

## Specification challenges

### S1: an address inside free text under `ips` alone

- Artifact: `openspec/specs/anonymization/placed-values/spec.md`, "The IP rule answers by the
  leaf's type" ("no other free text is one"); `AnonymizeConfig.ips_in_strings` (default off);
  inventory G4 ("owner decision on default of `ips_in_strings`").
- Counterexample (executed, `private_test_data/makeover-work/anonymize-embedded-values/repro.py` on
  `50b0a10`): `set system archival configuration archive-sites "scp://admin@203.0.114.5/path"` and
  `set interfaces ge-0/0/0 description "uplink to 203.0.114.6 port 3"` with `--anonymize-ips`:
  both addresses survive, no diagnostic. Violated invariant: the placed-values purpose,
  "Anonymization never claims success while a value it could replace survives unannounced".
- User impact: a user who asks for addresses to be anonymized publishes addresses.
- Proposed correction: under `ips` an address with other text beside it in a value is replaced on
  any leaf; an address that is the whole value still answers by the leaf's type (an SNMP OID, `from
  area 0.0.0.0` stay); `ips_in_strings` keeps one effect, an address that is a whole value on any
  leaf. Delta: `anonymization/embedded-values` "A value inside free text goes to the rule that owns
  its shape", `anonymization/placed-values` "The IP rule answers by the leaf's type" (MODIFIED).
  Alternative left to the owner: keep the opt-in and report each leaf holding an address inside
  text instead.
- Decision: Pending owner decision. Interim action: the proposed correction, which replaces more and
  never fewer values and is restored by the mapping; measured on every device capture by the
  before/after comparison (owner intake 2026-10-11: merge with recorded interim action).

### S2: one pseudonym per spelling of a sensitive word

- Artifact: `src/junoscfg/anonymize/rules/sensitive_word.py` ("the hash is derived from the
  lowercased matched text"); `openspec/specs/anonymization/wildcard-names/spec.md`, the revert
  exception "two plain values that do are NEW-R13" and scenario "Sensitive words" (`<ebgp-*>` is
  reported); `tests/unit/anonymize/test_integration.py::TestAWildcardNameIsAPattern::test_a_wildcard_that_selects_other_names_is_reported[sensitive-word-other-case]`.
- Counterexample (executed, `repro.py` on `50b0a10`): `set protocols bgp group EBGP description ebgp`
  and `set interfaces ge-0/0/0 description EBGP` with `--anonymize-sensitive-words ebgp`: all three
  values become `word_2789…`; revert gives `ebgp` for each (NEW-R13). Violated invariant: "Revert
  must be exact" (owner, change 6), "revert restores the canonical IR" (mission Definition of done).
- User impact: a reverted configuration renames a BGP group and every reference to it.
- Proposed correction: the pseudonym is keyed by the matched spelling, so `EBGP` and `ebgp` get two
  (Junos names are case-sensitive); matching stays case-insensitive, so every spelling is still
  replaced. `<ebgp-*>` beside `EBGP-A` then selects nothing, as Junos did, and is no longer
  reported; the wildcard-names scenario and that test row change (phase 5, after the orchestrator's
  ruling on the shared file, see `evidence-freeze.md`). Alternative left to the owner: keep one
  pseudonym per word and accept that revert restores one case.
- Decision: Pending owner decision. Interim action: the proposed correction; an analyst loses the
  link between two spellings of one word, nothing leaks, and revert becomes exact (owner intake
  2026-10-11: merge with recorded interim action).

## Verdict

Pending: the fresh Reviewer's verdict at STOP-R.
