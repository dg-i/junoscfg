## Why

Running the downstream `dgi/junos-config` collection's example playbook and
validating what it rendered gave **7 false errors per host**; the collection is
in production, so `-v` was unusable for it. Widening to three real devices took
the count to 507 of 7,093 set commands rejected, every one valid.

None of it was reachable from `examples/router1.set`, which I wrote, or from
the corpus harvested out of this repository's tests. `set groups <n> ...` alone
was six of the seven playbook errors, and `groups` is the one transparent child
of 135 in 24.4R0 that is not `nokeyword` — the review of `grammar-named-lists`
predicted exactly that and I recorded it as an accepted cost, while the
collection renders into it by default.

## What Changes

Nine shapes the generator read wrongly, every one found on real data:

- A child the parent is transparent over is spliced, as a `nokeyword` child was.
- A named list's entry name, and every leaf value, is `QUOTED_OR_VALUE`.
- A oneliner list of bare keywords takes them on either side of the entry name.
- A presence list takes its entry name; 5,808 nodes emitted a bare keyword.
- A parenthesised policy expression is one value, which the device's own
  `| display json` confirmed it carries as one opaque string.
- `flat-dict` and `flat-entry` take a run of values: they mark where the tree
  is not the syntax, and neither of the 154 such nodes was read.
- `apply-flags` and `apply-macro` are stripped like `apply-groups`; a bare
  `set apply-groups <n>` is accepted; and the stripper stops at a quote, so a
  `description "... to apply-groups foo"` keeps its closing quote.

## Capabilities

### New Capabilities

None; this repairs an existing one.

### Modified Capabilities

No requirement changes, so `.openspec.yaml` sets `skip_specs: true`.

## Non-goals

- The 21 lines still rejected, 0.30%. Every one is a statement the bundled
  24.4R0 schema does not model: `hop-limit` (18, present in 23.2R2),
  `analyzer` (2) and `dump-on-panic` (1). No junoscfg defect remains here.
- `positional-key`, `positional-key-flat` and `transparent-list-key`, unread
  across 6,436 nodes; nothing in any corpus reaches them, and
  `accepts-bracket` is never serialised at all.
- Running the collection's playbook in CI; verified by hand instead.

## Impact

`grammar_generator.py`, `set_validator.py` and `data/junos-set.lark`. Over
7,093 set commands from a border router, an admin switch and a lab switch,
rejections fall from 507 to 21 — 7.1% to 0.30% — and the admin switch
validates completely clean. The committed corpus goes 100 to 106 of 116, all
nine adversarial commands are still rejected, and grammar load rises 4.3s to
4.9s.
