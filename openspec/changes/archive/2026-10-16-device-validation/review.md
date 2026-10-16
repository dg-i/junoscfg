## Specification challenges

### SC1: The yaml-new reader loads no schema artifact

- Artifact: `openspec/specs/conversion/junos-json-yaml/spec.md`, requirement "yaml-new input reads as the JSON object it spells": "a scalar leaf-list stays scalar, no schema artifact is loaded"; tests `TestJunosYamlReader::test_a_scalar_leaf_list_stays_scalar_without_loading_schema` and `TestLeafListPromotion::test_json_scalar_leaf_list_stays_scalar_without_loading_schema`.
- Counterexample: executed. The device's JSON writes `"ieee-802.3ad"` and `"end-range"` (every `junoscfg-oracle.json.gz`); the IR of the same configuration read from set, curly or XML holds `802.3ad` and `to`. One IR (ARCHITECTURE.md §8; coordinator ruling RC2a: readers derive the name from the tree node) needs the tree in the JSON and yaml-new readers, which then fail without artifacts.
- User impact: `to_dict(text, "json")` with a custom artifacts directory that lacks the structure tree now raises `ValueError` where it read; every conversion past the reader already needed the tree.
- Proposed correction: the MODIFIED requirement in `specs/conversion/junos-json-yaml/spec.md` (the reader loads the tree as every reader does; a scalar leaf-list stays scalar); the two tests assert the shape with the tree and the refusal without it.
- Decision: Pending owner decision. Interim: the coordinator's RC2a ruling (one rule, names read off the tree), reversible by restoring a static name table in the reader.

### SC2: JSON validation rejects the keyword junoscfg's JSON writer used to write (Test/Challenge TC7)

- Artifact: `.openspec.yaml` declared-break assessment; `validate_config(format="json")`.
- Counterexample: executed. Base wrote `"802.3ad": {"bundle": "ae0"}` for `set interfaces ge-0/0/0 ether-options 802.3ad ae0` and base `validate_config` accepted it; the change writes `"ieee-802.3ad"` and rejects `"802.3ad"` (`TestTheSchemaStillRejects`, row "the CLI keyword of a renamed element"). The JSON reader still reads the keyword.
- User impact: JSON a pre-change junoscfg wrote for a renamed statement fails `-v`; converting it still works. The production Ansible collection renders through `convert_config` at run time, which writes the device's spelling.
- Proposed correction: none to the rule (owner design: JSON validation follows the XSD's names); declared-break text corrected to say so. Device question D3 would settle whether a device loads `"802.3ad"` in JSON (no XML element can bear that name).
- Decision: Pending owner decision (when to retire the alias; D3). Interim, coordinator ruling on review B1, option (ii): the JSON and yaml-new schema take the keyword as a deprecated alias beside the element name, where the node records one (one rule from `x`); a patch, reversible. Superseded interim: reject.

### SC3: Six renames reach JSON without device evidence (Test/Challenge TC4)

- Artifact: `specs/schema-pipeline/conversion-hints/spec.md`, "A rename keeps the device's element name".
- Counterexample: no committed capture holds SNMP `name` (XSD `system-name`), the NAT rule `match` (`*-nat-rule-match`), an `ethernet-` speed or a community `=`/`+`/`-` (`equal-literal`, ...); only `end-range`, `ieee-802.3ad` and `hello-padding-type` are device-proven. JSON output and JSON validation now use the XSD's names for the six.
- User impact: if a device's JSON used the keyword for any of the six, JSON output would no longer load and JSON validation would reject the device's own JSON.
- Proposed correction: none until device evidence (D2); the XSD is the default model for XML and JSON names (ARCHITECTURE.md §8) and the owner's design names it.
- Decision: Pending owner decision. Interim: XSD names for all renames (one rule).

## Pending owner decisions and device questions

- P1 (coordinator (P)): undocumented statements are one Group D fix with a table (`_UNDOCUMENTED`, anchored on the parent's XSD type or its own and parent's name), not a new group: one fix, one table, the counts the docs carry stay per group.
- P2 (coordinator (P)): keyed singleton entries keep the path list (no general rule over the 309 candidate elements, as change keyed-single-entry-lists SC1 ruled), extended to `protocols isis-instance` and to the routing-instance, logical-system and tenant copies of all four paths (8 more SRGB `o` carriers, 26 more `L` nodes).
- P3 (coordinator (P)): "no validation message reprints a subtree" is a test-pinned invariant (`src/junoscfg/validate/CONTRACT.md`).
- D1: hold-time: does `commit check` pass with only `interfaces ge-0/0/1 hold-time down 0` (mdr1, group `GR-EDGE-INTF-MH`)? Recorded as `mandatory-open`.
- D2: device JSON and XML for `snmp name`, a NAT rule `match`, `ether-options speed 1g` and `then community = X` (SC3).
- D3: does a device load `"802.3ad"`/`"to"` in JSON (SC2)?
- D4: siblings of the undocumented statements no capture shows (grpc `clear-text address`, `system dump-on-panic`, `debugger-on-break`, `debugger-on-panic`).
- P4: `set chassis dump-on-panic` stays the one recorded grammar rejection (`grammar-corpus.json`). Re-checked: it is device output, a presence flag inside `<chassis><undocumented>` in the private renderings of JVD `ap1_mx304` on three devices, and in no committed capture; no XSD dump names it. Interim: not modelled, as the coordinator ruled (committed device evidence only). Owner: commit an `ap1_mx304` capture or admit the private evidence, and it joins `_UNDOCUMENTED` as one row.
- D5: whether a non-`set` verb may stop at a list or keyword before its name (`protect policy-options policy-statement`): the validator now accepts any path the grammar could continue.
- B1 (backlog candidate): the rest of `xml-element-name-leak` (rf_list, server-group, other-variables, bridge-domains domain, dynamic-tunnels) seen only in private captures: hidden list names, not renames; outside the one rule.
- B2 (backlog candidate): the no-op fixes (`route-filter-arg`, `source-address-filter-arg`, `classifiers-default`, `teardown-forms`, `single-hop`, `enable-interface`, `name-freeform`, and `wildcard-star`, which matches no element).
- B3 (backlog candidate): `-v` on XML input (no XSD ships).

## Independent Test/Challenge (phase 4)

A fresh Opus agent challenged the acceptance tests at `8a34263` against base `2d4904b`
(report kept in `private_test_data/makeover-work/device-validation/test-challenge.md`):
5 MUST, 6 SHOULD, 7 NICE. Every device fact the tests assert matched the captures' XML, JSON
and set; every expected finding is justified by the device's own `## Warning` or recorded
as open. Dispositions:

- TC1 (MUST, wrong `Tests:` id): isis-instance added to `TestKeyedSingletonLists.PATHS`,
  parametrised over every copy the fix covers; id corrected.
- TC2 (MUST, verbs in a form the device never prints): rows without the leaf's value; the
  validator takes a non-`set` path that stops before a value (`deactivate ... max-hello-size`);
  `TestEveryVerbNamesAStatementPath` in `tests/contract/test_every_door.py` over every door.
- TC3 (MUST, one IR not checked on the IR): the rename rows pin the `yaml` writer's IR dump
  (`never_written`/`written`), JSON and yaml-new spellings.
- TC4 (MUST, renames without device evidence): SC3, D2; the snmp row now spells `system-name`.
- TC5 (MUST, curly `-v` ran nowhere): `test_the_curly_rendering_validates_as_its_set_lines`.
- TC6 (SHOULD): the corpus tool and the opt-in test read every verb, private and committed lines.
- TC7 (SHOULD): SC2; negative row; declared-break text corrected.
- TC8 (SHOULD): door coverage moved to `test_every_door`; the second truncation site is gone
  with the "Line does not start" branch; unit tests use the minimal grammar only.
- TC9 (SHOULD): the message invariant runs through `validate_json`, `validate_yaml_as_json`
  and `validate_yaml`; the deep case pins its path.
- TC10 (SHOULD, strict branch dead after the fix): accepted; the test pins that strict mode
  does not escalate a recorded warning and fails if an error-class finding is recorded unraised.
- TC11 (SHOULD): `UNPLACED_IN_THE_EXAMPLE` and `placed_only` removed with their two duplicate
  tests; the anonymization pin held unchanged on the whole example (measured).
- TC12/TC15/TC16 (NICE): accepted as they stand (one element per rename; findings as a set;
  the warning classes are checked by hand, recorded in the class definitions).
- TC13 (NICE): negatives under `autoconf` and grpc `clear-text` in `TestTheSchemaStillRejects`.
- TC14 (NICE): `$foo-...` stays checked.
- TC17 (NICE): the presence wording corrected in the delta.
- TC18 (NICE): ARCHITECTURE.md §8, the guides, BACKLOG and `tach.toml` updated.

## Fresh review (phase 6, round 1)

Verdict: **Merge after fixes**, on `8c53843...297e9fe` (full check `77b313a`); the full text
and probes are in the coordinator's scratchpad (`review-dv/verdict.md`). Binding:

- B1: the declared-break record called a tightening of `validate_config` and `-v` "not a
  break" (JSON junoscfg ≤ 0.28.23 wrote with `"802.3ad"`/`"to"` failed). Resolution
  (coordinator ruling, option (ii), pending owner (P)): the keyword is a deprecated alias in
  the JSON and yaml-new schema where the node records an element name
  (`schema_generator._property_names`); `TestTheKeywordOfARenameIsADeprecatedAlias`; the
  negative row now pins that an element name is unknown where nothing was renamed; the
  record and changelog say "deprecated, still accepted" with the re-write migration.
- B2: any prefix of a non-`set` path was valid; the line stopping inside the route
  filter's key passed. Resolution: such a line is valid only when the grammar takes it with
  one value more (`SetValidator._takes_one_value`); the reviewer's counterexample is the door
  row `deactivate-inside-an-entry-key`. D5 stays pending.
- B3: no default-tier test validated the device's own verb lines. Resolution:
  `tests/corpus/test_set_corpus.py::TestEveryCaptureValidatesAsSet` validates every non-`set`
  line of every capture (28 lines; base rejected 5) with the session grammar.

Advisory:

- A1: the curly and verb checks moved to `test_set_corpus.py`, which already compiles the
  grammar; `test_device_renderings.py` no longer compiles it; its cost in
  `tools/verification-costs.json` refreshed by measurement (1.08 → 26.0 s serial: no tool
  writes the file; the full check's shards measured it at 44.6 s with the compile).
- A2: the undocumented leaves stay untyped: their XSD analogues carry no type the tree keeps
  (grpc `ssl port`, a ddos protocol's `aggregate bandwidth`/`burst` are `{"l": true}`),
  dhcp-local-server holds no timer to copy; recorded in the `_UNDOCUMENTED` comment.
- A3 (recorded only): `required`, `enum` and `pattern` failures say only "fails the
  schema's 'X' constraint here"; the schema's own key, enum or pattern could be named.
- A4: the set and structured output changes are in the declared-break record and the
  changelog (30 equivalent reorders, 18 `hello-padding-type` → `hello-padding`, blocks for
  kept one-liners, no line lost).
- A5 (recorded only): the regenerated grammar corpus dropped 56 covering lines
  keyed-single-entry-lists had kept; the 421-rule cover holds; those lines are guarded by
  `--device-grammar` and the keyed-singleton unit rows.
- A6: `a-renamed-leaf` pins the yaml-new spelling too.
- A7 (recorded only): SC1 is invisible on the consumer surface: `to_dict` is not in
  `junoscfg/__init__.py`, and every `convert_config` path loaded the tree already.

## Fresh review (phase 6, round 2)

Verdict: **Merge**, on `297e9fe...9a0684d`, no binding findings (coordinator scratchpad
`review-dv/verdict-round2.md`). B1, B2 and B3 resolved, each executed: base-written JSON and
yaml-new with the keyword spellings validate and convert alike again; of 33 verb probes only
the two lines stopping inside a route filter's key changed, both now rejected; restoring
base's `set_validator.py` fails `TestEveryCaptureValidatesAsSet` on three captures' `protect`
lines. Advisory:

- R2-A1 (recorded): the alias rule also accepts `hello-padding` in JSON, a spelling junoscfg
  never wrote (base could not place the statement) and base JSON validation rejected; it
  follows from the one rule; added to the changelog's and the record's alias list.
- R2-A2 (recorded under the trust rule): JSON holding both spellings (`"802.3ad"` and
  `"ieee-802.3ad"`) validates, while conversion keeps the second as an unplaced statement;
  input junoscfg never writes, and a caller with untrusted input bounds it first
  (decision 2026-10-15-configuration-input-is-trusted).
- R2-A3 (pending owner decision): the deprecation lives only in the changelog and record; no
  diagnostic tells a user that a file holds the deprecated spelling. Interim: none; the
  owner decides on a field or validation note before retiring the alias.

## Owner decisions pending (nothing is backlogged without the owner)

SC1, SC2 (alias retirement and D3), SC3 with D2, R2-A3, P1 to P4, D1 to D5 and the
backlog candidates B1 to B3 above, each with its interim as recorded.
