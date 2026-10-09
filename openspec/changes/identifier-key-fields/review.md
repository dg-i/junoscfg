## Specification challenges

### The consumer migration names a required property the schema does not emit

- Artifact: `openspec/changes/identifier-key-fields/.openspec.yaml`,
  `declared-break.consumer.migration`: "the key the device's JSON names, which
  the regenerated JSON schema lists as the entry's required property".
- Counterexample: Read, not executed. `src/junoscfg/validate/schema_generator.py`
  emits no `required` anywhere, by design: its comment at "No `required`"
  records that marking XSD-mandatory fields required rejected every fragment
  and broke an earlier attempt. The delta
  `specs/validation/keyed-entries/spec.md` therefore lists the key fields as
  entry properties and rejects `name` where the key is another field, but does
  not make them required. A consumer following the migration text and
  looking for `required` in the regenerated schema finds none.
- User impact: The migration instruction points the production consumer at a
  schema keyword that is absent; the observable behaviour (`name` rejected,
  the device key accepted) is the same either way.
- Proposed correction: Either reword the migration to "lists as the entry's
  property", or add a requirement that the key fields, and only they, are
  `required` in an entry object, with a negative test that an entry without
  its key fails and a corpus run showing no fragment newly rejected.
- Decision: Decided by the owner, 2026-10-09, accepting the first correction:
  the migration in `.openspec.yaml` now reads that the regenerated JSON schema
  lists the key fields as the entry's properties, with `name` only where `name`
  is the key, and adds no `required`, citing the schema generator's "No
  `required`" comment. `specs/validation/keyed-entries/spec.md` pins it with
  `test_no_required_is_added`. No requirement for `required` is added.

### "`o` exactly where it is today" and "where the dump flags `oneliner`" disagree once a list gains its keys

- Artifact: `openspec/changes/identifier-key-fields/specs/schema-pipeline/entry-key-fields/spec.md`,
  requirement "The bundled tree carries the declared keys": "`o` SHALL be set
  exactly where it is today: where the dump flags `oneliner`, and on those
  three filter lists".
- Counterexample: Executed on the 0.14.0 artefacts and read from the 25.2R2
  dump. The dump flags `attributes-match` `<flag>oneliner</flag>` (and
  `homogeneous`). The bundled tree carries no `o` on either `attributes-match`
  node, because `_GUARDED_BOOL_KEYS` in `validate/artifact_builder.py` writes
  `o` only on a list with children and the parser left it childless. Once the
  parser keeps its three identifiers as children, "where the dump flags
  `oneliner`" puts `o` on both nodes, and "exactly where it is today" keeps it
  off. Any other list the dump flags `oneliner` that is childless today only
  for want of its key children is in the same position; their number is not
  measured here.
- User impact: Structured output of `attributes-match` is one line either way
  today (`attributes-match ping.test-owner matches "^uptime$";`), so the
  rendering may not move; the tree, the grammar's one-line repetition and any
  other such list may.
- Proposed correction: State which clause wins. The phase-4 test
  `tests/test_characterization.py::TestEntryKeysComeFromTheTree::test_the_one_line_flag_is_unchanged`
  pins the first ("exactly where it is today": 3,520 nodes, by path digest);
  if the second is meant, the pin is re-measured on the regenerated tree and
  the list of nodes that gain `o` is recorded in the test.
- Decision: Decided by the owner, 2026-10-09 (phase-4 answer 3): the rule
  clause wins, `o` stands where the dump flags `oneliner` and on the filter
  lists `_fix_flat_entry_keys` names. The delta now says so, and
  `test_the_one_line_flag_is_unchanged` is replaced by
  `test_the_one_line_flag_follows_the_dump`. Measured in phase 5 on the
  regenerated 25.2R2 tree: 4,736 nodes carry `o`, 1,216 gained and none lost;
  every one gained is a list whose only children are its key fields, where
  `o` moves no rendering. The 3,464 carriers with a child beyond their keys
  are all 0.14.0 carriers; the other 56 of 0.14.0's 3,520 now hold nothing but
  their key (24 flowspec `port-range`, 16 `tunnel-attribute`, 16 `then
  community`). No `name`-keyed list's output moves.

### The bundled tree holds 48 community action lists, not 16

- Artifact: `tests/test_characterization.py::TestEntryKeysComeFromTheTree::test_the_bundled_tree_carries_the_declared_keys`,
  `assert len(actions) == 16`.
- Counterexample: Executed in phase 5 on the regenerated 25.2R2 tree. Lists
  named `community` holding `add` are 48: 8 under `then`, and 8 each under
  `route-filter`, `prefix-list-filter`, `source-address-filter` and
  `route-filter-list`, 4 each under `rf_list` and `saf_list`. The filter lists'
  second choice of actions holds a `community` action, which the parser kept
  dropping until this change kept every declared choice
  (`test_a_second_choice_is_kept`). Every other assertion of the test holds:
  all 48 are keyed by the action choice then `community-name`, and the four
  `policy-options community` definitions are keyed `name` with no `k`.
- User impact: None; the count predates the second-choice requirement.
- Proposed correction: pin 48, or count only lists whose parent is `then`
  (8, the root, logical-system, group and grouped placements under term and
  policy).
- Decision: Decided by the owner, 2026-10-09: 48 is right. The test now
  checks the rule -- every list whose all-identifier action choice precedes
  `community-name` is keyed (action choice, `community-name`) -- pins 48, and
  keeps the check that the four `policy-options community` lists are keyed
  `name` with no `k`.

### A leaf occurrence's path ends with its value, not its key

- Artifact: `tests/test_audit/test_walker.py::TestEntryKeys::test_a_single_key_other_than_name`,
  `assert one(found, "4").path[-1] == "version"`.
- Counterexample: Executed. The walker records a leaf occurrence's CLI path as
  the path to the leaf then the value, so `version 4` gives `(..., "version",
  "4")`. `TestLeaves::test_leaf_occurrence` pins that convention
  (`... "class", "operator-class"`), and the new
  `TestKeyedEntries::test_list_name_is_the_reference` relies on it
  (`path[-2:] == ("list-name", "AS-LIST-A")`). The assertion contradicts both.
  Every other assertion of the test passes.
- User impact: None; the walker's convention is unchanged by this change.
- Proposed correction: `assert one(found, "4").path[-2:] == ("version", "4")`.
- Decision: Decided by the owner, 2026-10-09: accepted. The assertion reads
  `one(found, "4").path[-2:] == ("version", "4")`, the walker's existing
  leaf-path convention.

### A bare `as-path-neighbors` parses through a split keyword

- Artifact: `tests/test_set_validator.py::TestTheShippedGrammarTakesKeyedEntries::test_device_probe_lines`,
  `REJECTED` entry `... from as-path-neighbors`.
- Counterexample: Executed on the regenerated grammar. The grammar renders
  `as-path-neighbors` as its keyword followed by both key values, required;
  the line still parses because Lark's dynamic Earley lexer matches the merged
  `from` rule's `"as" QUOTED_OR_VALUE` alternative on `as` + `-path-neighbors`:
  terminals need no whitespace between them. The same split accepted the bare
  line on 0.14.0. Every other probe line is accepted or rejected as the device
  did, and the reader keeps the bare keyword as a non-list statement
  (`test_a_bare_list_keyword_creates_no_entry`).
- User impact: `-v -i set` accepts `... from as-path-neighbors` alone, which
  the device rejects; an inherited looseness of the grammar's tokenization,
  not of keyed entries.
- Proposed correction: either a terminal-boundary change (`VALUE` and
  `QUOTED` preceded by whitespace), in this change or a separate one -- it
  alters the terminal lines `tests/data/name-keyed.lark` pins and every value
  slot of the grammar -- or drop the bare line from the grammar-level
  `REJECTED` list here.
- Decision: Decided by the owner, 2026-10-09, in two parts. In this change, a
  keyed-list keyword with no key value is an incomplete statement under the
  one unplaced rule: the reader keeps it whole as written, field validation
  reports it ("... could not be placed in the schema: kept as written, not
  validated"), the set writer reproduces it; the phase-4 test that accepted
  "not a list" is tightened to require this, and was seen failing first. The
  grammar's keyword boundaries (about 380 keyword pairs, pre-existing) are a
  separate later change: the bare line stays in `test_set_validator.py`,
  pinned as a strict expected failure naming that follow-up.

### `apply-macro`'s `data` list is keyed `name`, so its rule loses `"name"`

- Artifact: `tests/data/name-keyed.lark`, the line `data__list: QUOTED_OR_VALUE
  ("name" QUOTED_OR_VALUE | "value" QUOTED_OR_VALUE | universal_statement)?`,
  pinned by `test_name_keyed_grammar_is_byte_identical`.
- Counterexample: Executed. The grammar writes a list's key fields as its
  entries' values and never as a child keyword. `data`, which
  `_apply_statement_nodes` builds, has no `k`, so it is keyed `name` like every
  other list, and its rule becomes `data__list: QUOTED_OR_VALUE ("value"
  QUOTED_OR_VALUE | universal_statement)?`. No information the structure tree
  carries tells `data`'s `name` from the identifier `name` of every other list
  (`is_key` does not survive the tree, by `test_the_three_fields_the_format_drops`).
  The rule is unreachable: `apply-macro` renders as the flat-dict
  `"apply-macro" QUOTED_OR_VALUE+`, so neither `apply_macro__list` nor
  `data__list` is referenced from `start`. Every other line of the pin is
  byte-identical.
- User impact: None; no set line reaches the rule.
- Proposed correction: accept the changed line, as done in the interim.
- Decision: Decided by the owner, 2026-10-09: accepted. The `data__list` line
  of `tests/data/name-keyed.lark` stays as generated; the rule is unreachable
  from `start` on master and on the branch, and every `apply-macro` line goes
  through `universal_statement`.

### Interim items decided with the challenges

- `entry_key_names()` in `junoscfg.display`: accepted by the owner, 2026-10-09,
  as long as it derives only from `entry_keys()`; it does.
- `_fix_groups` giving `group` a `name` key child and clearing `is_presence`:
  accepted by the owner, 2026-10-09, as a fix the regeneration requires;
  recorded in metrics.md as an addition beyond the proposal.

## Phase-6 review (fresh session, 2026-10-09)

Reviewed `master...HEAD` (588d16a..fc22c57) against the approved folder. Every
figure below was rerun in this session; master was run from `git archive
master` in the scratchpad with the same virtualenv. Device probes are cited as
"device probe, vMX 23.2R2-S7.5"; nothing from the probe files is copied here.
Synthetic values only.

### Verified

1. **The reference survives.** The bug report's synthetic fixture converted
   `-i conf -e set` with `--anonymize-all` and with `--anonymize-as-numbers
   64496`: each output carries `as-path-neighbors as-list SAMPLE-AS-LIST` exactly
   once; the group name is anonymized under `--anonymize-all`.
2. **Every `return` in `_merge_tokens`** (`src/junoscfg/convert/input/set_input.py`
   lines 237-455) either consumes every token or calls `_keep_whole`, except the
   two pre-existing leaf returns (lines 435, 443) that join the rest of the line
   into the value, as on master. Probed with a surplus after a keyed entry, after
   a childless list, after `apply-groups`, after a nokeyword leaf and after
   `attributes-match`: each is kept whole from its keyword and reported
   `UNPLACED`. The exceptions are findings 1, 2 and 5 below.
3. **The four doors agree** on every `tests/data/captures/keyed-entries-*` group
   (IR equal across set, rerooted structured, JSON and XML; set output equal
   across doors and equal to the capture), `attributes-match` and `then
   community add` included.
4. **The declared break matches the recorded figure.** Regenerated JSON schema:
   10,792 list-entry objects, 2,558 without `name` (0.14.0: 8,394, 0), exactly
   the phase-5 figures. Of the 8,394 entry objects present in both, 2,426 lost
   `name` (keyed otherwise) and 31 `name`-keyed ones changed property set: 7
   `snmp community` lost the spurious `community-name` the retired override
   added, 24 openconfig `acl-set`/`policer`/`protocol` gained a non-identifier
   sequence element (`type`, `identifier`). 2,266 `name`-keyed lists that were
   childless (`items` absent on master) now carry an object `items` with `name`;
   `[null]`, `["x"]` and `[{"name": "x"}]` all still validate. No `required`
   anywhere on either side. The YAML schema shows the same counts.
5. **Corpus, set reader.** 1,538 structured files (4,947,067 lines) under
   `private_test_data/jvd` and `private_test_data/captures`, structured to set
   through `convert_config_result`: unplaced statements 69,768 on master,
   68,227 on the branch; 161 files have fewer, none has more. Other field
   diagnostics: 521 on master, **11,984 on the branch** (finding 3). Set output
   differs in 124 of 1,538 files (findings 1 and 4 and the branch's correct
   `deactivate` line for an inactive route-filter entry that master dropped).
6. **Grammar.** Shipped grammars compared rule by rule: 4,849 rules on master,
   4,884 on the branch; 65 new `__k` rules, 67 `__eo` rules gone; 280 common
   rules changed body, 114 of them only by gaining a bare `QUOTED_OR_VALUE`
   alternative (finding 1). Sample of 11,000 unique corpus set lines (6,000
   from keyed lists, 5,000 random) through `validate_set` on both grammars:
   10,968 accepted and 32 rejected on both, no line newly rejected or newly
   accepted. The branch grammar rejects `as-path-neighbors as-list AS-LIST-A
   EXTRA`, `as-path-neighbors as-list`, `as-path-neighbors 1 AS-LIST-A`,
   `route-filter 198.51.100.0/24 exact EXTRA`, `route-filter 198.51.100.0/24
   next-policy` and the `attributes-match` line with a trailing `EXTRA`, and
   accepts `as-path-neighbors as-list AS-LIST-A` (executed through
   `SetValidator` on the bundled grammar). `set system location dc-a` is
   accepted (finding 7).
7. **Regeneration.** `pytest --regen-schema tests/test_schema_data.py` from the
   shipped 25.2R2 dump: the structure tree, JSON schema, YAML schema and
   grammar reproduce byte-identically; only `junos-schema-meta.json.gz`
   differs, in its `generated_at` timestamp (same version, 38 of 41 fixes
   applied, same node counts). That file was restored to HEAD after the
   check. The artifacts were regenerated, not hand-edited.
8. **Additions beyond the proposal.** Changed files the proposal and codemap do
   not name are all recorded as context expansions or additions in
   `metrics.md`, with these exceptions: `tests/test_set_corpus.py` (finding 7),
   `tests/test_audit/test_types.py` (the two `as-path-*` reference lines
   rewritten to the device's `as-list <name>` form, covered by the audit
   delta's test list), and the anonymize walker's `keywords` parameter
   (finding 9). Behaviour changes no spec covers: findings 1, 3, 4, 7.
9. **Full check** at fc22c57: exit 0, "every check passed", 1838 passed, 45
   skipped, 1 xfailed (the strict xfail named in the record). `openspec
   validate identifier-key-fields --strict`: valid. Production collection
   347715a against this checkout from a throwaway virtualenv: 33 passed.
10. **Stated figures.** 24 `control-as-list-type` slots carry `(list-type,
    list-name)`; 48 community action lists keyed `(action, community-name)`
    and 4 `policy-options community` keyed `name`; `o` on 3,520 nodes on
    master and 4,736 on the branch; `fe` on no node; the dump counts
    (2,800 / 171 / 64 / 38) pass in
    `tests/test_schema_data.py::TestEntryKeysOnTheDump` with `--schema`.
    Owner corrections all hold: `fe` gone, the two names removed and banned,
    identifier choices are key fields, a key keyword reads on either side, a
    bare keyed-list keyword is incomplete.

### Findings, by severity

**1. High. Non-list nodes with an identifier child: a second statement silently
replaces the first, and the corpus shows it.**
`src/junoscfg/validate/xsd_parser.py` line 342 records key fields and keeps
identifier children for every complexType, while line 120 counts only
`maxOccurs="unbounded"` as a list. The 25.2R2 dump has 385 element
declarations with a numeric `maxOccurs` above 1 (`peers` 3, `class` 16, ...).
Measured on the regenerated tree: 1,774 non-list nodes (144 element names)
gained a nokeyword `name` leaf, 26 non-list nodes carry `k`. For such a node
the reader takes the nokeyword-leaf path (`set_input.py` line 308,
`current[cname] = _parse_value(token)`), which overwrites.
Failing input (structured, from the corpus shape):
`forwarding-classes { class fc0 queue-num 0; class fc1 queue-num 1; class
mcast-fc queue-num 2; }` gives IR `{"class": {"name": "mcast-fc",
"queue-num": ["0", "1", "2"]}}`, no diagnostic, and set output `class mcast-fc
queue-num 0 / 1 / 2`; master kept all three lines, unplaced and loud. Same with
`set system commit peers 10.0.0.1` then `peers 10.0.0.2` (IR `{"peers":
{"name": "10.0.0.2"}}`, validates clean, first peer gone) and `system services
http servers server S1 port 80` / `S2 port 81` (S1 vanishes, S2 gets both
ports). In the jvd corpus this rewrites 164 `class SIG-OAM`, 96 `mcast-fc`, 84
`FC-SIGNALING` and further `queue-num` lines.
Invariant broken: ARCHITECTURE.md section 1 (what is written loads as the same
configuration) and the conversion delta's purpose "no token is dropped"; the
bug report's requirement 9 (never turn a loud failure into a quiet wrong
answer). The same class adds the bare `QUOTED_OR_VALUE` alternative to 114
merged grammar rules (`location`, `location_pool`, ...), which is why `set
system location dc-a` left `OVER_REJECTED` (finding 7).
Recommendation: in the parser, an element with any `maxOccurs` other than 1 is
a list (the XSD says so; the device's `forwarding-classes class` and `commit
peers` are lists); and the nokeyword-leaf path refuses to overwrite a present
different value, keeping the statement whole instead, which also covers a true
single container such as `then logical-system LS`. Raised as challenge A below.

**2. High. Key fields the tree marks as keyword leaves are read positionally.**
`_read_key` (`set_input.py` line 209) takes one bare token for every value
field, but 380 of the 1,214 positional key fields on keyed lists are leaves
without the `nk` flag: 218 list slots under 16 names (`virtual-link`
(`neighbor-id`, `transit-area`), vrrp `track route` (`routing-instance`),
`bfd-liveness-detection`, NAT `address-range` (`low`, `high`), evpn `mac`
(`remote-vtep`), `drop-profile-map`, `dlv`, ...). The grammar already honours
the flag: `grammar_generator.py` line 175 renders such a field `"keyword"
VALUE`, so reader and grammar disagree.
Failing input: `set protocols ospf area 0.0.0.1 virtual-link neighbor-id
10.0.0.1 transit-area 0.0.0.2` gives IR `{"neighbor-id": "neighbor-id",
"transit-area": "10.0.0.1", "transit-area 0.0.0.2": true}`: a wrong key value
in JSON/YAML output beside the unplaced report; master kept the line whole.
`track route 10.0.0.0/8 routing-instance default priority-cost 10` likewise
(`"routing-instance": "routing-instance"`). From device-shaped JSON the writer
(`dict_walker.py` line 453) drops the keyword: `track route 10.0.0.0/8 default
priority-cost 10`. The reader also accepts the positional form the grammar and
the device reject (`dlv example.net abc` reads clean).
Invariant: conversion delta "each input gives the device's IR"; "one token per
value field" is the spec's own sentence, so this is challenge B below.
Recommendation: a key field whose leaf is not nokeyword is read and written as
`keyword value`; the grammar's `_key_value` is the model.

**3. High. Validating `name` keys against their leaf floods valid
configuration with enum errors.**
Master never validated a `name` key (it was not a tree child). On the branch
every key leaf is validated (`field_validator.py` lines 312-320), and 3,684
`name`-keyed list slots carry an enum on their `name` leaf, of which
`enum_is_fragment` recognises 8. Example: `class-of-service interfaces <if>
unit <u> classifiers dscp DSCP` is keyed `name` with the enum `["default"]`,
no pattern; the device takes any classifier name there; the branch reports
"Invalid value 'DSCP': must be one of [default]". Over the corpus: 11,310 such
errors, 202 for `unit` (`[$junos-underlying-interface-unit, ...]`), 16 for
`[*]`, 57 for `drop-profile-map loss-priority`; other field diagnostics go from
521 to 11,984, 2.4 per 1,000 lines against the repository's own budget of 0.5
(`tests/test_jvd_corpus.py::TestFieldWarningBudget`, which the full check does
not run; a `--jvd` run would fail). This is the class
`test_a_nokeyword_leaf_takes_a_value_outside_its_enum` was written for,
recurring on identifiers. `-v --strict` now refuses valid device
configuration. Not covered by the non-goal (it names IR, output and grammar,
not validation). Challenge C below.

**4. Medium. Conversion is 2 to 6 times slower on large configurations.**
`_find_or_create_entry` (`set_input.py` line 163) compares a dict per entry
per lookup; profile of a 23,447-line file: 2.4 s of 3.6 s in that function,
4.1 M generator calls. `ma4_mx204.conf` (233,512 lines): 12.8 s on master,
72.8 s on the branch. The corpus pass takes about twice master's time.
Recommendation: index entries by key tuple, or compare a tuple of key values.

**5. Medium. An entry that arrives through JSON, YAML or XML without one of
its key fields is written as a line the device rejects, with no diagnostic.**
`{"as-path-neighbors": [{"list-name": "X"}]}` writes `as-path-neighbors X`;
`{"route-filter": [{"exact": [null], "accept": [null]}]}` writes two lines
`route-filter exact` and `route-filter accept` (master wrote one, also wrong);
`attributes-match` missing `condition` writes two lines. Field validation
reports nothing (`_entry_label` only labels), and the JSON schema adds no
`required` by owner decision. Master was wrong in kind as well, so the
severity is for the spec gap: "A statement the reader cannot complete is kept
whole" has no counterpart for the structured doors. Recommendation: field
validation reports a missing key field as it reports an unplaced statement, so
the pipeline refuses to anonymize it and `-v` flags it.

**6. Low. Bare `set apply-groups` validates clean.** It is kept whole as
`{"apply-groups": true}` and written back, which is better than master (the
line vanished), but `field_validator.py` line 245 exempts the exact spelling,
so an incomplete statement the device rejects passes `-v`. The conversion
delta names only the surplus case.

**7. Low. `tests/test_set_corpus.py` line 53: `set system location dc-a` left
`OVER_REJECTED`** because the merged `location` rule gained the bare value
alternative of finding 1, not because the grammar now models the line. No spec
covers that acceptance; whether the device takes a bare value under `system
location` is unprobed. The owner should decide whether the line goes back once
finding 1 is fixed.

**8. Low, simplification.** `field_validator.py` lines 275 and 319 read `"k" in
schema_node` directly where `entry_keys(node) != ("name",)` is the kernel's
answer, a second spelling of the same question. `_statement_children` exists
twice with one meaning (`set_input.py` line 170, `grammar_generator.py` line
156); the kernel next to `entry_key_names` is where it belongs. Pre-existing
residue noticed on the way: `_fix_route_filter_arg` and
`_fix_source_address_filter_arg` (`xsd_fixes.py` lines 240-253) are no-ops of
the same class as the retired `_fix_attributes_match_oneliner`; not this
change's, for the carry-forward list.

**9. Low, record.** The anonymize walker's `keywords` parameter
(`anonymize/walker.py` lines 207, 235, 245) is the one new parameter in the
change; it is generic over every enum leaf and required by the anonymization
delta, and `metrics.md` records it, but the owner-decided list above does not.
Named here so the acceptance is explicit under the simplification criterion.

**10. Low, record.** The declared break says "Lists the device keys `name` are
unchanged"; for the JSON and YAML schema that holds for 8,363 of 8,394 entry
objects (item 4 above). Both accept the IR as before; a sentence in the
migration would make the record exact. No action beyond the owner's say.

Tests: no owner-unapproved weakening found. Every removed assertion in the
diff is either an owner-approved rewrite recorded above, the version bump, or
the two audit path assertions that now include the choice keyword in the
entry's CLI path (`test_walker.py`, `("prefix-list-filter", "plf-a",
"orlonger")`), which follows the walker's `_key_tokens` and is consistent with
the challenge decided above. The strict xfail is strict.

### Review prompts

- Trust boundary: structured input from a device is the attacker-controlled
  side; finding 1 shows valid input rewritten into a different configuration
  with no diagnostic. Findings 2 and 5 are the same boundary.
- Incompatible but valid: findings 1, 2 and 3 are device-valid statements the
  implementation's assumptions ("unbounded means list", "a key value is
  bare", "an identifier's enum is closed") do not cover.
- Shared blind spot: the acceptance tests and the implementation share the
  assumption that identifier children only matter on lists and that key fields
  are positional; the jvd corpus (not run by the full check) is the independent
  evidence, and it fails the field-warning budget.
- Second answer: none added in the runtime beyond the enum pass-through
  (finding 9); the `"k" in node` reads (finding 8) are the only second spelling.
- Figures: all rerun (item 10); the `cannot` in the non-goals ("lost values
  elsewhere") is not a claim and has no counterexample here.

### Carry-forward (could not check)

- The grammar's keyword-boundary looseness (owner-deferred) was not re-measured.
- Device validity of `set system location <value>` (finding 7) and of the
  positional form of keyworded keys (finding 2) was not probed; both need a
  device probe before the fix lands.
- The `--jvd` and `--schema` tiers are not in `check --set full`; finding 3
  would have been caught by the first.

## Specification challenges (phase 6)

### A. Identifier children on non-list nodes are unspecified and lose statements

- Artifact: `specs/schema-pipeline/entry-key-fields/spec.md`, "The parser
  keeps every element a sequence declares" (every complexType), against
  `proposal.md` "Every list node carries its key fields"; `xsd_parser.py`
  line 120.
- Counterexample: executed. Finding 1: `forwarding-classes class` (XSD
  `maxOccurs="16"`), `commit peers` (`maxOccurs="3"`); 1,774 non-list nodes
  gained `name`, 26 carry `k`; the jvd corpus loses 344 `class ... queue-num`
  identities with no diagnostic.
- User impact: a converted configuration that loads differently from its
  input; the anonymize path (`--anonymize-*`) passes it through silently.
- Proposed correction: the parser treats every `maxOccurs` other than 1 as a
  list; a non-list node with identifier children is read as one statement and
  a second with a different key value is kept whole; a scenario for each with
  the jvd shapes as tests. Recommendation: both, the first is the XSD's own
  statement.
- Decision: Decided by the owner, 2026-10-09, accepting both corrections. The
  parser treats any `maxOccurs` but 1 as a list (`xsd_parser.py`), and the set
  reader's nokeyword-leaf path never overwrites a present, different value: it
  keeps the statement whole from its node's keyword and reports it. Pinned by
  `TestCardinality::test_a_numeric_max_occurs_is_list` and
  `TestANonListNodeNeverReplacesAnEntry` (three forwarding classes, two
  `commit peers`, two `http servers server`, `access securid-server`), and the
  spec scenario "Lists the XSD bounds by a number". Applied in the fix pass.

### B. "One token per value field" contradicts the tree for 380 key fields

- Artifact: `specs/conversion/entry-keys/spec.md`, "the set reader SHALL take
  one value per field in order"; `docs/architecture/conversion-bugfix-guide.md`
  "The set reader takes one token per value field".
- Counterexample: executed. Finding 2: `virtual-link neighbor-id 10.0.0.1
  transit-area 0.0.0.2`, `track route 10.0.0.0/8 routing-instance default`;
  the tree marks 380 key fields as keyword leaves and the grammar renders them
  `"keyword" VALUE`.
- User impact: wrong key values in JSON and YAML output, keyword dropped on the
  way back from device JSON, device-rejected positional form accepted.
- Proposed correction: a key field whose leaf is not nokeyword is read and
  written as `keyword value`, in declared order (the grammar's order); tests
  for `virtual-link`, `track route`, `address-range` in set, JSON and XML. The
  order the device accepts among keyworded fields needs a probe.
- Decision: Decided by the owner, 2026-10-09: a key field whose leaf is not
  nokeyword is read and written as `keyword value`. Device probe round 5 (vMX
  23.2R2-S7.5) then showed the keyword fields accepted in either order and
  stored in declared order, and the field left out or given without its
  keyword rejected; the owner replaced the interim "declared order only" with
  that. Reader (`_read_key`), writer (`DictWalker._entry_key`) and grammar
  (`_key_sequence`, permutations of the keyword fields; `_key_value` now writes
  the keyword before a closed enum too, `drop-profile-map loss-priority low`)
  agree. Pinned by `TestKeyFieldsGivenByKeyword`, the `virtual-link`
  device-truth capture and `test_round_5_accepted_lines` /
  `test_round_5_rejected_lines`. Applied in the fix pass.

### C. Validating `name` keys against an identifier's enum rejects valid configuration

- Artifact: `specs/validation/keyed-entries/spec.md`, "SHALL validate each key
  value against its own leaf in the tree, ... enum and pattern included", as
  implemented for `name` keys.
- Counterexample: executed. Finding 3: 11,310 `must be one of [default]`
  errors over the jvd corpus, `classifiers dscp DSCP` the shape; 3,684
  `name`-keyed slots carry an enum, 8 of which `enum_is_fragment` sees.
- User impact: `-v` and `--strict` refuse valid device configuration;
  `TestFieldWarningBudget` fails at 2.4 per 1,000 lines.
- Proposed correction: either restrict closed-enum enforcement to key fields
  the tree marks `k` (the device-probed `list-type` case) and treat a `name`
  identifier's enum as a fragment, or extend `enum_is_fragment` to identifier
  leaves with a corpus run under budget as the test. Recommendation: the first;
  it keeps the probed behaviour and the budget.
- Decision: Decided by the owner, 2026-10-09, accepting the first correction:
  closed-enum enforcement applies to the key fields the tree names in `k`; a
  `name` key's enum is a fragment and open, as on 0.14.0. Pinned by
  `TestANameKeyIsOpen`. Corpus: other field warnings 329 against master's 521
  (241 false `Missing mandatory field` on master gone, because the statements
  they sat in are now placed; 49 new, every one on a `$TEMPLATE` or
  `<placeholder>` value of a jvd snippet now placed and validated);
  `TestFieldWarningBudget` passes. Applied in the fix pass.

## Fix pass (owner decisions on the phase-6 review, 2026-10-09)

Each finding above, as the owner decided it; evidence in `tasks.md` section 4.

- Finding 1: challenge A, decided above.
- Finding 2: challenge B, decided above.
- Finding 3: challenge C, decided above.
- Finding 4, decided by the owner: entries indexed by key tuple
  (`_find_or_create_entry`). `ma4_mx204.conf`, 233,512 lines: 65.6 s at
  fc22c57, 4.5 s after, 12.5 s on master's code, same machine.
- Finding 5, decided by the owner: an entry from JSON, YAML or XML without a
  key field is reported with the unplaced message; requirement "An entry
  without a key field is unplaced" in `specs/validation/keyed-entries`,
  `TestAnEntryWithoutItsKeyIsUnplaced`.
- Finding 6, decided by the owner: a bare `apply-groups` is reported
  unplaced (`TestABareApplyGroups`). A full statement after a bare keyword
  kept whole under the same key raised `TypeError`/`AttributeError`; it is
  now kept whole too.
- Finding 7, decided by the owner after device probe round 5 (vMX
  23.2R2-S7.5): the device rejects `set system location dc-a` and accepts
  `location building <name>`. The grammar rejects the line again since the
  challenge A fix; `tests/test_set_corpus.py` lists it as a correct
  rejection, citing the probe.
- Finding 8, decided by the owner: `entry_keys(node) != ("name",)` replaces
  `"k" in node`; one `statement_children()` in `junoscfg.display` serves the
  set reader and the grammar. `_fix_route_filter_arg` and
  `_fix_source_address_filter_arg` stay: the proposal does not name them.
- Finding 9, decided by the owner: behaviour accepted, the anonymization
  delta states one rule for every leaf's own enum value, the "no value
  anonymized before escapes" requirement exempts it, the `enums` and
  `keywords` plumbing is gone (`_leaf_enum` resolves it in one place), and
  the changelog names the fix. `test_a_value_from_its_leafs_enum_passes_every_rule`
  fails on master's code. anonymizer-bugs rows 4 and 5 marked fixed.
- Finding 10, decided by the owner: the consumer migration names the 31
  `name`-keyed entry objects whose property set moved.
- Question 7, decided by the owner: the developer guide's pre-review list for
  grammar and field-validator changes names `--jvd`, `TestFieldWarningBudget`
  and the corpus comparison.
- `apply-macro`, decided by the owner after device probe round 5: a name,
  optionally a keyword and its value, at most three values. The reader keeps a
  fourth value whole and reports it; the grammar renders a `flat-dict` list
  from the tree as its key, then optionally its child list's key and leaf
  values. The guard tests for the one- to three-value forms pass before and
  after the change.

## Phase-6 re-review (fresh session, 2026-10-09)

Reviewed the fix pass `fc22c57..HEAD` (d0b892d, 8dc8629, d274595, 7f998e9,
8d623a1, d8717de) in full against the owner decisions above, the revised
deltas and the tests; the rest of `master...HEAD` rests on the first review
and was re-opened only where the fix pass touched it. Every figure below was
rerun in this session on the branch; master's figures are the frozen baseline
in `private_test_data/identifier-key-fields-review-baseline` and were not
rerun. Device facts are cited as "device probe, vMX 23.2R2-S7.5"; nothing from
the probe files is copied here. Synthetic values only.

### Verified

1. **The reference survives.** The bug report's synthetic fixture converted
   `-i conf -e set` with `--anonymize-all` and with `--anonymize-as-numbers
   64496`: each output carries `as-path-neighbors as-list SAMPLE-AS-LIST`
   exactly once; `--anonymize-all` anonymizes the group name only.
2. **Every `return` in `_merge_tokens`** (`src/junoscfg/convert/input/set_input.py`
   lines 262-507) consumes every token or calls `_keep_whole`: the two
   `apply-groups` returns (surplus, bare, or a full statement after a bare one
   kept whole; one group consumed), the two `apply-macro` returns (more than
   four tokens or a kept-whole key; else one to three values consumed), the
   nokeyword-leaf return only at end of tokens, the new overwrite guard
   (`_keep_whole(owner, tokens, owner_i)`), the `tk` return at end of tokens,
   the unknown-token keep-whole, the bare-keyword return, the `_read_key`
   None keep-whole, the surplus-or-kept-key keep-whole, the entry-complete
   return at end of tokens, the presence return at end of tokens, the
   unknown-node keep-whole, and the two pre-existing leaf returns that join
   the rest into the value. Probed: a surplus after a keyed entry
   (`as-list SAMPLE-AS-LIST EXTRA`), after a childless list of names
   (`snmp filter-interfaces interfaces IF1 EXTRA`), after `apply-groups`
   (`G1 G2`), after a nokeyword leaf (`autonomous-system 64496 EXTRA`), after
   `then community add COMM-A` and after `attributes-match`: each kept whole
   and reported `UNPLACED`.
3. **The four doors agree:** `tests/test_device_truth.py` and
   `TestKeyedEntriesAgreeAcrossReaders` (76 tests, the `virtual-link` and
   `apply-macro` captures included) pass; the probed `virtual-link` line in
   reversed order gives the declared-order IR and set line.
4. **The declared break matches the record.** Counting, on each JSON schema,
   every `array` whose `items` is an object with `properties`, and those
   without `name`: 0.14.0 8,394 / 0; fc22c57 10,792 / 2,558; HEAD
   11,547 / 2,560, the figures `tasks.md` 4.14 records, the 755 more being
   the numerically bounded declarations.
5. **Corpus** (`review_tools.py corpus rr`, branch only, 1,538 files,
   4,947,067 lines): unplaced 68,172 against master's 69,768, other field
   warnings 329 against 521, 35 files failing on both. Two files have one
   more unplaced statement than master, both the jvd `cpe-attachment.conf`
   template with `esi { $ESI_BYTES; $ESI_MODE; }`: master wrote `esi
   "$ESI_MODE"` alone, the branch writes `esi "$ESI_BYTES"` and keeps
   `esi $ESI_MODE` whole and reported (the challenge A guard; with a real
   mode, `esi <bytes>` then `esi single-active` reads clean). 161 files have
   fewer. Set output differs from master in 75 files, as `tasks.md` 4.13
   explains them.
6. **Grammar** (`review_tools.py grammar rr`, 11,000 sampled lines): 10,970
   accepted, 30 rejected; newly rejected 0, newly accepted 2, both decided:
   `drop-profile-map loss-priority any protocol any drop-profile dp0`
   (challenge B, keyword key fields) and `forwarding-classes class LOW
   queue-num 1` (challenge A, a bounded list). The bundled grammar rejects
   `as-list SAMPLE-AS-LIST EXTRA`, `virtual-link 10.255.255.4 0.0.0.2`,
   `drop-profile-map any any drop-profile dp0`, `apply-macro 12345 "KADJBF
   KU!H" balks XXXXX` and `set system location dc-a`, and accepts
   `virtual-link transit-area 0.0.0.2 neighbor-id 10.255.255.1`, the three
   `apply-macro` forms and `location building SAMPLE-BUILDING`, as the device
   did (device probe, vMX 23.2R2-S7.5).
7. **Regeneration, by inspection (owner's replacement for `--regen-schema`).**
   8dc8629 touches only the five files under `src/junoscfg/validate/data/`
   and follows d0b892d, the parser's `maxOccurs` change; 7f998e9 touches only
   `junos-set.lark.gz` and `junos-schema-meta.json.gz` and follows d274595,
   whose runtime changes reach only the grammar among the artifacts
   (`grammar_generator.py`, `statement_children`). 8d623a1 and d8717de touch
   no file under `data/`. No commit edits an artifact by hand.
8. **Additions beyond the proposal** in the fix pass are recorded in
   `metrics.md` (`statement_children`, `_EntryIndex`, the kept-whole
   statement after a bare keyword, `apply-macro`, the two captures) but one:
   finding 11 below. Behaviour the specs do not cover: none found; each fix
   has its requirement, scenario and test list.
9. **Full check** at d8717de: exit 0, "every check passed", 1892 passed, 45
   skipped, 1 xfailed (the strict keyword-boundary xfail).
10. **Stated figures.** `ma4_mx204.conf` (233,512 lines) structured to set:
    4.2 s (record: 4.5 s, fc22c57 65.6 s). The `o` pins (3,552 with other
    children, 1,286 keys only) and the 48 / 24 counts pass inside the full
    check. No `"k" in` read survives under `src/junoscfg/`; one
    `statement_children` definition exists, in the kernel. No runtime line
    special-cases `control-as-list-type`, `attributes-match` or `community`
    (comments only).

### Decisions, one probe each

- **Challenge A:** three structured `forwarding-classes class` lines give
  three entries and three set lines, no diagnostic; two `commit peers` stay
  two; `access securid-server SAMPLE-SERVER ...` then `SAMPLE-SERVER-2 ...`
  keeps the first and keeps the second whole from `securid-server`, reported.
  Implemented.
- **Challenge B:** `virtual-link transit-area 0.0.0.3 neighbor-id
  10.255.255.2` reads to `{"neighbor-id": ..., "transit-area": ...}` and
  writes declared order; `virtual-link 10.255.255.4 0.0.0.2` is kept whole and
  reported; `track route 10.0.0.0/8 routing-instance default priority-cost 10`
  round-trips with its keyword. Implemented.
- **Challenge C:** `classifiers dscp SAMPLE-DSCP` validates clean;
  `as-path-neighbors 1 SAMPLE-AS-LIST` still reports "must be one of
  [as-list, as-list-group]" from set and from `validate_ir`. Implemented.
- **Finding 4:** 4.2 s, item 10. Implemented.
- **Finding 5:** JSON `{"as-path-neighbors": [{"list-name": ...}]}` reports
  "'as-path-neighbors' entry without its key field 'list-type' could not be
  placed in the schema: kept as written, not validated" and `strict=True`
  raises `FieldValidationError`. Implemented.
- **Finding 6:** `set system apply-groups` reads `{"apply-groups": true}`,
  writes back, reports unplaced. Implemented.
- **Finding 7:** the bundled grammar rejects `set system location dc-a` and
  accepts `location building SAMPLE-BUILDING`; `test_set_corpus.py` lists the
  line as correctly rejected, citing the probe. Implemented.
- **Finding 8:** item 10. Implemented.
- **Finding 9:** `from protocol bgp` under `sensitive_words=["bgp"]` and
  `as-list-group SAMPLE-NAMES` under `["as-list"]` come back unchanged; the
  `enums`/`keywords` plumbing is gone and `_leaf_enum` reads the same bundled
  tree `walk()` loads, through the cached `load_schema_tree()`, so there is no
  second source. Implemented.
- **Finding 10:** the migration names the 31 `name`-keyed entry objects, 7
  `snmp community` and 24 openconfig. Implemented.
- **`apply-macro`:** one, two and three values read, write and validate as
  the device stores them; a fourth is kept whole, reported, and rejected by
  the grammar. Implemented.

### Findings, by severity

**11. Low, simplification.** "A key field written with its keyword" is
spelled three times: `set_input.py` lines 183-185 (`_is_keyword_field`, on a
tree dict), `grammar_generator.py` lines 152-154 (`_is_keyword_field`, on a
`SchemaNode`) and `dict_walker.py` lines 454-455 (inline, `leaf.get("l") and
not leaf.get("nk")`). The fix pass moved `statement_children` into the kernel
for exactly this reason, and that helper already takes either node type; the
predicate belongs beside it, so reader, writer and grammar cannot drift.
Correctness is unaffected today (the three agree, and the device-truth
captures pin them). Not recorded in `metrics.md`.

Tests: no owner-unapproved weakening, skip or deletion in `fc22c57..HEAD`.
The two re-measured pins are explained in their docstrings
(`test_the_one_line_flag_follows_the_dump`: 102 nodes gained `o`, none lost,
all newly lists; `test_name_keyed_grammar_is_byte_identical`: the
`universal_statement` line, by the `apply-macro` decision). The strict xfail
stays strict.

### Review prompts

- Trust boundary: structured and set input from a device. The challenge A
  guard turns the silent overwrite into a kept, reported statement (the
  corpus `esi` template shows it); finding 5 closes the structured doors.
- Incompatible but valid: a hand-written set script that sets a nokeyword
  leaf twice to different values is now reported rather than last-wins; a
  device's own display never does so, and keyword leaves already accumulated
  (`host-name r1` then `r2` gives both). Loud over quiet, as decided.
- Shared blind spot: the corpus and the field-warning budget were the
  independent evidence the first review called for; both now run and pass,
  and the developer guide names them before review.
- Second answer: `_leaf_enum` and `walk()` read one tree; `_is_keyword_field`
  is the one remaining second (third) spelling, finding 11.
- Figures: all rerun (item 10); the corpus and break figures match the record
  to the unit.

### Carry-forward (not this change's; not worse than master)

- A surplus token after a complete key of an entry whose other children
  include a nokeyword enum leaf lands in that leaf and nothing reports it:
  `virtual-link neighbor-id 10.255.255.1 transit-area 0.0.0.2 EXTRA` reads
  `"enable-disable": "EXTRA"` (enum `[disable]`, taken as a fragment) with no
  diagnostic, and the grammar accepts the line; the `name`-keyed `interface
  ge-0/0/0.0 EXTRA` does the same on the untouched path. The keyword-boundary
  follow-up is the place for it, or a rule that a one-value nokeyword enum is
  closed.
- The grammar's keyword boundaries (strict xfail) and the other owner-deferred
  items were not re-measured.

### Verdict

Mergeable from this review: every owner decision is implemented and probed,
the corpus and grammar move only as decided, the break figure is the recorded
one, and the full check passes. Finding 11 is a simplification the owner may
take now or carry forward; no specification challenge is open.
