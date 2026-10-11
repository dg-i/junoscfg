# Test/Challenge: anonymize-every-placed-value (STOP-T)

Role: independent Test/Challenge (phase 4), context-isolated. Read: proposal, instruction-integrity
(C4-C13), evidence freeze, delta `anonymization/placed-values`, diff `3a0607f..4b61fe4` under `tests/`,
the base sources of `anonymize/walker.py`, `rules/ip.py`, `rules/group.py`, `convert/__init__.py`, `cli.py`.
Probes (synthetic values only) are next to this file: `probe_*.py`, `mutant_identity.py`. Every
counterexample was executed on the branch head, which has the base's product code (tests only).

## Verdict on the oracle

- The MISSED retirement does not weaken anything: the subtractions are gone, and `ONCE_MISSED` asserts the
  values are replaced and absent.
- The C4/C5 rewrites keep the "no address passes" half everywhere and replace only the refusal, as
  declared.
- The base failures are for the right reason. The corpus `.conf`/`.set` nodes fail on the refusal
  (`FieldValidationError`) and the others on survivors.
- Still, a wrong implementation can pass, through findings 1 to 5.

## Findings, ranked

### 1. HIGH: the corpus survival law cannot tell anonymized from passed through

`test_no_address_of_the_capture_survives` excuses every address the run's own mapping maps to itself.

Executed (`mutant_identity.py`, `preserve_prefixes=["0.0.0.0/0", "::/0"]`):

- `services-leaf1_qfx5130-48c.xml`: 213 of 213 device addresses left as written, and the law PASSES.
- `synthetic-probes.set`: 5 of 5 left as written, and the law PASSES.

The companion revert test passes as well, because other rules change the IR.

Proposed test: derive `kept_by_design` independently of the run, either from
`IpRule(AnonymizeConfig(ips=True, salt=...)).transform(a) == a` built fresh, or from
`ip_network(a).is_unspecified/is_loopback/is_multicast/is_reserved` plus 198.51.100.0/24. Then assert that
`addresses - kept_by_design` is non-empty.

### 2. HIGH: the `@` sibling of an unknown or joined key is not tested

The walker skips `@` keys. The JSON reader keeps `"@bogus 203.0.114.9 G": {"inactive": true}`.

The writers read that key:

- JSON and YAML print it verbatim.
- set and structured derive `deactivate` / `inactive:` from it (`probe_writers.py`).

An implementation that rewrites the key but not its sibling passes every test. It leaks the address in
JSON and YAML, and it silently drops `deactivate`, so the statement becomes active.

Proposed test: `_UNPLACED["joined-key-inactive"]` and a `_DOORS` JSON row with the sibling. Assert:

- the address is absent from the JSON and YAML output;
- the set output holds `deactivate system bogus <pseudonym> G-SECRET`;
- revert restores both keys.

### 3. HIGH: quoted words in the record

The set and curly readers keep `bogus "203.0.114.9"` and `bogus "peer 203.0.114.9"` with the quotes
(`probe_readers.py`). The forward tests hold no quoted address; only the revert test does. A
`str.split()` implementation passes everything and leaks `"203.0.114.9"`.

Proposed test: set and curly door rows with a quoted address and with a quoted multi-word value.

### 4. HIGH: a dict on a leaf, the other "shape its node does not take"

`_try_rules` calls `str(value)` on whatever it is given. Executed on the base: `router-id:
{"203.0.114.9": "203.0.114.10"}` comes out as the string `"{'203.0.114.9': '203.0.114.10'}"`. That is the
original addresses, the IR corrupted, and revert impossible.

`_UNPLACED` tests a scalar on a container, never the reverse. These shapes pass verbatim on the base and
are untested:

- a list of dicts under an unknown key;
- an IPv6 key;
- a prefix key.

Proposed test: `_UNPLACED` rows `dict-on-a-leaf`, `list-of-dicts-on-a-leaf`, `unknown-list-of-dicts`,
`ipv6-as-key` and `prefix-as-key`.

### 5. MEDIUM-HIGH: the value check crashes (the NEW-R8 class, only interface names tested)

`_looks_like_ip` is true for `203.0.114.9/rack-4`, `203.0.114.0/24,`, `/33`, `/129`,
`fe80::1%ge-0/0/0.0` and `203.0.114.9/`. `transform` raises `ValueError` on every one of them
(`probe_valuecheck.py`).

C6 makes `xsd:string` eligible, and `interfaces interface description` is `xsd:string`. So
`--anonymize-ips` on `description "203.0.114.9/rack-4"`, or the same word in a kept statement, crashes if
the head reuses the check.

Proposed test: `matches`/`convert_config` do not raise on these values on a free-text leaf, a typed leaf
and an unplaced word, and the address part does not survive.

### 6. MEDIUM: syntax values rewritten under C6, untested

- `snmp view V oid 1.3.6.1 include`: `oid.name` is `xsd:string`, and `1.3.6.1` becomes `145.252.156.238`.
- `protocols ospf area 0.0.0.0` becomes `233.113.141.75` under `--anonymize-ignore-reserved`. The backbone
  is lost. This is pre-existing, and C6 extends it to `from area` (`probe_area.py`).

Both contradict the freeze's "syntax values unchanged".

Proposed test: negative rows for both, or a strict xfail citing the owner's decision.

### 7. MEDIUM: group references

`apply-groups "${node}"` becomes a pseudonym that no group defines. `node0`, `node1` and `re0` are
renamed, which loses their per-node meaning (`probe_groups.py`). The corpus test excuses any reference
whose old name was not defined. That is weaker than the freeze's criterion, "every apply-groups names a
group the output defines".

Proposed test: every reference after the run is either defined or unchanged. Record a decision on
reserved names.

### 8. MEDIUM: lexical secrets in unplaced content (C13)

Under an unknown key, `$9$ExAmPlEhAsH.KEY` survives with `passwords=True`, and `acme` survives with
`sensitive_words=["acme"]` (`probe_shapes.py`).

`PasswordRule` strategy 3 and `SensitiveWordRule` are purely lexical, just as rule 5 is.
`test_every_other_word_is_left_as_written` would lock in such a leak. This needs a specification challenge
S2 for the owner, and a test pinning whichever way the owner decides.

### 9. LOW: findings 9 to 12

- **"Counts once" lost.** `set(result.unplaced)` hides duplicates. Proposed: compare the tuple, and add a
  `deactivate` line to the set door.
- **Two writers untested.** The door test writes only set and JSON. Proposed: add YAML and structured.
- **Validation messages quote the value.** Non-`UNPLACED` field-validation messages quote the value in an
  anonymized run: `ssh protocol-version 203.0.114.9` is shown in the diagnostic and in the strict error.
  Proposed: a row for an enum-only leaf (`{"l": True, "e": 16}`) in `TestTheLeafsTypeAnswers`, and extend
  `test_no_message_carries_an_original_value` to such an error. `log_level="debug"` prints originals by
  design.
- **No mechanised check on the re-pin.** Nothing stops the phase-5 re-pin from dropping entries. The
  Reviewer must diff `pin-base.json`.
