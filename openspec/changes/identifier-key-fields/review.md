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
- Decision: Pending owner decision. Interim action: the delta specifies the
  key fields as properties only, which is the existing architecture and is
  reversible by adding one requirement.
