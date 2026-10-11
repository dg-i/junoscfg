# Test/Challenge: kept-whole-statements (phase 4, STOP-T)

Role: independent Test/Challenge, fresh context, working only from the committed
artefacts at `55ec2b2` (merge base `f0bb6aa`; `src/` on the branch is still the base).
Probes, all synthetic values, in this folder:

- `probe_challenge.py` / `.out`: the doors, writers, anonymization and edityaml
- `probe_schema.py` / `.out`: schema names, flag and value leaves, quote tokens
- `probe_anon.py` / `.out`: the public `anonymize()` on kept statements

## Do the tests fail on the base for the right reason?

Yes. The four files give 172 failed and 3,857 passed (5 xfailed), matching the freeze.
The failures are `AssertionError` (IR or output mismatch, `DID NOT RAISE`) and
`KeyError` from `kept_in(...)[statement]` lookups, which is the record being absent.
`test_the_display_door_names_the_record` fails on the missing import. None of them fail
on collection or on fixtures. The six `test_a_leaf_with_a_value_is_clean` guards pass on
the base, as they should.

## Findings, ranked

### F1 (high): C7. The tests require a regression on real device XML

Evidence:

- The device spells an empty value in all three of its formats, in the same capture
  (`tests/data/device/synthetic/vmx-23.2R2-S7.5/junoscfg-oracle.*` and the same on qfx):
  - set: `description ""`
  - JSON: `"description" : ""`
  - XML: `<description></description>`
- XML has no separate empty-string spelling, so `<description></description>` is the same
  document as `<description/>`. Both read as IR `[None]`, the same IR that
  `<host-name/>` gives.
- On the base, XML with an empty unit description converts with no diagnostic,
  anonymizes and passes strict mode (`probe_challenge.out` §1).
- `TestALeafWithoutItsValueIsUnplaced[xml]` requires `<host-name/>` to be `UNPLACED`,
  refused by strict mode and refused by anonymization. No implementation can tell
  `<host-name/>` from `<description></description>`. The test therefore forces an
  anonymization refusal and a `FieldValidationError` on device XML that holds
  `description ""`.
- The Builder's own count (`null_leaves.py`) is 12 hits in 10 captures, all
  `interfaces unit description`.
- No existing test will notice. Both tracked XML oracles are already refused on the base
  for 5 other UNPLACED statements, such as `shell` under user operator
  (`probe_challenge.out` §1b), so the device law hides this regression.
- The spec scenario contradicts itself on the XML door: it says "`<host-name/>` is
  UNPLACED" and also "`description ""` reports nothing".

Proposed correction. Option A is preferred and is the smallest step the evidence supports.

- **(A)** In this change, the XML reader reads an empty element of a value-taking leaf
  (`l` in the schema) as `""`. This is the device's spelling and amounts to DEV-16's
  one-line fix.
  - In `TestALeafWithoutItsValueIsUnplaced._SOURCES`, drop `xml`, or change its
    expectation to `set system host-name ""` with no `UNPLACED`.
  - Add `("xml", "<…unit><name>0</name><description></description></unit>…")` and the
    `<description/>` spelling to `test_a_leaf_with_a_value_is_clean`, expecting
    `description ""` in set output, no `UNPLACED`, a strict pass and an anonymization
    pass.
  - `known-differences.json` loses `xml-empty-value-lost` through
    `tools/device_differences.py`.
- **(B)** Exclude the XML door from the value-less-leaf report until change 9, correct
  the scenario to match, and run change 9 before the release that carries 0.17.0.

Either way, add a regression test that anonymizes and strict-converts a synthetic device
XML whose only special statement is the empty description.

### F2 (high): anonymization refuses only at the pipeline door. The public `anonymize()` leaks kept tokens

`_refuse_unplaced` runs only in `convert.pipeline_result`. `junoscfg.anonymize.anonymize(ir, cfg)`
is on the `consumer` surface and has no guard. `probe_anon.out` shows, on the base:

- `203.0.114.9` and `203.0.114.10` inside a kept statement leave unchanged.
- `G-SECRET` from `apply-groups G-SECRET G-OTHER` leaves unchanged, even with
  `ips_in_strings` and `groups` set.

The cause is that the second passes and the schema walker rewrite values, never keys. The
record moves this leak into one place but does not close it. Because the record is one
reserved key, the guard becomes cheap: if any `junoscfg:unplaced` record is non-empty,
`anonymize()` raises.

Proposed test: `anonymize()` called directly on the IR of
`set protocols bgp group G1 nonsense 203.0.114.9` raises `FieldValidationError`
("cannot anonymize"). The same test should use a record that arrives through JSON input.
The proposal's claim "anonymization still refuses it" should name both doors.

### F3 (high): a "verbatim" writer emits lines that were never statements

On the base, a JSON key holding `\n` produces a second, placed-looking set line. The
probe's key was `bogus\nset system root-authentication encrypted-password $9$ExAmPlEhAsH.KEY`.
A key holding `; } snmp { community public` breaks out of its block in structured output
(`probe_challenge.out` §2).

The record makes "print verbatim" the contract, and JSON and YAML input can now write
straight into it.

Proposed negative tests:

- A record key from JSON or YAML that holds a newline, an unquoted `;`, `{`, `}` or `#`,
  or unbalanced quotes is rejected or reported.
- Set output never has more lines than there are placed statements plus record entries.
- Structured output of every record key reads back as exactly that key.

### F4 (medium): C6's rationale is false, and the record can be malformed from JSON or YAML

The bundled schema holds 170 statement names with `:`, for example
`openconfig-interfaces:interfaces` and `ietf-netconf-acm:nacm` (`probe_schema.out`). The
claim "statement names hold no `:`" is therefore wrong. No name equals `junoscfg:unplaced`,
so nothing collides today; the rationale should say "a YANG module prefix junoscfg does
not own".

On the base, a JSON value under the reserved key that is a string or a list is written as
`set system junoscfg:unplaced host-name`.

Proposed tests:

- `set system junoscfg:unplaced host-name` is kept as the statement
  `junoscfg:unplaced host-name` inside the record, and does not forge a record.
- A colon-named schema statement is placed, not mistaken for a record.
- A JSON or YAML record whose value is a string, a list, a number, or a dict whose keys
  are not `@` keys is reported, without a crash and without being silently dropped.

### F5 (medium): edityaml treats the record as a container

`resolve_path(ir, "system.*")` returns the record's dict (`probe_challenge.out` §5). A
`static`, `copy` or `rename` rule or an ansibilize rule over `*`, or over a `pattern*`
glob, then writes fake kept statements into the record, and the writer prints them
verbatim. On the base, kept statements were `True` and were skipped.

Proposed test: `*` and dictglob segments skip `UNPLACED_STATEMENTS`, and a `static`
rule over `system.*` leaves the record unchanged.

### F6 (medium): wrong implementations that pass the tests

- **Re-quoting heuristic.** An implementation that adds quotes back to any token holding
  a space passes every quote test, because each quoted token in them has a space. The
  base loses `"abc"`, `"" gamma` (the empty token) and `"say \"hi\""`
  (`probe_schema.out`). Proposed test: parametrize `test_a_kept_statement_keeps_its_quotes`
  with `nonsense "abc" gamma`, `nonsense "" gamma`, `nonsense "alpha  beta"` and an
  escaped quote.
- **One report per record.** No test holds two kept statements at one level. An
  implementation that reports the record once, or only its first statement, passes.
  Proposed test: `set system bogus-a 1` plus `set system bogus-b 2` gives 2 `UNPLACED`
  reports, each naming its statement.
- **Flag leaves reported.** The "flag" negative case, `services ssh`, is a container.
  An implementation that reports every childless key with no value would flag the
  presence leaf `no-redirects` (schema `{'p': True}`) and still pass. Proposed test: add
  `no-redirects` as `null`, `[null]` and `true` to `test_a_leaf_with_a_value_is_clean`.
- **Other JSON spellings of a missing value.** A value-less leaf is tested in JSON only
  as `null`. `[null]` is what JSON output writes for XML-read empties, and `true` writes
  a bare line silently on the base. `[]` is dropped silently (§6). Proposed test: add
  all three to `_SOURCES`.

### F7 (low): coverage of the doors and formats

| Door | set out | structured out | JSON out | YAML out | Anonymize |
|---|---|---|---|---|---|
| set | yes | yes | yes | yes | pipeline only |
| structured | yes | yes | yes | yes | pipeline only |
| JSON | yes | yes | yes | yes | value-less leaf only |
| YAML | rows 1 and 2 | rows 1 and 2 | rows 1 and 2 | rows 1 and 2 | value-less leaf only |
| XML | value-less leaf (contested, F1) | – | – | – | value-less leaf |

XML output is not implemented, so it is not applicable.

Gaps:

- The quote row (`a-kept-statement-keeps-its-quotes`) has no YAML source. Its `!` and
  `"` inside a YAML key are the riskiest YAML spelling. Add one.
- No test covers the record at the library `anonymize()`, `apply_revert`, the audit
  walker, edityaml or ansibilize, or a CLI invocation.
- No anonymization-refusal test uses a record that arrives through JSON or YAML input.
- `_round_trip(...) == [placed, bare]` pins that placed lines come before kept ones, which
  is layout. Compare as sets, or say in the delta why the order is part of the contract.

### F8 (low): C5 is sound, but its record is incomplete

- The approved requirement text never said the valid line after a bare one is kept. Only
  the two test names did. Placing it matches the device: it loads `G1` and rejects the
  bare line, and set output still writes both lines. The override is therefore a test
  correction, not a weakening, and the new tests cover both orders.
- Phase 4 wants a specification challenge in `review.md` (Artifact, Counterexample,
  User impact, Proposed correction, Decision). There is none, and the resolution sits
  only in `instruction-integrity.md`. Add it.
- The main spec's `Tests:` line already names `..._is_placed`, while its requirement text
  is unchanged until phase 7. Record this in the delta log, which partly does so, and
  make sure phase 7 applies the text.
- Add the two non-colliding siblings to the "beside a placed node" parametrization as
  negatives: `apply-macro M1 a` with `apply-macro M1 a b c d`, and `apply-groups G0` with
  `apply-groups G1 G2`. The placed node is unchanged and there is one report.
