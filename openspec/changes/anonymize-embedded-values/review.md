## Findings

None yet: the fresh Reviewer runs at STOP-R. Test/Challenge findings T1-T12 and their rulings:
`test-challenge.md` and the evidence freeze's delta log.

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

### S3: annotations are free text

- Artifact: `specs/anonymization/embedded-values/spec.md` (as frozen at STOP-T it named placed values
  and content the walk cannot place, not annotations); `walker.py` skips every `@` key.
- Counterexample (executed by Test/Challenge, `roles/probe_annotations{,2}.py`): the vMX
  23.2R2-S7.5 `junoscfg-oracle.json.gz` annotation edited to hold `203.0.114.77`, and a synthetic
  `"@": {"comment": ...}` holding an address, a URL user and password and a `$9$` hash, survive
  every rule through JSON and YAML output.
- User impact: an anonymized Junos JSON export publishes what its comments say.
- Proposed correction: an annotation's text goes through the same chain as free text; revert
  restores it. Alternative: drop annotations from an anonymized run with one value-free warning.
- Decision: Pending owner decision. Interim action: annotations are treated as free text and
  anonymized by the chain at every door that keeps them (JSON, YAML; orchestrator ruling T1)
  (owner intake 2026-10-11: merge with recorded interim action).

### S4: an address alone in a free-text leaf

- Artifact: placed-values "The IP rule answers by the leaf's type" ("no other free text is one").
- Counterexample (executed, Test/Challenge): `description 203.0.114.9`, `snmp location 203.0.114.9`,
  `snmp contact 3ffe:b00::9` pass `--anonymize-ips` unchanged with no warning, while `description
  "to 203.0.114.9"` is replaced under S1; the SNMP OID key and `description` are both `xsd:string`.
- User impact: an address written alone in a description is published.
- Proposed correction: under `ips` an address that is the whole value of a free-text leaf is
  replaced, but for the SNMP OID (`snmp view V oid`); `areaid` references stay; `ips_in_strings`
  adds those. Alternative: report the path instead.
- Decision: Pending owner decision. Interim action: the proposed correction, replace (orchestrator
  ruling: the safe side) (owner intake 2026-10-11: merge with recorded interim action).

### S5: address forms the tokenizer or the address anonymizer kept

- Artifact: `anonymize/rules/__init__.py::_ADDRESS_TOKEN`, `IpRule`.
- Counterexample (executed, `roles/probe_lexical.py`, `probe_revert_and_v6.py`): `see 203.0.114.6.`,
  `lo_3ffe:b00::1`, `host:3ffe:b00::1`, `3ffe:b00::1.`, `203.000.114.006` give no token;
  `::ffff:203.0.114.5`, `::203.0.114.5`, `64:ff9b::203.0.114.5` come back unchanged.
- User impact: an IPv4 address survives `--anonymize-ips` because of how it is written.
- Proposed correction: a dot not followed by a digit ends an address; an IPv6 address may follow
  `_` or a non-hex word and a colon; the IPv4 inside a mapped, compatible or NAT64 form takes its
  own replacement, the IPv6 prefix kept; a zero-padded dotted quad is replaced, its spelling
  recorded in the mapping (revert restores the spelling unless the same address is also written
  plainly). Not covered: an IPv4 address written as hex groups inside an IPv6 form
  (`64:ff9b::cb00:7205`), which the address anonymizer keeps.
- Decision: Pending owner decision. Interim action: the proposed correction (orchestrator ruling
  T2, T3) (owner intake 2026-10-11: merge with recorded interim action).

### S6: where a URL's userinfo ends

- Artifact: `specs/anonymization/embedded-values/spec.md`, `scheme://user[:password]@`.
- Counterexample (constructed, Test/Challenge T9): `ftp://operator:p@ss:w0rd@203.0.114.6/x`; split
  at the first `@`, `ss:w0rd` is published as host text; `FTP://` unspecified.
- User impact: part of a password is published.
- Proposed correction: any scheme in any case; the userinfo runs from `//` to the last `@` before
  the host (RFC 3986); the user ends at its first `:`. A template user (`scp://${user}@...`) is a
  user too and is renamed; revert restores it (Test/Challenge T12).
- Decision: Pending owner decision. Interim action: the proposed correction (owner intake
  2026-10-11: merge with recorded interim action).

### S7: which filter governs a name inside an `apply-path`

- Artifact: `specs/anonymization/embedded-values/spec.md`, "An apply-path names configuration".
- Counterexample (constructed, Test/Challenge T10): `exclude=["protocols.bgp"]` keeps group `EBGP`;
  read at the apply-path, the path's `EBGP` is renamed and the prefix list selects nothing.
- User impact: a filtered run can break the configuration it was meant to keep, or, filtered at the
  named place, leak the name the path holds.
- Proposed correction (Test/Challenge): rewrite only where both places are in scope.
- Decision: Pending owner decision. Interim action: the filter at the `apply-path` leaf itself
  decides, so a name in a path in scope is replaced (orchestrator ruling: the safe side) (owner
  intake 2026-10-11: merge with recorded interim action).

## Explicit owner dispositions — superseding historical interim decisions

Source: `private_test_data/makeover-work/codex-resumption/owner-decisions.md`, explicit replies on 2026-10-11. Historical S1–S7 entries and T1–T12 evidence above are retained. S1/S3/S4 privacy and annotations accepted; S2 spelling-keyed pseudonyms with case-insensitive matching accepted; S6 last-@ URL handling accepted. S5 final simplification retains flat maps and rejects ambiguous plain/padded spellings before output; all successful runs restore exactly. It supersedes the historical spelling-loss exception and the supplemental v2 proposal; ambiguous old maps cannot recover lost occurrences and are rejected before revert mutation. S7 accepts in-scope selector replacement despite excluded targets and unchanged excluded selectors despite renamed targets, with value-free selector-risk reporting in both directions. Independent supplemental Test/Challenge evidence at `7e2209e` remains evidence, not Builder approval.

## Verdict

Pending: the fresh Reviewer's verdict at STOP-R.

### S5 supplemental: IPv6 spelling aliases evade the forward collision guard

- Artifact: existing exact-successful-reversal and flat-map ambiguity-refusal invariant; `IpRule.get_mapping`.
- Counterexample: independent final Test/Challenge report on `074736b`/`0438299` executes compressed/expanded (`3ffe:b00::9`, `3ffe:0b00:0:0:0:0:0:9`) and case (`3ffe:b00::a`, `3FFE:B00::A`) aliases in both orders/all readers. Forward output and flat map succeed; reverse rejects duplicate replacement values.
- User impact: a successful anonymized output cannot be restored with the map it just dumped.
- Proposed correction: extend the existing fixed value-free forward collision refusal to every IP mapping entry, rather than only the padded-IPv4 bookkeeping case; retain successful one-spelling controls and the flat format.
- Decision: orchestrator explicitly accepts this minimal correction under the already approved exact-successful-reversal policy; no new owner policy inferred or Builder approval. Independent verdict remains NEEDS CORRECTION until re-challenged.

Independent correction verification: APPROVE on exact source `574b55ef9895f88a9f417e9480eb017b6055d133`, report `private_test_data/makeover-work/anonymize-embedded-values/roles/codex-final-challenge/correction/report.md`. Executed 167 focused passes, 103 probe records/zero losses, 20 CLI safe refusals and 3 exact single-spelling controls. This resolves the preceding S5 IPv6 counterexample; original evidence remains. Fresh Reviewer verdict is still pending.

## Fresh isolated review — original candidate

Verdict: NEEDS CORRECTION on `2fa6c60466a5232df8257b0dff101100bec38cf0`, private `roles/codex-fresh-review.md`. R2 (high, privacy): original URL credentials lose identity ownership after password delimiters or nested address rewrites; original URL/login users must share the identity pseudonym. R1 (high, forward correctness): wildcard continuation lacks generated-span protection and later rules corrupt an IP selector. Exact independent public-door probes/controls retained under `roles/codex-fresh-review/`. Orchestrator accepts correction under existing approved invariants; no new owner policy or Builder approval. Original full/device/timing checkpoint remains scoped to 2fa; corrected fresh verdict is pending.

## R1 continuation — kept prefix ownership

Independent Test/Challenge approved exact b162444 R1-generated-prefix and R2 corrections (private roles/codex-final-challenge/r1/correction/report.md); original findings and red evidence remain. Fresh Reviewer then found supported unchanged IP prefixes still lose selection under later regex/AS rules: default documentation prefixes and explicit preserve options, including mixed peer names (18 executed rows, 12 losses/6 controls, private roles/codex-fresh-review/correction/kept-prefix-probe.json). Root accepts bounded correction under the existing wholly-kept-or-replaced/owned-shape invariant; no Builder approval or new policy. Corrected fresh verdict remains pending. b162 full/device/timing is preserved only for that source.

## Independent kept-prefix correction verification

Test/Challenge APPROVE on exact `48f8a858153696809ff1cd6496a84feed9a4b557`, private roles/codex-final-challenge/kept-prefix/correction/report.md: 252 focused passed/158 deselected; 50 wholly-kept and 50 generated selector rows without loss, 48 URL rows without identity leaks, 16 aliases without mismatch, 103 ambiguity/error records without loss. Original red evidence remains intact. Root full on the same clean source passes 9,064 tests/37 skipped/20 strict xfails and every gate, exit 0. Final device raw results remain identical to prior candidate outputs, with approved baseline deltas; bounded candidate timing and retained baseline provenance recorded in metrics/freeze. This resolves the independent correction challenge, not a Builder fresh-review verdict. Root-owned fresh corrected Reviewer closure remains pending, and no lifecycle approval is inferred.

## Final fresh isolated correction verdict

APPROVE exact source `48f8a858153696809ff1cd6496a84feed9a4b557` against `0438299772819f24c871d4cb2b8768f9233f9318`, independent private `roles/codex-fresh-review/kept-correction/report.md`. No surviving ranked finding. Reviewer executed 372 focused tests, 13 extra controls and independent selector/credential probes, and audited final full/device/timing hashes. R1 generated and wholly-kept prefixes and R2 original URL credential ownership are resolved under the unchanged frozen invariants. Original 2fa6c604 and b162444 NEEDS CORRECTION reports remain separately preserved. This supersedes historical pending verdict/checkpoint prose without changing it.
