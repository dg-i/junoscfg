# junoscfg.anonymize — contract

Interface: `__all__` in `__init__.py`, module entry and expose list in `tach.toml`.

## Not for

Not reversible without the mapping, and not idempotent: `anonymize()` writes a
generated salt back into the config you pass, so a reused config keeps one salt.
Not quiet at `log_level="debug"`: it pairs each original with its replacement.

## Invariants

- `anonymize()` copies the IR it is given and never changes it; `walk()` and `apply_revert()` rewrite theirs in place, as documented — enforced by `tests/unit/anonymize/test_integration.py::TestAnonymizeLeavesItsInputAlone`.
- No rule's warning or error names an original or its replacement — enforced by `tests/unit/anonymize/test_as_number_rule.py::TestAsNumberConflictDetection::test_no_warning_pairs_an_original_with_its_replacement` and `tests/unit/anonymize/test_ip_rule.py::TestAPassThroughCollision::test_the_error_names_no_address`.
- The same input and the same salt produce the same output, every run —
  enforced for every rule by
  `tests/contract/test_every_rule.py::TestEveryRule::test_the_same_salt_gives_the_same_output`.
- No per-password field of the original survives: not the salt, and for `$8$` not the IV or the tag — enforced by `tests/unit/anonymize/test_password_rule.py::TestSaltIsNotCopied`.
- `networks=["auto"]` needs `source_text` and says so — enforced by `tests/unit/anonymize/test_ip_rule.py::TestNetworksAutoNeedsSourceText`.
- Unplaced content is never refused nor passed unannounced: words known by shape are replaced, its path is in `AnonymizeResult.unplaced` — enforced by `tests/unit/anonymize/test_integration.py::TestContentTheWalkCannotPlace`.
- A schema enum value or the keyword of a key choice is syntax and passes the
  rules unchanged — enforced by `tests/unit/anonymize/test_walker.py::TestKeyFieldsAreLeaves::test_an_enum_key_passes_unchanged` and `tests/unit/anonymize/test_walker.py::TestKeyFieldsAreLeaves::test_a_key_choice_keyword_passes_unchanged`.

## Precedent

- `junoscfg.anonymize.anonymize(..., diagnostic_sink=...)` — debug events leave
  through a caller-owned sink (the address anonymizer's own debug warnings go to stderr).
- `junoscfg.anonymize.rules.ip.IpRule` — the rule shape: `matches()` then
  `transform()`, both taking the shared signature.
