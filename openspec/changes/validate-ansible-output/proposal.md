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
- Every leaf value is `QUOTED_OR_VALUE`, not thirteen hard-coded names. Found
  on a real 6,941-line device configuration, which puts a nested `set` command
  inside `event-options policy <n> then change-configuration commands "..."`.
  `VALUE` is `/\S+/`, so any quoted value holding a space was unparseable.
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
- The 8.6% of a real device configuration still rejected. The largest class is
  `policy-statement <n> term <t> then community add <c>`: `community` is a
  *oneliner* list, and the generator reads the `oneliner` flag nowhere, though
  24.4R0 has 3,456 such nodes. Emitting them action-first is not the fix —
  measured, it takes the real config from 308 rejections to 1,025 and the
  corpus from 104 to 73, so oneliner lists are not uniformly ordered.

## Impact

`grammar_generator.py`, `set_validator.py` and `data/junos-set.lark`. The
collection's rendered configs validate clean, from seven errors each. The
corpus goes 100 to 104 of 116, all nine adversarial commands are still
rejected, and compile rises 4.3s to 5.6s.
