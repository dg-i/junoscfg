# Toolbox

Generated from `[tool.template.toolbox]` in `pyproject.toml` by `agent-ready render toolbox`. Not hand-edited.

## Approved

| Tool | Purpose | Minimum version | Licence |
| --- | --- | --- | --- |
| ruff | format and lint | 0.15.0 | MIT |
| mypy | types, whole package; 102 errors in 25 of 68 files at adoption, so phase 4 installs it warn-mode against a baseline | 2.4.0 | MIT |
| pytest | tests | 9.0.2 | MIT |
| deptry | undeclared and unused dependencies | 0.25.1 | MIT |
| tach | module boundaries and the public name surface | 0.35.1 | MIT |
| griffe | the symbol index, and the API surface check in the mode the stage sets | 2.3.0 | ISC |
| markdownlint-cli | duplicate headings and dead fragments | 0.45.0 | MIT |
| PyYAML | YAML input and output in the conversion pipeline; also workflow metadata and decision front matter | 6.0.3 | MIT |
| agent-ready-checks | the checks no tool covers, starting with document caps | 0.10.0 | see LICENCE |
| openspec | the change folder and the specs: new change, validate, archive | 1.13.0 | MIT |
| copier | the versioned template: copy at adoption, update afterwards | 9.0.0 | MIT |
| peter-evans/create-pull-request | opens the scheduled update pull requests | 7.0.0 | MIT |
| click | CLI argument parsing and command groups | 8.3.1 | BSD-3-Clause |
| jsonschema | validate JSON and YAML configurations against the generated JSON Schema | 4.26.0 | MIT |
| lark | grammar-based parser for set-command validation, from the generated grammar | 1.3.1 | MIT |
| ipanon | prefix-preserving IP address anonymization; first-party, github.com/dg-i/ipanon | 0.3.3 | MIT |
| netutils | Juniper $9$ encoding constants for the password anonymizer | 1.17.1 | Apache-2.0 |
| lxml | XML parsing and XSD extraction; optional, behind the xml extra | 6.0.2 | BSD-3-Clause |
| mkdocs | the documentation site | 1.6.1 | BSD-2-Clause |
| mkdocs-material | the documentation theme | 9.7.1 | MIT |
| mkdocstrings | API reference pages generated from docstrings | 1.0.3 | ISC |
| uv | the runner every documented command goes through; tests/conftest.py shells out to it under --regen-schema | 0.12.18 | Apache-2.0 OR MIT |
| git | the checks read refs: stage, lane, retired, metrics | 2.55.0 | GPL-2.0-only |
| OpenSSH (ssh, scp) | tests/integration_test.sh drives a live device; run by hand, never by pytest | 9.0 | BSD-2-Clause |

## Considered and rejected

| Tool | Reason | Date |
| --- | --- | --- |
| markdownlint for document caps | its length rules bound a line, not a file, and it cannot read a per-artefact cap from pyproject.toml; no maintained tool enforces declared per-file line budgets, which is why agent-ready-checks owns this one | 2026-09-28 |
| tach's [[interfaces]] expose on its own | it enforces the expose list only against member-path imports; a name reached as `from pkg import mod` then `mod.name` passes whatever the list says, so a codebase that imports modules rather than members has a declared interface that is never enforced. agent-ready-checks covers that half, against the same declaration | 2026-09-30 |
| import-linter | module-to-module only, so it cannot express the public name surface a module contract rests on, and it has no command that derives a first contract set from an existing codebase; it is the documented exit if tach is abandoned | 2026-09-28 |
| semgrep, Vale, a markdownlint custom rule, or git grep for the retired-terms check | the check bans a vocabulary declared per pivot across source, tests, docs, and configuration, with identifier splitting and a per-term occurrence delta; semgrep and a markdownlint rule each read one language, Vale is prose-only and is kept out of the core (AC18), and git grep has no word model and no delta. agent-ready-checks owns it | 2026-10-02 |
| griffe check alone for the release deprecation rule and the __all__ diff | it reports a removal whether or not the name carried the deprecation decorator at the previous tag, and it has no per-ref __all__ diff; both are a few lines on griffe's own load_git API, which is reuse of griffe rather than a replacement for it, and they live in agent-ready-checks | 2026-10-02 |
| cookiecutter and cruft for the template | cookiecutter has no update; cruft adds one as a patch over a fresh render, with rejected hunks as its only conflict handling and no versioned migrations, and neither renders a conditional path, which is how the skeleton stays out of a brownfield repository (AC25) | 2026-10-03 |
| OpenTelemetry SDK for change metrics import | it instruments future events but does not parse existing Codex exec and Claude stream-json files or bind a selected window to an immutable change and exact log hash; agent-ready-checks uses narrow native parsers with stdlib JSON and hashing | 2026-10-06 |
