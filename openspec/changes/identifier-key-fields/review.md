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
