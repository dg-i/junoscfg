## Context

The comparison needs three things the repository already has: a structured
reader that takes a fragment once it is re-rooted, a JSON writer, and the
`| display json` document the device produced. What is new is only the
pairing and the path-set comparison, which is a dozen lines. The constraint
is that the data is one operator's: the test must run where a pair exists and
stay silent where none does, without a flag, since a pair converts in
milliseconds.

## Reuse ladder

| Candidate | Coverage | Gap | Maintenance signal, lookup date | Verdict |
|---|---|---|---|---|
| `convert_config` with `Format.STRUCTURED` to `Format.JSON`, in the slice | The whole conversion | None; re-rooting is string assembly before the call | This repository, 2026-10-08 | Use |
| `json` from the standard library | Parsing the device document and junoscfg's | None | Standard library | Use |
| A diff library such as `deepdiff` | Structural comparison with values | Values are not compared, and it would be a new dependency for a set difference | Not looked up: the gap decides | Build the path set, twelve lines |

## Decisions

- Discovery over two directories, the committed one first, so publishing a
  pair is a rename and nothing in the test changes. One synthetic pair is
  committed, shaped after a device's rendering with documentation ranges, so
  the helpers run on every clone; it is self-consistent, not an oracle.
- A list entry is told from its siblings by its `name` or `address`; without
  that, siblings pool their children and two terms equal one.
- Paths, not values: the question is whether junoscfg and the device agree on
  shape, and the field validator owns values.
- `@` attributes are dropped on both sides; the device stamps commit metadata
  junoscfg has no source for.
- No pytest flag: the `--schema` and `--jvd` tiers are gated because they cost
  minutes or the network; this one costs nothing, so presence is the gate.

## Risks

- A pair captured with secrets in it. The README says to strip them; the two
  present were. A failure prints element paths only: an entry's name and a
  value fused into a key are elided, which the review found necessary, since
  a fused value is exactly what the tier exists to catch.
- The device prints a subtree's contents while `| display json` wraps to the
  root; a capture headed by the wrong path compares nothing with nothing and
  fails on the "device rendered nothing" guard rather than passing vacuously.
