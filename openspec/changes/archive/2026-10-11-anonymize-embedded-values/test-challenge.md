# Test/Challenge: anonymize-embedded-values (STOP-T)

Independent Test/Challenge role (phase 4, high-risk floor). Inputs: the change folder at head
`0c3bb38` (proposal, delta, evidence freeze, review.md S1/S2), `docs/how-to/run-a-batch-of-changes.md`,
the acceptance tests of `bee5ad3`, and the product code of base `50b0a10` (the worktree has no
product change yet). All values are synthetic. Probes live in this folder:

| Probe | What it runs |
|---|---|
| `probe_lexical.py` | `address_tokens`, `IpRule.transform`, `PasswordRule.lexical` on adversarial words |
| `probe_comments.py`, `probe_annotations.py`, `probe_annotations2.py` | annotations through each reader and writer, anonymized |
| `probe_revert_and_v6.py` | revert with replacements sharing a prefix or nested in a pseudonym; IPv6 forms that embed an IPv4 address |
| `probe_vacuous.py` | which `gone` items of `_FREE_TEXT` disappear with no anonymization at all |
| `probe_second_half.py` | the group/AS half of `test_text_one_rule_wrote_is_never_rewritten` on its own, on the base |

## Verdict on the baseline

- Base run reproduced: 36 fail, 17 pass. Every failure is an assertion failure, with no import,
  fixture or collection error. The failure lines match the defect each test names, with three
  caveats (T8). The group/AS half of `test_text_one_rule_wrote_is_never_rewritten` is never reached
  on the base because the first half fails first. Run on its own (`probe_second_half.py`, salt
  `salt-1`, digits `456`), it also fails on the base, for the right reason (NEW-R17).
- The tests check meaning, not layout. The exception is the pin
  `test_an_address_that_is_the_whole_value_answers_by_the_type`, which compares one exact set line.
  That is acceptable for a pin.
- No oracle is weakened. `test_ips_in_strings_disabled_by_default` asserted the ANON-P5 leak and its
  replacement follows the delta. The three `test_integration.py` edits are deferred and declared.
- The scans have large gaps. No new test holds an IPv6 address, a `$9$` hash, an annotation, an
  `include` filter, a transparent container in an `apply-path`, or a stderr check (grep of
  `git diff 50b0a10..HEAD -- tests`: 0, 0, 0, 0, 0, 0). An implementation that leaks each of the
  executed counterexamples below passes all 53 tests.

## Findings, ranked

### T1 (high, leak): annotations are free text that no rule ever sees

- Evidence (`probe_annotations.py`, `probe_annotations2.py`). Two inputs were tried. The first is the
  device's own capture `tests/data/device/synthetic/vmx-23.2R2-S7.5/junoscfg-oracle.json.gz` (vMX,
  23.2R2-S7.5), with `/* router-id is the loopback */` edited to hold `203.0.114.77`. The second is a
  synthetic `"@": {"comment": "/* peer 203.0.114.7 via scp://operator:secret99@203.0.114.8/x key
  $9$ExAmPlEhAsH.KEY */"}`. Both were converted JSON to JSON and JSON to YAML with
  `ips, identities, passwords`. Every original survives: both addresses, `operator`, `secret99` and
  the hash. The walker skips every key starting with `@` (`walker.py`, `_Walker.node`), so a Junos
  JSON annotation (`"@"`, `"@<leaf>"`) is never offered to any rule. The structured and set writers
  drop annotations, so those outputs do not leak. In this probe the XML and curly readers do not
  carry the annotation text.
- Coverage: the only comment row, `comments-holding-syntax`, is vacuous for anonymization. The
  curly reader drops `/* ... */` and `#` comments, so `203.0.114.7` and `203.0.114.8` are already
  gone with anonymization off (`probe_vacuous.py`).
- Proposed test: in `tests/unit/anonymize/test_walker.py::TestValuesInsideFreeText`, add
  `test_an_annotation_is_free_text`. Run the synthetic `"@"` and `"@router-id"` comments through
  `convert_config(..., from_format=JSON, to_format=JSON|YAML)` and through `junoscfg convert -i json
  -e json` with `--anonymize-ips --anonymize-identities --anonymize-passwords`. Assert that none of
  the five originals is in the output, and that the revert map restores the IR. This is
  specification challenge S3.

### T2 (high, leak): the address tokenizer misses common prose and IPv6 forms

The delta makes `address_tokens` "the one answer" for an address in text. Executed
(`probe_lexical.py`), each of these returns no token, so the address survives in free text:

| Text | Tokens |
|---|---|
| `see 203.0.114.6.` (end of a sentence) | none |
| `see 203.0.114.6...` | none |
| `lo_3ffe:b00::1` | none |
| `host:3ffe:b00::1` | none |
| `3ffe:b00::1.` | none |
| `203.000.114.006`, `203.0.114.06` (zero-padded) | none |

`(203.0.114.6)`, `ip=203.0.114.6;`, `x203.0.114.6y`, `peer-3ffe:b00::1` and `[3ffe:b00::1]:179` are
found. The how-to's rows `host:<ip>` and `lo_<ip>` are tested only with IPv4, and no `_FREE_TEXT` row
holds IPv6 or ends a sentence with an address.

- Proposed rows for `_FREE_TEXT`:
  - `"prose-v6"`: `description "peer [3ffe:b00::1]:179 lo_3ffe:b00::2 host:3ffe:b00::3 see 3ffe:b00::4."`,
    with `{"ips": True}`, gone `{"b00::1", "b00::2", "b00::3", "b00::4"}`, kept `{"]:179", " lo_", " host:", " see "}`.
  - `"prose-sentence"`: `description "Uplink to 203.0.114.6. Backup 203.0.114.7..."`, gone both
    addresses, kept `{"Uplink to ", ". Backup "}`.
- Negative row: `snmp view V oid 1.3.6.1.4.1.2636` and the prose `version 1.2.3.4.5` stay. The fix
  for the trailing dot must not start matching OID fragments.
- Zero-padded and hex forms are a decision for the owner (S5). Either replace or report them, or
  record them as accepted.

### T3 (high, leak): IPv6 forms that embed an IPv4 address keep it

- Evidence (`probe_revert_and_v6.py`): `IpRule.transform` returns `::ffff:203.0.114.5`,
  `::203.0.114.5` and `64:ff9b::203.0.114.5` unchanged, because ipanon passes those blocks through.
  `203.0.114.5` written alone is replaced. Under `--anonymize-ips` the IPv4 address therefore
  survives whenever it is written in the mapped form. The base already does this on address leaves;
  this change extends the same rule to all free text.
- Proposed test: `test_ip_rule.py::TestTheLeafsTypeAnswers::test_an_ipv4_address_inside_an_ipv6_form_is_replaced`.
  Use `description "nat64 64:ff9b::203.0.114.5 mapped ::ffff:203.0.114.5"` and
  `next-hop ::ffff:203.0.114.5`. Assert that `203.0.114.5` is absent and that the mapping restores
  it. This is specification challenge S5.

### T4 (high, leak): a `$9$` hash in prose is untested and is not recognised beside punctuation

- No new test holds a password hash inside placed free text, so a chain that leaves out the
  password-hash shape passes every test. On the base, `description "old key $9$ExAmPlEhAsH.KEY"`
  survives `--anonymize-passwords`: `matches` requires the hash at the start of the value.
- `PasswordRule.lexical` uses `^\$(?:sha1|[0-9]+[a-z]?)\$` on a whitespace-delimited word. It returns
  nothing for `pw=$9$ExAmPlEhAsH.KEY`, `($9$ExAmPlEhAsH.KEY)`, `'$9$ExAmPlEhAsH.KEY'` and
  `key:$9$ExAmPlEhAsH.KEY` (`probe_lexical.py`).
- Proposed row `"a-hash-in-prose"`: `description "rotated: old $9$ExAmPlEhAsH.KEY, (key=$9$ExAmPlEhAsH.KEZ)"`
  with `{"passwords": True}`, gone `{"ExAmPlEhAsH"}`, kept `{"rotated: old ", "(key="}`. Add the
  same text through content the walk cannot place (an unknown key from JSON) as a second row.

### T5 (medium-high): two revert hazards remain untested; both are order-dependent on the base

Executed with `apply_revert` (`probe_revert_and_v6.py`):

- (a) Replacements that share a prefix. With `{"password": {"first-secret": "netconanRemoved1",
  "tenth-secret": "netconanRemoved10"}}`, the text `ftp://operator:netconanRemoved10@198.51.100.1/x`
  reverts to `first-secret0` in one order and to `tenth-secret` in the other. URL passwords
  (NEW-R16) put `netconanRemoved<n>` inside free text for the first time, so this path is new. The
  rule "a number only between non-digits" does not cover it; only "longest first" does.
- (b) An AS replacement inside another rule's pseudonym. With `identity: operator ->
  user_ab64497cd0123456789abcde` and `as_number: 64496 -> 64497`, the text
  `scp://user_ab64497cd…@198.51.100.1/x AS64497` gives `scp://operator@… AS64496` in one order and
  `scp://user_ab64496cd…@… AS64496` in the other.
- Proposed tests in `test_revert.py::TestRevertUndoesEachReplacementOnce`:
  `test_replacements_sharing_a_prefix_revert_longest_first` (a) and
  `test_a_number_inside_a_pseudonym_is_no_number` (b). Run each in both mapping orders.

### T6 (medium): "never re-offered" is tested only on whole values

`test_text_one_rule_wrote_is_never_rewritten` uses `router-id`, `neighbor` and a group name, which
are all whole values a rule takes. Free text, where the new chain does its work, is not tested. A
chain that feeds each rule's output to the next rule, as `_Walker._chain` does on the base, passes
it. Proposed parametrised test `test_text_one_rule_wrote_inside_free_text_is_never_rewritten`:

| Input | Options | Assertion |
|---|---|---|
| `description "via 203.0.114.7"` beside `router-id 203.0.114.7` | `ips`, `sensitive_patterns=[r"\d{3}"]` | the description holds `mapping["ip"]["203.0.114.7"]` |
| `archive-sites "scp://operator@198.51.100.1/x"` | `identities`, `sensitive_words=["user"]` | the URL holds `//{mapping["identity"]["operator"]}@` |
| the same | `identities`, `as_numbers=[<digits found in the pseudonym by salt search>]`, `as_numbers_in_strings` | the same (NEW-R17 in free text) |
| `ftp://operator:secret99@198.51.100.1/x` | `passwords`, `sensitive_patterns=[r"\d+"]` | the URL holds `mapping["password"]["secret99"]` |

### T7 (medium): `apply-path` reader cases are missing

The tree marks `interfaces` and `routing-instances` as transparent containers (`t` = `interface`,
`instance`). The most common real `apply-path` forms cross them, and no test does. Rows to add to
`TestAnApplyPathNamesConfiguration`:

- `apply-path "interfaces <*> unit <*> family inet address <*>"`, all rules: unchanged, absent from
  `unplaced` and `patterns`.
- `apply-path "routing-instances CUST-A protocols bgp group <*> neighbor <*>"` beside instance
  `CUST-A`, `sensitive_words=["cust"]`: the path names the instance's new name, and `CUST` is absent.
- `apply-path "protocols bgp group neighbor neighbor <*>"` beside `group neighbor` (junoscfg reads
  it; Junos acceptance unconfirmed), `groups`: the first `neighbor` is renamed and the second
  stays. A reader that asks "is this word a keyword here?" before "is this the key after a list
  keyword?" keeps the name.
- `apply-path "protocols ospf area 0.0.0.0 interface <*>"` beside `protocols ospf area 0.0.0.0`,
  `ips`, `ignore_reserved`: the path takes the area's replacement, matching the list-name rule (S3
  of the earlier change).
- Every readable row asserts `result.unplaced == ()`. As written, an implementation that names every
  `apply-path` in `unplaced` passes.

### T8 (medium): vacuous assertions and unnamed pins

- `test_an_address_that_is_the_whole_value_answers_by_the_type[from-area]` cannot fail. ipanon keeps
  `0.0.0.0` unless `ignore_reserved` is on (`IpRule.transform("0.0.0.0") == "0.0.0.0"`; with
  `ignore_reserved` it gives `233.113.141.75`). The delta's scenario for this case says
  `--anonymize-ignore-reserved` is on. Correction: pass `ignore_reserved=True` in that row.
- The comment half of `comments-holding-syntax` is vacuous (T1).
- `an-as-number-inside-a-name` fails on the base only because of `203.0.114.6`. The base's strings
  pass already rewrote `AS64496`, so the AS half is a pin that the freeze does not name. Split the
  row or name it.

### T9 (medium): URL userinfo is tested in one shape only

Only lowercase `scp://` and `ftp://` with a simple user and password are tested. Rows to add:

- `FTP://Operator:Secret99@203.0.114.6/x`, an uppercase scheme.
- `ssh://operator@203.0.114.5:2222/x`.
- `https://operator:secret99@[3ffe:b00::5]:8443/x`.
- A password holding `:` and `@`: `ftp://operator:p@ss:w0rd@203.0.114.6/x`. A userinfo regex that
  stops at the first `@` leaks `ss:w0rd`. This is specification challenge S6.
- Negatives, unchanged under `identities` and `passwords`: `scp://203.0.114.5/path` (no userinfo,
  apart from the address under `ips`) and `description "mail noc at example"`.

### T10 (medium): the filters are tested for one rule and one direction

`test_the_filters_apply_inside_free_text` uses only `exclude` and only addresses. Parametrise it
over `identities`, `passwords`, `as_numbers_in_strings`, `sensitive_words` and `include=["routing-options"]`.
Add an `apply-path` whose named list is excluded (`exclude=["protocols.bgp"]`): the group keeps
`EBGP`, and so must the path, or the prefix list stops selecting. Which filter governs a name inside
an `apply-path` is not specified (S7).

### T11 (low-medium): doors and writers

- The free-text rows read only set and curly input, write only set output, and check the CLI's
  stdout only (`result.stdout`). Assert on `result.output` (stdout and stderr), and add JSON input
  with JSON and YAML output; the annotation leak (T1) shows only there.
- `tests/contract/test_every_message.py` has no door for the new reports: the `apply-path` named in
  `unplaced`, and the `apply-path` pattern warning. Add `cli-anonymize-apply-path-warning`
  (`apply-path "protocols bgp bogus-acme EBGP-ACME 203.0.114.7"`) and a pattern row. Both are
  checked against `MARKER`, `DOTTED_QUAD` and the pseudonyms.

### T12 (low)

- An AS number inside an IPv6 address: an IPv6 group holds at most 4 hex digits and every
  test-data AS number has 5, so the case is reachable only with an AS number outside the test-data
  range. Record it as not applicable, or rely on "never inside an address" being implemented
  through `address_tokens`, which covers IPv6 too.
- A key and its reference holding an address beside text: `prefix-list PL-203.0.114.0/24` and
  `from prefix-list PL-203.0.114.0/24` are rewritten identically.
- Determinism: anonymize `_FREE_TEXT` twice with one salt and get the same output (the AS sequence
  and `netconanRemoved<n>` are order counters).
- A template in userinfo, `scp://${user}@203.0.114.10/`: the identity rule renames `${user}` and
  breaks the template. Revert restores it, but it is worth a recorded decision.

## Specification challenges (review.md format)

### S3: annotations are free text

- Artifact: `openspec/changes/anonymize-embedded-values/specs/anonymization/embedded-values/spec.md`,
  "A value inside free text goes to the rule that owns its shape" (it names placed values and
  content the walk cannot place, not annotations); `walker.py` skips `@` keys.
- Counterexample: executed in `probe_annotations2.py`. The device JSON form of
  `tests/data/device/synthetic/vmx-23.2R2-S7.5/junoscfg-oracle.json.gz` (vMX, 23.2R2-S7.5) was edited
  so the annotation holds `203.0.114.77`. Anonymized with `ips`, converted JSON to JSON and JSON to
  YAML, the address survives. The synthetic annotation in `probe_annotations.py` keeps an address,
  a URL user, a URL password and a `$9$` hash under every rule.
- User impact: a user who anonymizes a Junos JSON export publishes every address, user, password and
  hash written in a comment.
- Proposed correction: an annotation's text (`"@"`/`"@<key>"` `comment`, and the XML or curly
  annotation wherever a reader keeps it) is content the walk cannot place. The chain rewrites it by
  shape, and its schema path is named in `unplaced`. Alternative: drop annotations from an
  anonymized run and say so in one value-free warning.
- Decision: pending the owner. Interim action, safe and reversible: the proposed correction. It
  replaces more and never less, and the mapping restores it.

### S4: a whole-value address on a free-text leaf survives `--anonymize-ips` silently

- Artifact: delta `embedded-values` ("A part that is the whole value SHALL be replaced only where its
  rule takes the value"); placed-values "The IP rule answers by the leaf's type".
- Counterexample (executed on the base, unchanged by the delta): `set interfaces ge-0/0/0 description
  203.0.114.9`, `set snmp location 203.0.114.9` and `set snmp contact 3ffe:b00::9` with `ips` are
  output unchanged, with 0 warnings. `description "to 203.0.114.9"` is replaced under the interim S1
  rule. The `snmp view oid` key and `description` are both `xsd:string`, so the type cannot tell
  them apart.
- User impact: an address written alone in a description is published. That breaks the
  placed-values purpose ("never claims success while a value it could replace survives
  unannounced"), and the outcome depends on whether a word stands beside the address.
- Proposed correction: under `ips`, replace a whole-value address on a string leaf except on a
  closed list of syntax leaves (the `snmp view oid` key, `areaid` references), or name its path in a
  value-free report. `ips_in_strings` then adds only those syntax leaves.
- Decision: pending the owner. Interim action: report the path, which is safe, changes no output,
  and is reversible.

### S5: address forms the address anonymizer keeps or cannot parse

- Artifact: `anonymize/rules/__init__.py::_ADDRESS_TOKEN` and `IpRule`, which this change makes the
  one answer for free text.
- Counterexample (executed, `probe_lexical.py` and `probe_revert_and_v6.py`): `::ffff:203.0.114.5`,
  `::203.0.114.5` and `64:ff9b::203.0.114.5` come back unchanged from the address anonymizer.
  `see 203.0.114.6.`, `lo_3ffe:b00::1`, `host:3ffe:b00::1`, `3ffe:b00::1.` and `203.000.114.006`
  give no token.
- User impact: an IPv4 address survives `--anonymize-ips` because of how it is written.
- Proposed correction: (a) a dot not followed by a digit ends an IPv4 address; (b) an IPv6 address
  may follow `_` or a non-hex word and a colon; (c) the IPv4 inside a mapped, compatible or NAT64
  form takes the IPv4 replacement; (d) a zero-padded dotted quad is replaced or reported.
- Decision: pending the owner. Interim action: (a) to (c), each with a negative OID row.

### S6: where a URL's userinfo ends

- Artifact: delta `embedded-values`, `scheme://user[:password]@`.
- Counterexample (constructed, not executed): `ftp://operator:p@ss:w0rd@203.0.114.6/x`. A split at
  the first `@` leaves `ss:w0rd` as host text. The scheme case (`FTP://`) is unspecified.
- User impact: part of a password is published.
- Proposed correction: the scheme matches in any case; the userinfo runs from `//` to the last `@`
  before the first `/` after it; the user ends at the first `:`.
- Decision: pending the owner. Interim action: the proposed correction (safe side).

### S7: which filter governs a name inside an `apply-path`

- Artifact: delta `embedded-values`, "An apply-path names configuration" ("offered to the rules as
  that key field's value at that path") and "`include`/`exclude` apply".
- Counterexample (constructed): `exclude=["protocols.bgp"]` keeps group `EBGP`. A path filter read at
  `policy-options.prefix-list.apply-path` renames `EBGP` in the path, the prefix list selects
  nothing, and the mapping gains a group entry that no group holds.
- User impact: a filtered run breaks the configuration it was meant to keep.
- Proposed correction: a name in an `apply-path` is rewritten only where both the `apply-path`'s
  place and the named key field's place are in scope.
- Decision: pending the owner. Interim action: the proposed correction (it rewrites less, never
  more).
