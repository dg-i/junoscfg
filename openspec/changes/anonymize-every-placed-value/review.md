## Findings

A fresh, isolated Reviewer read the freeze, the delta, the touched contract, the
Test/Challenge record and its rulings, the tests and the diff `3a0607f..3ac0fda`
(`ab13794` a freeze reword); probes with synthetic values in
`private_test_data/makeover-work/anonymize-every-placed-value/roles/review/`, the
full report `roles/review.md`. Verdict at `ab13794`: **CHANGES REQUIRED**. Every
ruling relayed by the orchestrator on 2026-10-11 was accepted; dispositions:

1. HIGH, an address beside `:` or `_` (`http://203.0.114.9:8080/x`,
   `203.0.114.9:179`, `host:203.0.114.9`, `lo_203.0.114.9`) left unplaced content
   as written, where the base refused it. Fixed: one tokenizer,
   `junoscfg.anonymize.rules.address_tokens`, IPv4 bounded by a digit or a dot
   only, the `:` exclusion for IPv6 only; the strings pass's second regex is
   retired (the pass now finds IPv6 too). Rows for the four shapes and four more,
   as keys and values, in `_UNPLACED`.
2. HIGH, revert missed an address inside a word of a key. Fixed: revert splits
   a key as the walk does and restores each word, then each address token in it,
   with the same tokenizer; values revert the same way before the substring pass.
   Rows in `TestContentTheWalkCannotPlace::test_the_mapping_restores_it` and
   `TestRevertRestoresKeys::test_an_address_inside_a_word_of_a_key_is_restored`.
3. MEDIUM-HIGH, `ipv6-router-id` and BGP `cluster` keep the loopback beside the
   router ID's pseudonym (pre-existing). Fixed as S4's interim: a leaf-name
   allowance, only with types `string`/`areaid`, retirement with change 18. The
   strengthened proof (S5) then found 75,279 JVD route distinguishers in address
   form passing as written: the allowance covers `route-distinguisher rd-type` and
   the `vrf-target` leaves too (the address anywhere in the value). Blast radius
   `blast_s4.py`/`blast_s4.out`: 328 tree leaves; values changed: 75,279
   route distinguishers, 40 clusters, 9 `ipv6-router-id`; 102,217 values without an
   address (AS-form targets) unchanged; no integer, OID or `from area` touched.
   `cluster` left the syntax exclusions of the spec, the corpus law and
   `combos.py`.
4. MEDIUM, the warning claimed replacements the active rules do not make.
   Fixed: it names only the active rules' shapes, or says no active rule replaces
   a word; asserted in `test_without_the_ip_rule_it_is_still_named`.
5. MEDIUM-LOW, one rule per word. Fixed: the rules apply in turn to the same
   word; a rule that keeps the text around its replacement (`Rule.keeps_text`: the
   address and sensitive-word rules) lets the next look at it, on placed values
   too. `test_every_shape_in_one_word_is_replaced`.
6. LOW, a key spelled like a switch passed unannounced. Fixed: skipped only
   when its value is `None`, `True` or `[None]`; row
   `a-switch-spelling-holding-a-value`.
7. LOW, routing-matrix group names. Fixed: `lcc<N>-re<N>`, `sfc<N>-re<N>` pass.
8. LOW, stale texts. Fixed: the pin's docstring, the developer guide's rule
   priorities.

Re-review (same Reviewer, at `7173e75`): findings 1–8, S4 and S5 confirmed fixed,
the extension accepted; one new finding, ruled and fixed:

- R1, MEDIUM: with `--anonymize-ips` alone, `vrf-target target:<address>:100`
  was replaced but `policy-options community C1 members target:<address>:100`
  was not, so a `vrf-import`/`vrf-export` policy stopped matching. Fixed:
  `("community", "members")` joins `_ADDRESS_VALUED_LEAVES` (`target:` and
  `origin:` address forms); AS-form, regular-expression and well-known members
  hold no address and stay. `test_a_policy_community_matches_its_renamed_target`
  asserts the same pseudonym on both and an exact revert. Blast radius (the
  Reviewer's grep over 1,535 JVD files): 0 address-form members, 25,953 AS-form
  members unchanged.

Carried forward: NEW-R9 (change 5b); the OpenConfig `router-id` leaves typed
`string` (10 positions), change 18 with S4.

## Already provided

- `junoscfg.display.schema_child` resolves a universal statement below the root (change 4); the walkers adopt it rather than a copy.
- `audit/walker.py` already walks a transparent container's other children and each entry of a list under a container; the anonymize walker and field validation follow its shape.
- `IpRule.transform` and its mapping replace an address; content the walk cannot place uses it, not a second anonymizer.

## Specification challenges

### S1: the record of kept statements follows owner rule 5 instead of being refused

- Artifact: `openspec/specs/conversion/entry-keys/spec.md`, requirement "A statement the reader cannot complete is kept whole": "`junoscfg.anonymize.anonymize()` SHALL refuse an IR whose record holds a statement (any other key its walk cannot place is NEW-R5, change 5), and the conversion's refusal SHALL withhold the statement's text"; scenarios "A leaf without its value" ("anonymization refuses") and "A record is input like any other"; tests `TestAKeptStatementIsRefused`, `TestAKeptStatementOnTheCommandLine::test_anonymizing_refuses_without_the_statement`. Related: challenge R1 of change kept-whole-statements, pending the owner.
- Counterexample: executed on `3a0607f` (`private_test_data/makeover-work/anonymize-every-placed-value/repro.py`): `set system bogus 203.0.114.9` reads into the record and is refused, while the same statement from XML (`<system><bogus>203.0.114.9</bogus></system>`) or as its 0.16.1 joined key reads as a key. Owner answer 5 rewrites the key's address and warns; the requirement refuses the record. One configuration gets two answers by input door, and one statement two answers by spelling, against "one safety rule for unknown schema" (the owner's task for change 5).
- User impact: a set or curly configuration with one statement junoscfg cannot place cannot be anonymized at all, while the same configuration as JSON can; or, if the record were left to pass, its addresses would leave as written.
- Proposed correction: the record is content the walk cannot place, under rule 5: its address-shaped words are replaced (tags alike), its parent's schema path is warned about, nothing is refused, and no message carries its text. Delta `specs/conversion/entry-keys/spec.md`; tests `TestContentTheWalkCannotPlace`, `TestEveryDoorGivesOneAnswer`, `test_anonymizing_warns_without_the_statement`.
- Decision: Pending owner decision. Interim action: the proposed correction, reversible by restoring the record's refusal in `anonymize()` and the pipeline (owner intake 2026-10-11: merge with recorded interim action).

### S2: password hashes and sensitive words in content the walk cannot place are rewritten by shape

- Artifact: owner answer 5 ("anonymize IPv4/IPv6/prefix-shaped values by lexical pattern, never keywords"); C13 of `instruction-integrity.md` as first frozen (addresses only).
- Counterexample: executed by the Test/Challenge role (`private_test_data/makeover-work/anonymize-every-placed-value/roles/probe_shapes.py`): under an unknown key `$9$ExAmPlEhAsH.KEY` survives `passwords=True` and `acme` survives `sensitive_words=["acme"]`, while both rules recognise such a word by its shape alone, as the address rule does.
- User impact: an anonymized run publishes a secret or a protected word from a statement junoscfg cannot place, with only a warning.
- Proposed correction: every rule that knows a word by its shape alone (`Rule.lexical`: address, password hash, sensitive word) rewrites it in content the walk cannot place; `TestContentTheWalkCannotPlace::test_a_password_hash_and_a_sensitive_word_are_replaced_by_shape`.
- Decision: Pending owner decision. Interim action: the proposed correction, applied by the orchestrator's ruling on finding 8; reversible by restricting `Rule.lexical` to the IP rule (owner intake 2026-10-11: merge with recorded interim action).

### S3: `protocols ospf area 0.0.0.0` is rewritten under `--anonymize-ignore-reserved`

- Artifact: `openspec/changes/anonymize-every-placed-value/evidence-freeze.md` acceptance "syntax values (enum values, keywords, key choices) are unchanged"; `anonymize/rules/ip.py` `_ADDRESS_KEYED_LISTS` (`area`), unchanged from the base's `_IP_NAMED_LIST_PARENTS`.
- Counterexample: executed (`roles/probe_area.py`): with `ignore_reserved=True`, `set protocols ospf area 0.0.0.0 interface ge-0/0/0.0` becomes `area 233.113.141.75`; the backbone is lost. Base behaviour, unchanged here; `from area` is left as written (ruling 6), so a policy naming a non-zero area no longer matches its rewritten area under `--anonymize-ips`, as on the base.
- User impact: an anonymized configuration under that flag loses its backbone area.
- Proposed correction: an area identifier is syntax (`areaid`) and passes the IP rule, or the area and every reference to it are rewritten alike; the owner decides.
- Decision: Pending owner decision. Interim action: base behaviour kept, not extended; pinned by the strict xfail `tests/unit/anonymize/test_ip_rule.py::TestTheLeafsTypeAnswers::test_the_backbone_area_is_unchanged_s3` (owner intake 2026-10-11: merge with recorded interim action).

### S4: BGP `cluster`, `ipv6-router-id`, route distinguishers and VRF targets are data, not syntax

- Artifact: `specs/anonymization/placed-values/spec.md`, scenario "Syntax shaped like an address" ("or a BGP `cluster` is anonymized ... THEN it is unchanged"); `tests/corpus/test_device_anonymization.py` `_SYNTAX_BEFORE`.
- Counterexample: executed by the Reviewer (`roles/review/p_leaks.py` E): `set routing-options router-id 203.0.114.1`, `ipv6-router-id 203.0.114.1` and `bgp group IBGP cluster 203.0.114.1` with `--anonymize-ips`: the router ID becomes a pseudonym, the other two keep `203.0.114.1`; base and head alike. The strengthened proof (S5) found the same for route distinguishers (`10.255.0.1:100`, 75,279 JVD values).
- User impact: the published output pairs each pseudonym with its original loopback.
- Proposed correction: these leaves take an address; retype them in the schema model once a device artefact settles `cluster`'s accepted forms (change 18).
- Decision: Pending owner decision. Interim action: a leaf-name allowance in the IP rule (`_ADDRESS_VALUED_LEAVES`: `ipv6-router-id`, `cluster`, `route-distinguisher rd-type`, `vrf-target` `community`/`import`/`export`), only for types `string`/`areaid`, retiring with change 18; measured in `blast_s4.out` (owner intake 2026-10-11: merge with recorded interim action).

### S5: the proofs counted only whole-word addresses

- Artifact: the evidence-freeze criterion "no address of the capture survives", as `combos.py` `addrs()` and the corpus law implemented it.
- Counterexample: executed by the Reviewer: an address inside a word (`http://addr:port/`, `peer=addr`) was invisible to both, so finding 1 passed every gate.
- User impact: a leak of that shape passes every gate.
- Proposed correction: both proofs also scan each run of address characters inside a word with plain `ipaddress`, independent of the product's tokenizer.
- Decision: Pending owner decision. Interim action: applied in `tests/corpus/test_device_anonymization.py` and `combos.py`; it revealed the route distinguishers, fixed under S4 (owner intake 2026-10-11: merge with recorded interim action).

## Verdict

<!-- Filled by the fresh Reviewer at STOP-R. -->
