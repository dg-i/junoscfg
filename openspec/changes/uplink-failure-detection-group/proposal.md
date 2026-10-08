## Why

`set protocols uplink-failure-detection group G link-to-monitor ae0` read as
one fused key, `"G link-to-monitor ae0"`, on every release held, 25.2R2
included, so it is junoscfg's and not drift. The XSD wraps the named list
`ufd-group-name` in a `group` container, the shape `groups`/`group` and
`interfaces`/`interface` take, but the transparent-container fix keys its
table by element name and `group` is also BGP's list, so it could not say so.
Step 4 of the owner's plan of 2026-10-08, under the limit "only if simple".

## What Changes

- `xsd_fixes._fix_ufd_group_transparent`, Group H: for every
  `uplink-failure-detection` whose `group` child holds `ufd-group-name`, the
  `transparent:ufd-group-name` flag. Scoped to the parent; BGP's `group` is
  untouched. Registered as `ufd-group-transparent`, 42 fixes from 41.
  **BREAKING** on `api`, as `ALL_FIXES` is, and on `cli`, as the rendering is.
- The five artifacts regenerated: only the structure tree and the metadata
  change, as a flag-only fix should; the grammar and both JSON schemas are
  byte-identical, since the grammar already took the line.
- The reader keeps `G` as the entry and its links as its children; structured
  output writes `group { G { link-to-monitor ae0; } }`; JSON keeps the
  wrapper, `"group": {"ufd-group-name": [...]}`, as Junos JSON does for every
  transparent container but `groups`.

## Capabilities

### New Capabilities

None; one conversion hint, in the fix table where the others are.

### Modified Capabilities

None at spec level; `.openspec.yaml` sets `skip_specs: true`.

## Non-goals

- Generalising the transparent table to paths, or touching the positional-key
  machinery: the owner's limit, and the parent-scoped shape needed neither.
- The two other `uplink-failure-detection` elements, under the satellite
  `extended-ports` templates, which carry no `group` and are left alone.
- Settling the JSON shape by inference. A capture of the subtree from the
  device that carries it did, the same day: the shape is the device's, and
  the device-truth tier checks it on every run.

## Impact

Fix tests on a synthetic tree, 3; a round trip on the bundled artifacts, 2.
Three real devices: unplaced statements 7 to 1, the one left `chassis
dump-on-panic`; set rejections unchanged at 1 of 7,002. The fix fires on
25.2R2 and not on 23.2R2, which lacks the statement; the metadata reads 39 of
42 applied. Full suite 1,544 passed. Minor bump to 0.10.0.
