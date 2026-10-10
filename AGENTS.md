# AGENTS.md

Instructions for agents and human contributors. What this system *is* — its goals,
constraints, layering and cross-cutting rules — is `ARCHITECTURE.md`. This file is
only the house rules: break one and the repository is badly written, not wrong.

## Project Overview

Python toolkit for converting, validating, anonymizing and auditing Junos
configurations between XML, JSON, structured, YAML and display set formats.
Originally inspired by the [Ruby Junoser gem](https://github.com/codeout/junoser).

<!-- agent-ready:stage:begin -->
## Stage

beta: what the named surfaces do today holds until the next minor release under
this repository's versioning scheme. A change to one of them is declared in the
change's `.openspec.yaml` with its migration, and a removal is deprecated first.
Named surfaces: consumer, cli. The change that retires an import bans it: list
the import under `bans` in the decision record that retires it and run
`agent-ready render levers`, which renders the ban into `pyproject.toml`. What
each stage flips is in the `## Stage` section of every phase of
`agent-ready-change`, and the lever blocks of `pyproject.toml` carry what this
stage renders.
<!-- agent-ready:stage:end -->

## Before you edit a module

1. Read its `CONTRACT.md` (or `<module>.CONTRACT.md`) — invariants and what the
   module is *not* for.
2. Prefer an existing helper. `display` is the shared kernel; six packages
   import from it, and a seventh copy of a formatter belongs there instead.
3. Import through the package door, never a submodule path: `tach check` and
   `agent-ready interfaces` both refuse `junoscfg.display.constants.X`.
4. A knowledge graph of this repository lives in `graphify-out/`;
   `/graphify query "<question>"` answers architecture and "what touches X"
   questions from it, alongside the codemap and the `CONTRACT.md` files.

## Before you change what junoscfg accepts

**Ask for a device artefact before inferring**, in set, JSON and XML: device output outranks the schema model
([evidence hierarchy, Junos correctness](ARCHITECTURE.md)). **Never request a whole configuration** — name a path.
**Equivalent, not identical**: output loads as the same configuration, whatever the device's layout. **Fix at the
owning layer, or record why not.** **Measure the blast radius before loosening**: slots and a negative test. Examples: [settle a schema question](docs/how-to/settle-a-schema-question.md).

## Verification

Use exact test nodes or affected files during implementation; grammar changes use
the focused list in [the developer guide](docs/architecture/developer-guide.md).
Before review, run one `uv run --locked agent-ready check --set full`; it replaces
pre-commit and full-pytest runs on the same tree.
After review fixes, use focused tests plus the locked `agent-ready` fast set; repeat
full only when runtime-relevant files changed after its previous result.
After XSD/schema changes, use `--regen-schema` as the developer guide describes.

## Version Management

Version lives in three places that move together: `pyproject.toml`,
`src/junoscfg/__init__.py`, and the assertion in `tests/test_cli.py`.

- A break on a named surface (`consumer`, `cli`) raises the **minor**, as
  `[tool.template.stage] break-bumps` declares. Everything else is a patch.
- Bump in the same commit as the code; tag `v{version}` after committing.

## Documentation Checklist

1. Every `@click.option` in `cli.py` is in generated `docs/guide/cli-reference.md`.
2. Every name in a module's `__all__` appears in its `docs/api/` page.
3. Python snippets use real names from `__all__`.
4. Any `src/junoscfg/...` path in `docs/architecture/` points at a real file.
5. Every `.md` under `docs/` is in `mkdocs.yml` `nav:` or its `not_in_nav`.
6. Adding or removing an XSD fix updates the counts in
   `docs/architecture/developer-guide.md` and `schema-internals.md`.
7. `README.md` mentions every major feature and imports only real names.
8. `[Ruby Junoser gem]` citations name the upstream Ruby project; never rename them.

## Test Data Conventions

Never use real operator data. Real configurations go in `private_test_data/`,
which is gitignored except its README.

| Category | Standard values | Notes |
|----------|----------------|-------|
| AS numbers | 64496-64511 | RFC 5398 documentation range |
| IPv4 (to anonymize) | 203.0.114.x, 198.0.2.x | Outside the documentation ranges |
| IPv4 (preserved) | 10.x, 192.168.x, 198.51.100.x | RFC 1918 / RFC 5737 |
| IPv6 (to anonymize) | `3ffe:0b00:*` | Old 6bone (RFC 3701) |
| Passwords | `$9$ExAmPlEhAsH.KEY` | Synthetic `$9$` format |
| Usernames / hostnames | admin, operator, router1, sw1 | Generic |

## Where things are

| Looking for | Read |
|---|---|
| Layering, the one-IR rule, error handling | `ARCHITECTURE.md` section 8 |
| The three pipelines in detail | `docs/architecture/developer-guide.md` |
| Why a conversion renders wrongly | `docs/architecture/conversion-bugfix-guide.md` |
| Approved tools and versions | `docs/TOOLBOX.md` |
| A decision and its expiry | `docs/decisions/index.md` |
| How to run a change | the `agent-ready-change` skill |
