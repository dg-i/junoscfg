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
| Messages withhold values | `tests/contract/test_every_message.py`; `ARCHITECTURE.md` section 8 (errors and diagnostics) |

## Affected documents

- `ARCHITECTURE.md` section 8 (rule, yaml-new pointer)
- `docs/decisions/2026-10-15-configuration-input-is-trusted.md` (new), `docs/decisions/index.md` (rendered)
- `docs/decisions/2026-10-15-yaml-nests-at-most-64-levels.md`, `docs/guide/conversion.md`,
  `docs/api/input.md`, `src/junoscfg/input.CONTRACT.md`, `src/junoscfg/convert/CONTRACT.md`

## Documentation QA

- Links: `uv run --locked --group docs mkdocs build --strict` exits 0 with no new warning.
- Referenced paths and decision slugs exist (`ls`).
- Caps: `ARCHITECTURE.md` stays at or under 200 lines (`agent-ready caps`).
- Terminology: no tracked document outside the archive and reviews states a YAML-only trust
  assumption without the rule (`git grep -n "not hostile"`), C2/C3 aside.
- Rendered output: markdownlint passes (pre-commit).
- One full checkpoint passes.
