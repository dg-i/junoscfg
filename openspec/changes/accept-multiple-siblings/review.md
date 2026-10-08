## Specification challenges

### Flat positional metadata also resolves the traceoptions-file rejection

- **Artifact:** Reviewed acceptance test
  `tests/test_set_corpus.py::TestShippedGrammarAgainstTheCorpus::test_rejections_are_exactly_the_recorded_ones`.
- **Counterexample:** Executed after regenerating the shipped grammar:
  `set protocols bgp traceoptions file bgp-log size 10m files 10` now validates,
  while the exact-corpus test still records it as an over-rejection with code
  `merged`. The shipped `file` rule has the same `positional-key-flat` value
  followed by known keyworded siblings as the approved maximum-prefixes case.
- **User impact:** Keeping the generic metadata rule fixes this third compact
  command as well as the two named examples. Narrowing the implementation to
  the named examples preserves the old false rejection but makes the behavior
  special-case driven rather than metadata driven.
- **Proposed correction:** Keep the generic rule and remove the traceoptions
  command from `OVER_REJECTED`; add it to the compact-form acceptance cases so
  this consequence remains explicit.
- **Decision:** Accepted by the owner on 2026-10-08. Keep the generic
  metadata-driven rule, remove this command from `OVER_REJECTED`, and pin it
  alongside the other compact-form acceptance cases.

## Carry-forward

- `agent-ready render codeowners --check` fails on unchanged `.github/CODEOWNERS`
  already present on local `master`; regenerate it in template maintenance.
- `agent-ready render levers --check` cannot render the unchanged stage-lever
  blocks on local `master` because the result would contain a TOML table/key
  collision; reconcile it through `agent-ready-refresh`, not this grammar fix.
