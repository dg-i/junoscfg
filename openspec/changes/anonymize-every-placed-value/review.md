## Findings

<!-- Filled by the fresh Reviewer at STOP-R. -->

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

## Verdict

<!-- Filled by the fresh Reviewer at STOP-R. -->
