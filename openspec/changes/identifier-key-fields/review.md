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
- Decision: Pending owner decision. Interim, safe and reversible: the test pins
  today's 3,520 paths; phase 5 stops and reports if the regenerated tree moves
  them.
