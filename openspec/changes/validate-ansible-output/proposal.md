## Why

Running the downstream `dgi/junos-config` collection's own example playbook and
validating what it rendered reported **7 errors per host** on valid
configuration. The collection is in production, so `-v` was unusable for it.
Three causes, none of which `examples/router1.set` or the harvested corpus
exposed:

- `set groups <name> ...` — six of the seven. `groups` carries
  `transparent:group`, and `group` is the one transparent child of 135 in
  24.4R0 that is not `nokeyword`, so the splice added in `grammar-named-lists`
  missed exactly it. Its own review predicted this; the corpus confirmed it;
  the collection renders `global_personalized_users` into it by default.
- `set ... apply-flags replace` — `apply-flags`, `apply-macro` and
  `apply-groups` are universal Junos meta-statements and none is in the schema.
  Only `apply-groups` was stripped before parsing.
- `set ... authentication ssh-ed25519 "ssh-ed25519 AAAA..."` — `ssh-ed25519` is
  itself a list, so the key is the entry name, and a key is quoted and contains
  spaces. List rules took `VALUE`, which is `/\S+/`.

## What Changes

- A child the parent is transparent over is spliced, as a `nokeyword` child
  already was. `_collect_rules` knows the parent, so it passes the hint.
- `_strip_apply_groups` also strips `apply-flags` and `apply-macro`.
- A named list's entry name is `QUOTED_OR_VALUE`.
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
- Running the collection's playbook in CI. It needs ansible-core and a
  checkout of another repository; this change verified it by hand.

## Impact

`grammar_generator.py`, `set_validator.py` and `data/junos-set.lark`. The
collection's rendered `router1.conf` and `router2.conf` both validate clean,
where they reported seven errors each. The corpus goes 100 to 104 of 116, all
nine adversarial commands are still rejected, and cost is unchanged at about
4s to compile and 4 ms a line.
