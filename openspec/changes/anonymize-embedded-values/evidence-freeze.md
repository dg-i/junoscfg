<!-- Complete at the end of phase 2. Later instructions or evidence require a delta consistency check before affected work continues. -->

## Resolved instructions

- Owner brief and intake answers of 2026-10-11 (`instruction-integrity.md`): IDs ANON-P5, NEW-A-N4, NEW-A-N5, NEW-A-N7, NEW-R13, NEW-R14 (ledger row 7); lane C, no serialized path; assurance `economy` under the high-risk floor; never push, merge, archive, bump or tag; a specification challenge merges with a recorded interim action (intake 3).
- C3 S1 (addresses inside free text under `ips` alone) and C4 S2 (a pseudonym per spelling) are pending the owner with interim actions (`review.md`). C5 a URL's user is an identity; its password (NEW-R15, found here) a secret. C6 revert undoes each replacement once. C7 the strings passes move into the walk (NEW-R16, found here). C8 an `apply-path` is read against the tree. C9 declared break on `consumer` and `cli`. C11 NEW-R17 recorded, not fixed.
- Coordination (`builder-kickoff.md`): `private_test_data/makeover-work/anonymize-embedded-values/files.txt`. One overlap with the live change `value-quoting-by-type`: `tests/unit/anonymize/test_integration.py` (it changes only the strict xfail marker of `TestKeyedEntriesSurvive::test_the_mapping_restores_the_set_output`). This change writes its acceptance tests elsewhere and does not edit that file until the orchestrator rules (reported at STOP-T). Phase 5 needs three edits there: the row `sensitive-word-other-case` of `test_a_wildcard_that_selects_other_names_is_reported` (S2: no longer reported), the docstring of `test_a_word_in_two_cases_reverts_to_each`, and the mapping pin `8e13d961…` of `test_name_keyed_output_is_unchanged` (the example's `CM-CUSTOMER` is upper case, so its pseudonym changes under S2).

## Requirements

- `specs/anonymization/embedded-values/spec.md` (new capability): ADDED "A value inside free text goes to the rule that owns its shape", "An apply-path names configuration", "Revert undoes each replacement once".
- `specs/anonymization/placed-values/spec.md`: MODIFIED "The IP rule answers by the leaf's type" (an address beside other text is replaced on any leaf; the route-distinguisher, VRF-target and community-member special cases become that rule).
- `specs/anonymization/wildcard-names/spec.md`: MODIFIED "A wildcard name is a pattern, not a name" (a wildcard's text is free text of the walk, no strings pass after it; NEW-R14; the revert exception goes; scenario "Sensitive words").
- Unchanged and binding: placed-values "Content the walk cannot place is named, its addresses replaced" (the same chain now also knows a URL's user and password and, under `as_numbers_in_strings`, an AS number), "No message of an anonymized run quotes the configuration", "anonymize() leaves its input alone"; keyed-entries "Key fields are leaves, and a leaf's own enum value is syntax"; the contract law of `tests/contract/test_every_rule.py` (each rule's mapping names every value it replaced, whole: the sensitive-word rule keeps recording whole values).

## Evidence

Observed on `50b0a10` (v0.20.4), synthetic values, `private_test_data/makeover-work/anonymize-embedded-values/repro.py`, output `repro-base.out`:

| ID | Input | Options | Base output | Defect |
|---|---|---|---|---|
| ANON-P5 | `archive-sites "scp://admin@203.0.114.5/path"`, `description "uplink to 203.0.114.6 port 3"` | `ips` | both unchanged, no diagnostic | leak |
| ANON-P5 | the same, `oid 1.3.6.1`, `from area 0.0.0.0` | `ips`, `ips_in_strings` | URL replaced; OID rewritten to `145.252.156.238` (NEW-R17); area kept | OID is syntax |
| NEW-A-N4 / NEW-R15 | login user `operator`; `"scp://operator@203.0.114.5/path"`, `"ftp://operator:secret99@203.0.114.6/x"` | `ips`, `identities`, `passwords`, `ips_in_strings` | user renamed, `operator` and `secret99` survive in the URLs | leak |
| NEW-A-N7 | `protocols bgp group EBGP`; `apply-path "protocols bgp group EBGP neighbor <*>"` | `groups` | group renamed, the path keeps `EBGP` | leak, prefix list selects nothing |
| NEW-A-N7 | the same | `sensitive_words=["bgp"]` | path becomes `protocols word_… group Eword_… neighbor <*>` | keyword rewritten, path broken |
| NEW-A-N7 | `neighbor 203.0.114.7`; `apply-path "... neighbor <203.0.114.*>"` | `ips` | neighbour replaced, the pattern kept | leak, selects nothing |
| NEW-R13 | `group EBGP description ebgp`, `description EBGP` | `sensitive_words=["ebgp"]` | all three `word_2789…`; revert gives `ebgp` for each | revert inexact |
| NEW-R14 | `groups GR interfaces <ge-0/0/1?>` | `as_numbers=[64496]`, `as_numbers_in_strings` | reported at `groups.interfaces` | false report |
| NEW-A-N5 | `description "AS64496 and AS6449612 and 64497"` | explicit map `64496:64497, 64497:64498`, in strings | revert gives `AS64496 ... 64496` | order-dependent substring loop |
| NEW-A-N5 | the inventory's address repro (`repro_revert_substring.py`) | revert only | `scp://admin@198.0.2.2/path`, exact | already fixed by change 5's address tokens |
| NEW-R16 | (code reading, `anonymize/__init__.py::_replace_as_in_strings`) | AS 100, in strings | the pass rewrites `100` inside `10.100.0.1` and digits inside any pseudonym's hex, and ignores `include`/`exclude` | wrong configuration, inexact revert |

- Device-capture blast radius (`blast.py`, `blast-base.out`): over every JSON capture in `tests/data/device/manifest.json`, the only placed values holding an address beside other text are 42 route distinguishers (`routing-instances route-distinguisher rd-type`, `string`), which the base already replaces (`_ADDRESS_VALUED_LEAVES`); whole-value addresses on non-address types are the `areaid` and syslog-host keys the base answers by list name. The only `apply-path` in the captures is `protocols bgp group <*> neighbor <*>` (vMX 23.2R2-S7.5 and QFX5120 25.2R2-S1.5 `junoscfg-oracle`, line 148 of the `.set.gz`). No capture holds a URL with a user.
- Device captures never exercise hand-written text, so the synthetic adversarial rows the how-to requires (one-line blocks, statements across lines, comments holding `;`, `{`, `}` and quotes, templates, prose, `10.255.0.1:100`, `target:<ip>:<n>`, `host:<ip>`, `lo_<ip>`) are the substitute for corpus coverage of the lexical scanning: `tests/unit/anonymize/test_walker.py::TestValuesInsideFreeText` (`_FREE_TEXT`).
- Existing tests the delta contradicts, the requirement wins: `tests/unit/anonymize/test_ip_rule.py::TestIpAnonymizeIntegration::test_ips_in_strings_disabled_by_default` asserts the ANON-P5 leak; it becomes `test_an_address_inside_free_text_is_replaced`. The three `test_integration.py` edits above (S2, the pin).

## Non-goals

As `proposal.md`: an SNMP OID rewritten under `ips_in_strings` (NEW-R17, change 18); an AS replacement that equals a number the configuration already holds (revert cannot tell them apart); hostnames inside URLs (no rule claims hostnames).

## Acceptance criteria

- Every test id the delta names exists and `agent-ready reconcile` passes. Each fails on the merge base `50b0a10` and passes after the change, except named pins: rows of `TestValuesInsideFreeText::test_each_value_inside_it_is_replaced` and `test_the_mapping_restores_each_row` the base already handles (an address in content the walk cannot place; a route distinguisher), `test_an_address_that_is_the_whole_value_answers_by_the_type` (base behaviour kept), `TestRevertUndoesEachReplacementOnce::test_a_replacement_inside_a_word_is_restored` (the base's substring loop did it), and `TestAnApplyPathNamesConfiguration::test_a_wildcard_in_it_is_a_pattern[match-all]` (`<*>` passed on the base).
- The before/after comparison (how-to) with `--anonymize`, each rule alone, all rules, and the in-strings options: every difference names an ID; the device-law and capture-anonymization tests stay green.
- No message carries a value: the existing door rows of `tests/contract/test_every_message.py` and `test_every_rule.py` stay green. The unplaced warning keeps its wording (address, password hash, sensitive word): a URL's user or password, or an AS number, that the chain also replaces in content the walk cannot place is not named, which understates a replacement and never claims one (placed-values: it "names only the shapes the active rules replace").
- `tests/unit/anonymize/`, `tests/contract/`, `tests/corpus/test_device_anonymization.py`, `tests/unit/convert/`, `tests/unit/cli/` green.
- High risk floor: independent Test/Challenge (STOP-T) and a fresh Reviewer (STOP-R).

## Performance expectations

The chain runs on every placed string value (the base ran it only after a rule took one, and two strings passes over every value after the walk). Timed per the developer guide on the largest configuration under `private_test_data/` and on the device example, base and head; a record, never a gate.

## Outstanding decisions

None blocking: S1 and S2 are pending the owner with interim actions, which owner intake 3 permits to merge. The shared-file overlap is the orchestrator's ruling (reported at STOP-T); no edit to that file happens before it.

## Execution and checkpoint

- Assurance preference: economy
- Risk floor: high (red zone `anonymize`, trust boundary, declared break on `consumer` and `cli`, cross-domain `anonymization` and `conversion`)
- Roles required: Builder; independent Test/Challenge; fresh Reviewer at least as capable as the Builder; Finalizer duties run by the orchestrator at merge
- Resume point: phase 4 (acceptance tests). Phase 3 does not apply to type `bug`

## Delta log

<!-- Append source, change, consistency result, invalidated work, and rerun required. -->

- Freeze established after the proposal commit `82633ff` and the delta. Approved under the owner's unattended-run instruction of 2026-10-11.
- 2026-10-11, phase 4: acceptance tests written, no product code; on `50b0a10`'s product code (`private_test_data/makeover-work/anonymize-embedded-values/tests-on-base.out`) 36 fail and 17 pass, all named pins: the two `address-forms-inside-words` rows of `test_each_value_inside_it_is_replaced` (route distinguishers and VRF targets, which the base replaced already), the 8 rows of `test_the_mapping_restores_each_row` (the base reverted its own output, which left these values as written), the 2 rows of `test_an_address_that_is_the_whole_value_answers_by_the_type`, `test_a_wildcard_in_it_is_a_pattern[match-all]` and `test_the_mapping_restores_it` of `TestAnApplyPathNamesConfiguration`, `test_a_replacement_inside_a_word_is_restored`, and the two reported rows of `TestAWildcardUnderAsNumbersInStrings` (`a-question-mark-in-the-number`, `a-class-in-the-number`). New evidence while writing them: on the base a sensitive pattern (`\d{3}`) rewrites the octets of an address the IP rule just wrote, through the walk's chain (`test_text_one_rule_wrote_is_never_rewritten`), the same class as NEW-R16. The curly reader refuses a statement whose words span lines (`description` then its value on the next line: "has no ';'", probe P7 pending); the across-lines rows use a quoted value and a `[ ]` list that span lines, which it reads. `test_ips_in_strings_disabled_by_default` became `test_an_address_inside_free_text_is_replaced`. `tests/unit/anonymize/test_integration.py` not edited (overlap). Checkpoint: STOP-T, independent Test/Challenge next; then phase 5. Approved under the owner's unattended-run instruction of 2026-10-11.
