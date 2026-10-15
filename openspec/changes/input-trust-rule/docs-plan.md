## Reader and task

- Reader: a contributor about to add a size limit, timeout or parser workaround; a caller
  deciding whether junoscfg protects them from hostile configuration.
- Task: learn that configuration input is trusted, why, what is still fixed, and where the
  decision lives.

## Authoritative sources

| Claim | Source |
|---|---|
| The rule and its reason | the owner's first-hand instruction of 2026-10-15 (`instruction-integrity.md`) |
| The alias bounds were the only hostile-input protection | `docs/reviews/2026-10-15-trusted-input-retirement.md`, main result |
| The 64-level ceiling and cycle refusal stay as own-crash fixes | `docs/decisions/2026-10-15-yaml-nests-at-most-64-levels.md`; `src/junoscfg/input.py` `find_non_json_value` |
| An anonymized run's messages withhold values | `tests/contract/test_every_message.py` (anonymized runs only); `src/junoscfg/convert/__init__.py` (reader refusals quote input unless the run anonymizes) |
| Code that handles PyYAML output, kept | `src/junoscfg/convert/output/json_output.py` (`_JunosYamlDumper` quotes NEL, LS, PS); `docs/BACKLOG.md` YAML-DATE-001 (kept), YAML-BREAKS-001 (open owner question) |

## Affected documents

- `ARCHITECTURE.md` section 8: cross-cutting rules live there (the owner asked for it there);
  the yaml-new paragraph points at the rule instead of restating a YAML-only assumption.
- `docs/decisions/2026-10-15-configuration-input-is-trusted.md` (new) and the rendered
  `docs/decisions/index.md`: a decision and its review date belong in a record.
- `docs/decisions/2026-10-15-yaml-nests-at-most-64-levels.md`: its consequence is a case of
  the rule, so it cites it.
- `docs/guide/conversion.md` (yaml-new reading rules) and `docs/api/input.md`
  (`find_non_json_value`): where a user meets the YAML assumption.
- `src/junoscfg/input.CONTRACT.md`, `src/junoscfg/convert/CONTRACT.md`: the invariants that
  stated the YAML-only assumption.

## Documentation QA

- Links: `uv run --locked --group docs mkdocs build --strict` exits 0 with no new warning.
- Commands and examples: not applicable, because the change adds no command or example.
- Referenced paths and decision slugs exist (`ls` on each path the changed text names).
- Diátaxis placement: explanation in `ARCHITECTURE.md` and the decision record; the guide,
  API page and contracts only point at it; no new page.
- Caps: `ARCHITECTURE.md` stays at or under 200 lines (`agent-ready caps`).
- Terminology: no tracked document outside the archive and reviews states a YAML-only trust
  assumption without the rule (`git grep -n "not hostile"`), C2/C3 aside.
- Rendered output: markdownlint passes (pre-commit).
- One full checkpoint passes.
