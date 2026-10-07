## Why

`junoscfg -v` validated nothing for set or structured input: the bundled
`junos-set.lark` carries two `start:` rules, fails to load, and both formats
report "Error loading validation artifacts" and exit 3 on a valid and an
invalid configuration alike. It failed loudly, not silently.

`_safe_rule_name` has two defects:

- It does not lowercase, and Lark reads a name containing an uppercase letter
  as a *terminal*. Of 60 such names in a real 23.2R2 dump only one has
  children and so becomes a rule definition —
  `jnx-tel-RE-local-interfaces-stats:interfaces` — and that one is enough to
  make the grammar unparseable. 24.4R0 has no such element.
- It does not reserve the grammar's own `start`. Junos has an element `start`,
  whose child is `start-options`; the generator emitted a second `start:` rule
  beside the entry rule. The bundled grammar carried two from the 24.4
  migration in `3b55b78` until the artefact was rebuilt.

Neither was reachable from the synthetic fixtures: a device dump found the
first, and the second sat in a file nothing loaded.

## What Changes

- Lowercase generated rule names; reserve `start`, so a schema element of that
  name becomes `start_element`.
- Unit tests on `_safe_rule_name`, needing no device data.
- `TestBundledGrammarCompiles`, and two `xfail(strict=True)` pins for defects a
  rebuilt grammar still hit. All three were still failing at this change; the
  two successor changes resolved every one, so none is an xfail today.
- A schema-backed test tier, so a developer who syncs device dumps gets tests
  the fixtures cannot provide: `tests/schema_data.py`, `tests/test_schema_data
  .py`, and a `--schema` flag, marker and fixtures in `tests/conftest.py`.
  Dumps live in gitignored `private_test_data/schemas/`, staged as `new.xsd`
  and promoted to their version. This landed here and belongs in the record.

## Capabilities

### New Capabilities

None; this repairs an existing one.

### Modified Capabilities

No requirement changes, so `.openspec.yaml` sets `skip_specs: true`.

## Non-goals

- Regenerating the bundled artefacts. Recorded here as needing a dump at the
  shipped release; `rebuild-set-grammar` later showed that premise false by
  rebuilding from `junos-structure-tree.json` instead.
- Fixing the two defects the pins record. `grammar-named-lists` does that.

## Impact

`grammar_generator.py`, `tests/conftest.py` and the test suite. Set and
structured validation stayed broken for users until `rebuild-set-grammar`
replaced the artefact: this change fixed the generator, which is a separate
thing from what ships in `validate/data/`.
