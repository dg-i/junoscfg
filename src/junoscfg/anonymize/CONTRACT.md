# junoscfg.anonymize — contract

Interface: `__all__` in `__init__.py`, module entry and expose list in `tach.toml`.

## Not for

Not reversible without the mapping, and not idempotent: `anonymize()` writes a
generated salt back into the config you pass, so a reused config keeps one salt.
Not quiet at `log_level="debug"`: it pairs each original with its replacement.

## Invariants

- `anonymize()` copies the IR it is given and never changes it; `walk()` and `apply_revert()` rewrite theirs in place, as documented — enforced by `tests/unit/anonymize/test_integration.py::TestAnonymizeLeavesItsInputAlone`.
- No rule's warning or error names an original or its replacement — enforced by `tests/unit/anonymize/test_as_number_rule.py::TestAsNumberConflictDetection::test_no_warning_pairs_an_original_with_its_replacement` and `tests/unit/anonymize/test_ip_rule.py::TestAPassThroughCollision::test_the_error_names_no_address`.
- The same input and the same salt produce the same output, every run — enforced for every rule by `tests/contract/test_every_rule.py::TestEveryRule::test_the_same_salt_gives_the_same_output`.
- No per-password field of the original survives: not the salt, and for `$8$` not the IV or the tag — enforced by `tests/unit/anonymize/test_password_rule.py::TestSaltIsNotCopied`.
- `networks=["auto"]` needs `source_text` and says so — enforced by `tests/unit/anonymize/test_ip_rule.py::TestNetworksAutoNeedsSourceText`.
- Unplaced content is never refused nor passed unannounced: words known by shape are replaced, its path is in `AnonymizeResult.unplaced` — enforced by `tests/unit/anonymize/test_integration.py::TestContentTheWalkCannotPlace`.
- A wildcard name (`<*>` in a group) is a pattern: `*` alone passes every rule, any other keeps its brackets, and one that selects other names once anonymized or that no rule could rewrite is named in `AnonymizeResult.patterns`; revert restores it — enforced by `tests/unit/anonymize/test_integration.py::TestAWildcardNameIsAPattern` and `tests/contract/test_every_rule.py::TestEveryRule::test_a_match_all_wildcard_name_passes`.
- A value inside free text (a URL, a description, an annotation, an `apply-path`'s names) goes to the rule that owns its shape, and no rule rewrites text another wrote; revert undoes each replacement once — enforced by `tests/unit/anonymize/test_walker.py::TestValuesInsideFreeText`, `tests/unit/anonymize/test_walker.py::TestAnApplyPathNamesConfiguration` and `tests/unit/anonymize/test_revert.py::TestRevertUndoesEachReplacementOnce`.
- A schema enum value or the keyword of a key choice is syntax and passes the rules unchanged — enforced by `tests/unit/anonymize/test_walker.py::TestKeyFieldsAreLeaves::test_an_enum_key_passes_unchanged` and `tests/unit/anonymize/test_walker.py::TestKeyFieldsAreLeaves::test_a_key_choice_keyword_passes_unchanged`.
- Flat IP maps must invert without choosing between originals: distinct spellings sharing one replacement are rejected before anonymized output or any public revert mutation. Unambiguous legacy maps remain supported — enforced by `tests/unit/anonymize/test_walker.py::TestValuesInsideFreeText::test_ambiguous_spellings_are_rejected_before_output`, `::test_an_unambiguous_spelling_restores_exactly`, `::test_an_ambiguous_legacy_map_is_rejected_before_output`, and `tests/unit/anonymize/test_revert.py::TestRevertUndoesEachReplacementOnce::test_an_ambiguous_ip_map_is_rejected_before_mutation`.
- Apply-path literal and wildcard selectors report changed selection through `patterns` by their own schema path, including excluded selectors left unchanged; match-all and harmless selectors stay quiet — enforced by `tests/unit/anonymize/test_walker.py::TestAnApplyPathNamesConfiguration::test_filtered_selector_meaning_is_reported`.

- Original URL users/passwords belong to their active credential rules before nested address/pattern processing; generated URL delimiters cannot change that ownership. A wildcard answer keeps its generated spans protected while untouched surrounding text reaches later rules. Existing Rule subclasses retain the two-item wildcard answer and need no new hook — enforced by `tests/unit/anonymize/test_walker.py::TestValuesInsideFreeText::test_original_url_credentials_keep_their_ownership` and `TestAnApplyPathNamesConfiguration::test_an_ip_wildcard_replacement_is_protected`, `::test_surrounding_original_text_still_reaches_later_rules`, `::test_an_existing_custom_wildcard_rule_needs_no_new_hook`.

## Precedent

- `junoscfg.anonymize.anonymize(..., diagnostic_sink=...)` — debug events leave through a caller-owned sink (the address anonymizer's own debug warnings go to stderr).
- `junoscfg.anonymize.rules.ip.IpRule` — the rule shape: `matches()` then `transform()` for a whole value, `spans()` for the parts of free text.
