## Why

With the rule-name collision fixed, a grammar rebuilt from the bundled 24.4R0
structure tree compiles — and then rejects 49 of the 61 set lines in
`examples/router1.set`. A validator rejecting four fifths of valid
configuration is worse than one that fails to load. Two defects cause it:

- `_collect_rules` merges rules by name across the whole tree. A named list and
  a plain container sharing a name merged into one rule, which lost the
  entry-name slot. `user` is a list under `system login` and a container under
  `snmp`; that one collision broke every line addressing a list entry —
  `interfaces ge-0/0/0`, `system login user`, `protocols bgp group`.
- A nokeyword container is not written in a set command, but the generator
  emitted its keyword anyway. `interfaces` holds a nokeyword `interface` list,
  so `set interfaces ge-0/0/0 mtu 9192` left the parent offering a bare `VALUE`
  with nothing allowed after the name.

A third, found while testing: a container may be set bare to bring it into
being — `set system services netconf ssh` — and content was required.

## What Changes

- Named lists get their own rule, suffixed `__list`, so a same-named container
  cannot merge the entry name away; `_RuleInfo.has_non_list` goes with it.
- A nokeyword container contributes its content to its parent without its
  keyword, keyed on `nokeyword` rather than the `transparent:` flag, which in
  24.4R0 often names a child the node does not have.
- A non-list container's content becomes optional.
- Six tests needing no device data; the previous change's two pins become
  regression guards.

## Capabilities

### New Capabilities

None; this repairs an existing one.

### Modified Capabilities

No requirement changes, so `.openspec.yaml` sets `skip_specs: true`.

## Non-goals

- Closing the remaining over-acceptance, pinned rather than taken.
- Regenerating the bundled artefacts; `rebuild-set-grammar` does that.
- `set groups ...`, which this change's choice breaks: keying on `nokeyword`
  is right for 134 of 135 transparent flags, and the exception is
  `groups`/`group`, whose child is a list carrying no `nokeyword`.

## Impact

`grammar_generator.py` and its tests; 12 to 61 of 61 example lines. Three
corrections from this change's review. The "61 of 61" is partly
undeserved: `set interfaces ge-0/0/1 unit 0 vlan-id 100` parsed only through
the over-acceptance above, until `acd0633`. The accept-rate figures measured
against 113 commands came from a scratch corpus no reviewer could reproduce;
it is committed as `tests/data/set_corpus.txt` by `rebuild-set-grammar`, and
those numbers are indicative only. And "25s against 43s" compares grammar
*load*: this emission costs ~228 ms a line to parse against ~4 ms, which
`rebuild-set-grammar` reversed two commits later. Load was the wrong measure.
