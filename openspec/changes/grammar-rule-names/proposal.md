## Why

`junoscfg -i set -v` validates nothing: the bundled grammar fails to load with
`Rule 'start' defined more than once`, so a valid configuration and one naming
a nonexistent element alike report "Error loading validation artifacts".
Structured input is affected too — `JunosValidator` wraps the same
`SetValidator`. JSON and YAML are unaffected.

`_safe_rule_name` has two defects:

- It does not lowercase, and Lark reads a name containing an uppercase letter
  as a *terminal*. Junos has `jnx-tel-RE-local-interfaces-stats`; found on a
  real 23.2R2 dump, where 24.4R0 happens to have no such element.
- It does not reserve the grammar's own `start`. Junos has a `start` element,
  so the generator emitted a second `start:` rule beside the entry rule —
  there since the 24.4 migration in `3b55b78`.

Neither was reachable from the synthetic fixtures: a device dump found the
first, and the second sat in a file nothing loaded.

## What Changes

- Lowercase generated rule names; reserve `start`, so a schema element of that
  name becomes `start_element`.
- Unit tests on `_safe_rule_name`, needing no device data.
- `TestBundledGrammarCompiles`, `xfail(strict=True)` while the committed
  artefact is the broken one; regeneration turns it into an unexpected pass.
- Two more `xfail(strict=True)` pins, each with a passing control, for the
  further defects that keep a *rebuilt* grammar from working: rules merged by
  name across the tree strip the key slot from named lists, and transparent or
  nokeyword list children are not spliced. Their docstrings carry the detail.
  Rebuilt, the grammar still rejects 49 of the 61 set lines in
  `examples/router1.set`, so regenerating is not sufficient to restore set
  validation.

## Capabilities

### New Capabilities

None; this repairs an existing one.

### Modified Capabilities

No requirement changes, so `.openspec.yaml` sets `skip_specs: true`.

## Non-goals

- Regenerating the bundled artefacts. Three dumps are synced — 23.2R2-S7.5,
  23.4R2-S6.6, 25.2R2-S1.5 — but none is the shipped 24.4R0, and the newest is
  no substitute: from a device without those packages it loses 48% of
  `services`, 95% of `unified-edge` and 60% of `security`, 7,096 nodes net
  across shared sections against 22 gained OpenConfig/IETF ones.
- Fixing the further defects. They are pinned, not repaired, here.
- Hand-patching `junos-set.lark`. `ARCHITECTURE.md` section 8 forbids editing
  a generated artefact.

## Impact

`grammar_generator.py` and its tests. Set and structured validation stay broken
for users: this fixes one defect of three.
