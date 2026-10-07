## Why

With the rule-name collision fixed, a grammar rebuilt from the bundled 24.4R0
structure tree compiles — and then rejects 49 of the 61 set lines in
`examples/router1.set`, and 90 of the 113 distinct set commands in this
repository's own tests. A validator rejecting four fifths of valid
configuration is worse than one that fails to load. Two defects cause it:

- `_collect_rules` merges rules by name across the whole tree. A named list and
  a plain container sharing a name merged into one rule, which lost the
  entry-name slot. `user` is a list under `system login` and a container under
  `snmp`; that one collision broke every line addressing a list entry —
  `interfaces ge-0/0/0`, `system login user`, `protocols bgp group`.
- A nokeyword container is not written in a set command, but the generator
  emitted its keyword anyway. `interfaces` holds a nokeyword `interface` list,
  so `set interfaces ge-0/0/0 mtu 9192` left the parent offering a bare `VALUE`
  with nothing allowed after the name. 24.4R0 has 534 such nodes.

A third, found while testing: a container may be set bare to bring it into
being — `set system services netconf ssh` — and content was required after one.

## What Changes

- Named lists get their own rule, suffixed `__list`, so a same-named container
  cannot merge the entry name away. `_RuleInfo.has_non_list` goes with it.
- A nokeyword container contributes its content to its parent without its
  keyword, keyed on `nokeyword` rather than the `transparent:` flag, which in
  24.4R0 often names a child the node does not have.
- A non-list container's content becomes optional.
- Seven tests needing no device data; the previous change's two pins become
  regression guards.

## Capabilities

### New Capabilities

None; this repairs an existing one.

### Modified Capabilities

No requirement changes, so `.openspec.yaml` sets `skip_specs: true`.

## Non-goals

- Closing the remaining over-acceptance. A nokeyword leaf becomes a bare
  `VALUE`, which a list's repetition matches any number of times, so
  `set interfaces ge-0/0/0 bogus-thing 5` parses. Hoisting it to one optional
  slot closed three of four such cases but rejected two commands this
  repository's tests treat as valid, so it is pinned, not taken.
- Regenerating the bundled artefacts. The shipped grammar is still the broken
  one; the generator is a separate thing.
- `vlan-id` under `unit`: `_fix_vlan_id_freeform` marks every `vlan-id`
  nokeyword, so the grammar expects no keyword where a set command writes one.
  That is an `xsd_fixes.py` defect.

## Impact

`grammar_generator.py` and its tests. On the bundled 24.4R0 tree a rebuilt
grammar goes from 23 to 99 of 113 set commands, and 12 to 61 of 61 example
lines, loading in 25s against 43s under the alternative fix.
