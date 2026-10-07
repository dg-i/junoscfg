## Why

Running the downstream `dgi/junos-config` collection's example playbook and
validating what it rendered gave **7 false errors per host**; the collection is
in production, so `-v` was unusable for it. Three causes, none of which
`examples/router1.set` or the harvested corpus exposed:

- `set groups <name> ...` — six of the seven. `groups` carries
  `transparent:group`, and `group` is the one transparent child of 135 in
  24.4R0 that is not `nokeyword`, so the splice added in `grammar-named-lists`
  missed exactly it. Its own review predicted this; the corpus confirmed it;
  the collection renders `global_personalized_users` into it by default.
- `set ... apply-flags replace` — `apply-flags`, `apply-macro` and
  `apply-groups` are universal Junos meta-statements and none is in the schema.
  Only `apply-groups` was stripped before parsing.
- `set ... authentication ssh-ed25519 "ssh-ed25519 AAAA..."` — `ssh-ed25519` is
  itself a list, so the key is the entry name, which is quoted and holds
  spaces, and list rules took `VALUE`, which is `/\S+/`.

## What Changes

- A child the parent is transparent over is spliced, as a `nokeyword` child
  already was.
- `_strip_apply_groups` also strips `apply-flags` and `apply-macro`.
- A named list's entry name is `QUOTED_OR_VALUE`.
- Every leaf value is `QUOTED_OR_VALUE`, not thirteen hard-coded names: a real
  configuration puts a nested `set` command inside `event-options policy <n>
  then change-configuration commands "..."`, and `VALUE` is `/\S+/`.
- A oneliner list of bare keywords takes them on either side of the entry
  name; nothing in the schema says which, and `community add COMM-A` and
  `flag all detail` disagree.
- The grammar is rebuilt.

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
