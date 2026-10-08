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

## Fresh review findings

### P1: isolate flat-positional rules

The first implementation stored positional metadata on a globally merged rule,
so a marked container could give compact sibling syntax to an unmarked
same-named container. The reviewer executed a counterexample and found mixed
marked/unmarked names in the shipped tree. Add a metadata-specific rule suffix
and a same-name collision regression.

### P1: use the declared-break version bump

The change declares `api` and `cli` surface changes. Beta policy maps either
declared break to a minor bump, so the release is `0.12.0`, not `0.11.3`.

### P2: keep the performance claim reproducible

The accepted implementation's five-second bound for 100 commands is executable,
but the historical 228 ms versus 4 ms comparison cannot be reconstructed from
committed repository state. Make the executable bound the requirement and keep
the historical measurement out of the change's claims.

## Review resolution

- Flat-positional parent rules use a metadata-specific `__pkf` suffix, and a
  stable variant identity propagates through affected ancestor rules. Ordinary
  alternatives retain the established global union; only metadata-sensitive
  child references remain path-local. Same-named child and parent regressions
  failed before their corrections and pass afterwards.
- The project, package, CLI assertion, and lockfile now agree on version
  `0.12.0`.
- Proposal, specification, implementation commentary, and validation guide now
  rely on the executable five-second/100-command guard rather than the
  unreproducible historical comparison.
- After the corrections, pre-commit passes and the full suite reports 1,587
  passed, 72 skipped, and the one bracket-list xfail.

## Correction review

The reviewer found that the first `__pkf` correction still leaked through a
same-named parent rule and that the proposal still said "patch version". The
second correction propagates variant identity through ancestors, pins the
shipped SNMP/BGP `traceoptions` collision, preserves the existing ordinary-rule
merge, and records the minor bump consistently. Final pre-commit and the full
suite are green with 1,587 passed, 72 skipped, and one xfailed bracket-list case.
