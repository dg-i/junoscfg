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
