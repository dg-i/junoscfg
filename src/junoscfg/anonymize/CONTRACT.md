# junoscfg.anonymize — contract

Interface: `__all__` in `__init__.py`, module entry and expose list in `tach.toml`.

## Not for

Not reversible without the mapping, and not idempotent: `anonymize()` writes a
generated salt back into the config you pass, so a reused config keeps one salt
across calls.

## Invariants

- The same input and the same salt produce the same output, every run —
  enforced by `tests/test_anonymize/test_ip_rule.py::TestIpRuleTransform::test_deterministic_with_same_salt`
  and the matching `test_deterministic` in each other rule's tests.
- No per-password field of the original survives: not the salt, and for `$8$`
  not the IV or the tag — enforced by
  `tests/test_anonymize/test_password_rule.py::TestSaltIsNotCopied`.
- `networks=["auto"]` needs `source_text` and says so rather than doing
  nothing — enforced by
  `tests/test_characterization.py::TestNetworksAutoNeedsSourceText`.
- A schema enum value or the keyword of a key choice is syntax and passes the
  rules unchanged — enforced by `tests/test_anonymize/test_walker.py::TestKeyFieldsAreLeaves::test_an_enum_key_passes_unchanged` and `tests/test_anonymize/test_walker.py::TestKeyFieldsAreLeaves::test_a_key_choice_keyword_passes_unchanged`.

## Precedent

- `junoscfg.anonymize.anonymize(..., diagnostic_sink=...)` — debug events leave
  through a caller-owned sink and never write to a terminal.
- `junoscfg.anonymize.rules.ip.IpRule` — the rule shape: `matches()` then
  `transform()`, both taking the shared signature.
