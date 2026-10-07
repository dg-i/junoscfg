## Why

Running the downstream `dgi/junos-config` collection's example playbook and
validating what it rendered gave **7 false errors per host**; the collection is
in production, so `-v` was unusable for it. Pointing junoscfg at three real
devices then at the stanzas they render took the total to 507 of 7,093 set
commands rejected, every one of them valid configuration.

None of it was reachable from `examples/router1.set`, which I wrote, or from
the corpus harvested out of this repository's own tests. The shapes only exist
on real hardware: `set groups <n> ...` is six of the seven playbook errors, and
`groups` is the one transparent child of 135 in 24.4R0 that is not `nokeyword`
— the review of `grammar-named-lists` predicted exactly that, and I recorded it
as an accepted cost while the collection renders into it by default.

## What Changes

Seven shapes the generator read wrongly, every one found on a real device and
none reachable from a committed fixture:

- A child the parent is transparent over is spliced, as a `nokeyword` child was.
- `_strip_apply_groups` also strips `apply-flags` and `apply-macro`, and a bare
  `set apply-groups <n>`, which stripping reduced to `set`, is accepted.
- A named list's entry name, and every leaf value, is `QUOTED_OR_VALUE`: a real
  configuration nests a `set` command inside `event-options policy <n> then
  change-configuration commands "..."`, and `VALUE` is `/\S+/`.
- A oneliner list of bare keywords takes them on either side of the entry name;
  `community add COMM-A` and `flag all detail` disagree and the schema is silent.
- A presence list takes its entry name; 5,808 nodes emitted a bare keyword.
- A parenthesised policy expression is one value. A device carries it as one
  opaque string and junoscfg already converted it to that, so only the grammar
  was wrong.

## Capabilities

### New Capabilities

None; this repairs an existing one.

### Modified Capabilities

No requirement changes, so `.openspec.yaml` sets `skip_specs: true`.

## Non-goals

- The over-rejection that remains: 104 of 116 corpus commands, with bracket
  lists the largest class. `xsd_fixes` carries an `accepts-bracket` flag the
  generator still ignores.
- Running the collection's playbook in CI; verified by hand instead.
- The 2.3% of real configurations still rejected, chiefly
  `snmp filter-interfaces interfaces <n>`.

## Impact

`grammar_generator.py`, `set_validator.py` and `data/junos-set.lark`. The
collection's rendered configs validate clean, from seven errors each. Measured
on three real device configurations, 7,093 set lines: rejections fall from
roughly 40% before this session's grammar work to 2.3%. The corpus goes 100 to
105 of 116, all nine adversarial commands are still rejected, and grammar load
rises 4.3s to 5.7s.
