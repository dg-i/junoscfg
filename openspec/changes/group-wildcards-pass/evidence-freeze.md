<!-- Complete at the end of phase 2. Later instructions or evidence require a delta consistency check before affected work continues. -->

## Resolved instructions

- Owner brief and intake answers of 2026-10-11 (`instruction-integrity.md`): ID ANON-P3 (= NEW-C12), plan row 6; assurance `balanced`; fast-forward into local `master`, archive, tag, never push; a specification challenge merges with a recorded interim action (intake 3).
- C3 type `bug`, standard lane (the fix caps are exceeded). C4 the literal-text decision is specification challenge S1 (`review.md`) with the interim rule as the delta. C5 the warning names a schema path and a count only. C6 the test filters that hid the defect go. C7 the rule applies to entry key fields, every rule alike; free text written `<...>` stays data. C8 `apply-path` (NEW-A-N7) stays with change 7. C9 patch 0.20.1, not a break.

## Requirements

- `specs/anonymization/placed-values/spec.md`: ADDED "A wildcard name is a pattern, not a name".
- Unchanged and binding: `anonymization/placed-values` "A group reference goes to the group rule once" (reserved group names pass), "No message of an anonymized run quotes the configuration", "anonymize() leaves its input alone"; `anonymization/keyed-entries` "Key fields are leaves, and a leaf's own enum value is syntax" (the text inside a wildcard is offered as that key field's value, enum check included) and "No value anonymized before escapes" (the dumped mapping of the device example stays pinned at `8e13d961…`; the `<*>` entry the pin left out no longer exists).

## Evidence

Observed on `1ebeed9` (v0.20.0), synthetic values, `private_test_data/makeover-work/group-wildcards-pass/repro.py` and `repro-base.out`, `paths.py`:

| Input (a wildcard name in a group) | Rule | Base output | Selects the same names |
|---|---|---|---|
| `protocols bgp group <*>` (device example) | group | `group group_7d61…` (not a wildcard; defines a new BGP group) | no |
| `snmp view <*>` | group | the same `group_7d61…` | no |
| `system login user <*>` | identity | `user_…` | no |
| `protocols bgp group <EBGP>` beside `protocols bgp group EBGP` | group | `group_<hash of "<EBGP>">`, not the group's pseudonym | no |
| `protocols bgp group <EBGP-*>` beside `EBGP-A` | group | `group_41e4…` | no |
| `protocols bgp group <EBGP-*>` | sensitive word `ebgp` | `<word_2789…-*>`, `EBGP-A` to `word_2789…-A` | yes |
| `protocols bgp group "<[A-E]BGP*>"` | sensitive word `ebgp` | unchanged; `EBGP` to `word_2789…` | no |
| `neighbor <203.0.114.7>` beside neighbour `203.0.114.7` | ip | unchanged (the address survives in the wildcard) | no |
| `neighbor <203.0.114.*>` | ip | unchanged | no |
| `interfaces <ge-*>`, `unit <*>`, `routing-instances <VRF-*>` | none claims them | unchanged | yes |
| `description "wildcard ebgp"` under a wildcard entry | description | replaced | data, not a name |

- Revert restored the base outputs exactly in every row (`repro-base.out`: `revert exact: True`), through the exact or the substring pass.
- Walker paths (`paths.py`): the device example's wildcards reach the rules at `groups.interfaces.name`, `groups.interfaces.unit.name`, `groups.protocols.bgp.group.name`, `groups.routing-instances.instance.name`, `groups.protocols.isis.interface.name`, as entry key fields (`_Walker._is_key_field`).
- Device captures holding wildcard names (counted from the `.set.gz` renderings): `tests/data/device/synthetic/vmx-23.2R2-S7.5/junoscfg-oracle` and `.../qfx5120-25.2R2-S1.5/junoscfg-oracle` (`group <*>` twice, `interfaces <ge-*>`, `"<[gx]e-*>"`, `<xe-0/0/1*>`, `unit <*>`, `routing-instances <VRF-*>`, `isis interface <ge-*>`), `tests/data/device/jvd/vmx-23.2R2-S7.5/mdr1_acx7509` (`interfaces <*>`, `<ae*>`, `"<[egx][te]-*>"`, `unit <*>`, `interface <et-*>`). The devices accepted every one; none has literal text at a name a rule renames.
- The defect's tests: strict xfail `test_a_wildcard_group_name_passes_the_group_rule`; `test_no_value_anonymized_before_escapes` and `test_name_keyed_output_is_unchanged` filter out every original starting with `<` (C6).
- Junos semantics (Junos OS "Configuration Groups"): a wildcard in angle brackets selects names within a group; `*` any string, `?` one character, `[...]` and `[!...]` a character class. Python `fnmatch.fnmatchcase` implements the same syntax.

## Non-goals

As `proposal.md`: `apply-path` strings (NEW-A-N7, change 7, which must keep `<*>` inside a path as this change keeps a wildcard name); pseudonyms that keep a wildcard's literal text selecting the same names (S1).

## Acceptance criteria

- Every test id the delta names exists and `agent-ready reconcile` passes. Each fails on the merge base `1ebeed9` and passes after the change, except named pins: `test_the_mapping_restores_every_wildcard` and `test_a_description_written_as_a_wildcard_is_data` (base behaviour kept: revert and free text), the rows of `TestEveryRule::test_a_match_all_wildcard_name_passes` for rules that claim no name holding `<*>` on the base, the corpus rows of captures whose wildcards no rule claims (JVD), and `test_a_wildcard_that_selects_the_same_names_is_not_reported` rows whose output the base already gave (they fail on the base only for the missing `patterns`).
- The strict xfail `test_a_wildcard_group_name_passes_the_group_rule` is removed because it passes; the `<` filters of C6 go and the pinned SHA stays `8e13d961…`.
- Every rule passes a match-all wildcard at every name position of the contract configuration; every capture's wildcard names survive anonymization with every rule on, unreported; revert is exact for every wildcard of `repro.py` under each rule set.
- No message carries a value of the wildcard or of its names: a door row in `tests/contract/test_every_message.py` for the library and the CLI.
- `tests/unit/anonymize/`, `tests/contract/`, `tests/corpus/test_device_anonymization.py` green; `tests/unit/convert/` green.
- High risk floor: independent Test/Challenge (STOP-T) and a fresh Reviewer (STOP-R).

## Performance expectations

The walker records each entry name it hands the rules (path, original, replacement) and, only when a wildcard with text was met, compares selections over the names at the wildcard's place. Timed per the developer guide on the largest configuration under `private_test_data/` and on the device example, base and head; a record, never a gate.

## Outstanding decisions

None blocking: S1 is pending the owner with an interim action, which owner intake 3 permits to merge.

## Execution and checkpoint

- Assurance preference: balanced
- Risk floor: high (red zone `anonymize`, trust boundary, cross-domain `anonymization` and `conversion`)
- Roles required: Builder; independent Test/Challenge; fresh Reviewer at least as capable as the Builder; Finalizer duties run by the Builder under the owner's brief
- Resume point: phase 4 (acceptance tests). Phase 3 does not apply to type `bug`

## Delta log

<!-- Append source, change, consistency result, invalidated work, and rerun required. -->

- Freeze established after the proposal commit `30015bb` and the delta. Approved under the owner's unattended-run instruction of 2026-10-11.
- 2026-10-11, phase 4: acceptance tests written; on `1ebeed9`'s product code (`private_test_data/makeover-work/group-wildcards-pass/tests-on-base.out`) 39 fail and 18 pass, all named pins: `test_the_mapping_restores_every_wildcard` (7 rows: the base reverted its own output), `test_a_description_written_as_a_wildcard_is_data`, `TestEveryRule::test_a_match_all_wildcard_name_passes` for `password`, `ip`, `description`, `as-number`, `sensitive-word`, `sensitive-pattern` (no such rule claims `<*>` at a name on the base; `ssh-key`, `community`, `identity`, `group` fail), and the four `mdr1_acx7509` corpus rows (its wildcards sit at interface and unit names no rule renames). New finding while writing them, out of scope and carried: NEW-R13, the sensitive-word rule maps `ebgp` and `EBGP` to one pseudonym, so revert restores one case for both (`revert_sw.py`; the test text avoids two cases of one word). Checkpoint: STOP-T, independent Test/Challenge next; then phase 5. Approved under the owner's unattended-run instruction of 2026-10-11.
