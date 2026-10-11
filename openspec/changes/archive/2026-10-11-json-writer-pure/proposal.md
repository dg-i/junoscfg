## Why

`junoscfg.convert.from_dict(ir, "json")` rewrites the IR its caller holds
(ARCH-C11): presence normalization turns `ssh: true` and the set reader's
`ssh: {}` into `[null]`, and scalar coercion turns `class: ["super-user"]`
into `"super-user"`, nested group entries included. A caller that renders JSON
and then another format, or keeps the IR, sees an IR it never wrote.

## What Changes

- The JSON writer normalizes its own copy of the IR; the caller's IR is left
  unchanged. JSON output is unchanged, `_native_groups` included: the device
  writes `"groups": [...]` (ARCH-C15, INTENTIONAL, three captures cited in the delta).
- A law at the owning door: no writer (set, structured, JSON, YAML) changes
  the IR it is given, for every catalogue source and the hand-built spellings.
- `convert/CONTRACT.md` gains the invariant; patch bump to 0.16.1, no named
  surface behaviour changes (`convert_config` reads a fresh IR).

## Capabilities

### New Capabilities

- `conversion/writers`: a writer leaves its input alone; JSON writes native `groups`.

### Modified Capabilities

- None.

## Non-goals

- Changing any output, or the IR split for `groups` between readers (NEW-A3, change 13).
- Rewriting the JSON writer's three passes as one; copying once is the rule.

## Impact

`src/junoscfg/convert/output/json_output.py` (zone conversion), its contract,
`tests/unit/convert/test_convert_roundtrip.py`, `docs/guide/conversion.md`, version files and changelog.
Reproduce: `private_test_data/makeover-work/c11_mutation.py`.
