## Why

The bundled 24.4R0 artifacts are defective, not merely old: `firewall family
inet6 filter term from hop-limit` and `forwarding-options analyzer` fail only
against them across seven releases from 21.4R0 to 25.2R2, and the dump they
came from no longer exists, so they can be neither rebuilt nor audited. That
gap was 20 of the 21 rejected lines across three real devices, and every
`hop-limit` converted to a fused key rather than a statement with a value.
Evidence and the owner's decision are in the private assessment of 2026-10-08.

## What Changes

- The five artifacts are regenerated from the 25.2R2-S1.5 QFX5120 dump in
  `private_test_data/schemas/`; the invariant is that the shipped release is
  one whose dump is to hand. **BREAKING** on `api` and `cli`: what validates
  and what converts moves where the releases differ.
- The regenerated tree carries the four `apply-*` statements with the
  `universal` flag, so the set validator's bridge goes, as its docstring said
  it would: `_strip_apply_groups`, `_inside_quotes` and the early return,
  with the two tests that went red together on that day.
- Documentation that named 24.4R0 names 25.2R2; `schema info` reports 25.2R0,
  the namespace the dump declares.

## Capabilities

### New Capabilities

None; the same artifacts, from a release that can be rebuilt.

### Modified Capabilities

None at spec level, so `.openspec.yaml` sets `skip_specs: true`.

## Non-goals

- What the converter does with a statement it cannot model.
- The `uplink-failure-detection group` shape, which is the same on 25.2R2.
- Making `--regen-schema` name its release; today it picks the newest dump,
  which is now the one shipped.

## Impact

Same inputs before and after: three real devices 21 to 1 rejected set lines,
of 6,998 under the old artifacts and 7,002 under the new, since `hop-limit`
stops fusing; the one left is `chassis dump-on-panic`, in no XSD of any release;
against the device's own `| display json` of a `firewall family inet6`
subtree 0 missing and 0 extra paths, from 1 and 3; `tests/data/set_corpus.txt`
10 of 116 rejected on the artifacts alone, the same ten, and 14 once the
bridge went, the four being `apply-groups` after a leaf value, which is not
Junos; jvd 1,500 of 1,535 converted and 233 field warnings, unchanged; grammar
load 4.6 s, unchanged; artifacts 2.57 to 2.48 MB.
