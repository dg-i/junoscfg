## Why

`junoscfg -i set -v` validates nothing. It reports

```text
Error loading validation artifacts: Failed to load Lark grammar:
Rule 'start' defined more than once
```

and **exits 0** — on a valid configuration and on one containing an element
that does not exist. JSON, YAML and structured validation are unaffected; they
do not use this grammar.

`_safe_rule_name` has two defects:

- It does not lowercase. Lark reads a name containing an uppercase letter as a
  *terminal*, and Junos has elements such as
  `jnx-tel-RE-local-interfaces-stats`, which produced
  `jnx_tel_RE_local_...` and an unparseable grammar. Found on a real 23.2R2
  dump; 24.4R0 happens to have no such element.
- It does not reserve the grammar's own `start`. Junos has `start-options`, so
  the generator emitted a second `start:` rule beside the entry rule. The
  bundled grammar has carried two since the 24.4 migration in `3b55b78`,
  confirmed by loading the pre-onboarding artifact.

Neither was reachable from the synthetic fixtures: a device dump found the
first, and the second sat in a file nothing loaded.

## What Changes

- Lowercase generated rule names.
- Reserve `start`; a schema element of that name becomes `start_element`.
- Three unit tests on `_safe_rule_name`, needing no device data.
- `TestBundledGrammarCompiles`, loading the shipped grammar. `xfail(strict=True)`
  today, because the committed artifact is still the broken one; regeneration
  turns it into an unexpected pass, which is the signal to delete the xfail.

## Capabilities

### New Capabilities

None; this repairs an existing one.

### Modified Capabilities

No requirement changes, so `.openspec.yaml` sets `skip_specs: true`.

## Non-goals

- Regenerating the bundled artifacts: that needs a dump at the shipped release,
  and the only one to hand is 23.2R2 against a bundled 24.4R0.
- Hand-patching `junos-set.lark`. `ARCHITECTURE.md` section 8 forbids editing a
  generated artifact, and the next regeneration would undo it.

## Impact

`src/junoscfg/validate/grammar_generator.py` and its tests. Future grammars get
lowercase rule names and a renamed `start` element. Set validation stays broken
for users until the artifacts are regenerated: this fixes the generator, and
the shipped artifact is a separate thing.
