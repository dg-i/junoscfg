# Architecture

arc42 numbering. Sections 1, 2, 3, and 8 are required; the rest are headings the
linter accepts and never demands. A section that is present but does not apply
carries one line saying so and a pointer.

## 1. Introduction and goals

junoscfg converts, validates, anonymizes and audits Junos device
configurations between five representations — display set, structured
(curly-brace), XML, JSON and YAML — and turns them into Ansible variable
files. It is a library first and a CLI second: every capability a downstream
consumer would otherwise reimplement lives in the public API, and `cli.py`
only parses arguments and formats output.

When two of these conflict, the order is:

1. **Correctness** — a converted configuration must mean what the input meant.
2. **Simplicity** — a second way to do the same conversion is a defect.
3. **Cost / size** — accepted: ~36 MB of schema artifacts ship in the wheel.
4. **Latency** — last; a multi-megabyte schema load on start-up is tolerated.

The ranking is visible in the record. `tests/test_convert_consistency.py`
asserts every format pair agrees and every round trip preserves content.
`docs/architecture/design-decisions.md` records rejecting both a prefix trie
and a Lark grammar for set-to-structured conversion because each got
context-dependent elements wrong, in favour of a slower schema tree walk. XML
output raises `NotImplementedError` rather than emit something approximate.
And `src/junoscfg/validate/data/` bundles ~36 MB of generated artifacts rather
than fetching or deriving them at run time.

## 2. Constraints

- **Offline.** The package opens no sockets and spawns no processes: no
  `socket`, `urllib`, `requests`, `httpx` or `subprocess` import exists under
  `src/junoscfg/`. Retrieving an XSD dump from a router is the operator's own
  `ssh ... netconf` pipeline, documented in README.md; junoscfg reads the
  resulting file.
- **Python 3.13 or later.** Decided in onboarding, against the measurement:
  the suite is 1373-green on 3.14 and 6-red on both 3.11 and 3.12, all six in
  `tests/test_anonymize/test_password_rule.py`. `_make_crypt_hash()` calls
  `crypt.crypt()`, which macOS answers with a 13-character DES hash instead of
  the requested `$1$`/`$5$`/`$6$` format; from 3.13 the module is gone and the
  documented fallback runs. The declared floor was `>=3.10`; aligning
  `requires-python`, the classifiers, `ruff target-version`, `mypy
  python_version` and `.copier-answers.yml` is the first tracked change.
- **lxml is optional.** XML input, XSD extraction and XSD parsing need the
  `xml` extra; `_ensure_xml_imports()` in `src/junoscfg/display/to_yaml.py`
  imports it lazily so that every non-XML conversion path works without it.
- **The schema is pinned to one Junos release.** The bundled artifacts are
  currently Junos 24.4R0 (commit 3b55b78). Structural corrections live in
  `validate/xsd_fixes.py` as Python, not in the artifacts, so they survive any
  regeneration.
- **Real router configurations stay out of the public repository.** They go in
  `private_test_data/`, which is gitignored; tests use the synthetic ranges in
  AGENTS.md. No external regime stands behind this — the content is router
  configuration, not personal data — so it is a repository rule rather than a
  compliance boundary.
- **MIT licence; published to PyPI** from `.github/workflows/publish.yml` on a
  GitHub release, via trusted publishing.

## 3. Context and scope

**Who calls this system**

- Network operators, through the `junoscfg` CLI: `convert` (the default
  subcommand), `edityaml`, `schema`, `audit`.
- **`dg-i/ansible-collection-junos-config`, in production.** It pins
  `junoscfg>=0.5.8` and its `render` filter
  (`plugins/filter/junos_config.py`) imports exactly four names from the
  top-level package: `convert_config`, `validate_config`, `Format` and
  `FieldValidationError`. Its documented pipelines also drive the CLI:
  `convert -e yaml`, `edityaml rename-root`, `edityaml ansibilize --root`.
  This consumer must keep working; it is why `api` and `cli` are the declared
  surfaces in `[tool.template.stage]`.

**What it consumes**

- Junos configuration text in five formats, from a file or stdin.
- NETCONF XSD dumps, as a file the operator captured.
- Third-party libraries on the other side of an edge: `lark` (set-command
  grammar), `ipanon` (prefix-preserving IP mapping), `netutils` (Juniper `$9$`
  constants), `lxml` (XML and XSD), `click`, `jsonschema`, `pyyaml`.

**What it produces**

- Converted configuration text; validation results; an anonymization mapping
  that `anonymize/revert.py` can replay; Ansible `host_vars` / `group_vars`;
  unused-object audit reports and delete scripts.

**Where responsibility ends**

- It never talks to a router and never applies a configuration. Capture and
  deployment are the operator's.
- It does not emit XML: `convert_config()` raises `NotImplementedError` for
  `Format.XML` output.
- It does not own the schema's truth. Juniper's XSD is upstream; junoscfg
  corrects known structural defects in `xsd_fixes.py` and says so.
- The Ruby Junoser gem is ancestry, not a dependency or an interface.

## 8. Cross-cutting concepts

<the rules that hold everywhere: layering, error handling, money, time, identity>
