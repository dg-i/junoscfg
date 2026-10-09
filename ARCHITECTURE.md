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
3. **Cost / size** — accepted: generated schema artifacts ship compressed in
   the wheel.
4. **Latency** — last; a multi-megabyte schema load on start-up is tolerated.

The ranking is visible in the record. `tests/test_convert_consistency.py`
asserts every format pair agrees and every round trip preserves content.
`docs/architecture/design-decisions.md` records rejecting both a prefix trie
and a Lark grammar for set-to-structured conversion because each got
context-dependent elements wrong, in favour of a slower schema tree walk. XML
output raises `NotImplementedError` rather than emit something approximate.
And `src/junoscfg/validate/data/` bundles the generated artifacts in compressed
form rather than fetching or deriving them at run time.

## 2. Constraints

- **Offline.** The package opens no sockets and spawns no processes: no
  `socket`, `urllib`, `requests`, `httpx` or `subprocess` import exists under
  `src/junoscfg/`. Retrieving an XSD dump from a router is the operator's own
  `ssh ... netconf` pipeline, documented in README.md; junoscfg reads the
  resulting file.
- **Python 3.10 or later.** The suite is green on 3.10, 3.11, 3.12, 3.13 and
  3.14. Onboarding briefly raised this floor to 3.13 to get past six failures
  in `tests/test_anonymize/test_password_rule.py`; the failures were a defect,
  not a language requirement. `_make_crypt_hash()` called `crypt.crypt()`,
  which macOS answers with a 13-character DES hash instead of the requested
  `$1$`/`$5$`/`$6$` format, and which Python removed in 3.13. The branch is
  gone: the body is derived deterministically and keeps the length it replaces,
  so output is identical on every platform and interpreter.
- **lxml is optional.** XML input, XSD extraction and XSD parsing need the
  `xml` extra; `_ensure_xml_imports()` in `src/junoscfg/display/to_yaml.py`
  imports it lazily so that every non-XML conversion path works without it.
- **The schema is pinned to one Junos release.** The bundled artifacts are
  currently Junos 25.2R2, from a dump kept in `private_test_data/schemas/` so
  they can be rebuilt. Structural corrections live in `validate/xsd_fixes.py`
  as Python, not in the artifacts, so they survive any regeneration.
- **Real router configurations stay out of the public repository.** They go in
  `private_test_data/`, which is gitignored; tests use the synthetic ranges in
  AGENTS.md. No external regime stands behind this — the content is router
  configuration, not personal data — so it is a repository rule rather than a
  compliance boundary.
- **MIT licence; published to PyPI** from `.github/workflows/publish.yml` on a
  GitHub release, via trusted publishing.

## 3. Context and scope

### Who calls this system

- Network operators, through the `junoscfg` CLI: `convert` (the default
  subcommand), `edityaml`, `schema`, `audit`.
- **[https://github.com/dg-i/ansible-collection-junos-config](https://github.com/dg-i/ansible-collection-junos-config),
  in production.** It pins
  `junoscfg>=0.5.8` and its `render` filter
  (`plugins/filter/junos_config.py`) imports exactly four names from the
  top-level package: `convert_config`, `validate_config`, `Format` and
  `FieldValidationError`. Its documented pipelines also drive the CLI:
  `convert -e yaml`, `edityaml rename-root`, `edityaml ansibilize --root`.
  This consumer must keep working; it is why `consumer` and `cli` are the
  declared surfaces in `[tool.template.stage]`. The consumer surface is the
  top-level package file that carries those four imports; secondary package
  doors remain available but are not compatibility promises during beta.

### What it consumes

- Junos configuration text in five formats, from a file or stdin.
- NETCONF XSD dumps, as a file the operator captured.
- Third-party libraries on the other side of an edge: `lark` (set-command
  grammar), `ipanon` (prefix-preserving IP mapping), `netutils` (Juniper `$9$`
  constants), `lxml` (XML and XSD), `click`, `jsonschema`, `pyyaml`.

### What it produces

- Converted configuration text; validation results; an anonymization mapping
  that `anonymize/revert.py` can replay; Ansible `host_vars` / `group_vars`;
  unused-object audit reports and delete scripts.

### Where responsibility ends

- It never talks to a router and never applies a configuration. Capture and
  deployment are the operator's.
- It does not emit XML: `convert_config()` raises `NotImplementedError` for
  `Format.XML` output.
- It does not own the schema's truth. Juniper's XSD is upstream; junoscfg
  corrects known structural defects in `xsd_fixes.py` and says so.
- The Ruby Junoser gem is ancestry, not a dependency or an interface.

## 8. Cross-cutting concepts

**Layering.** The package import graph is a DAG with no cycles, enforced by
`tach check`. Dependencies run one way:

```text
display + input.py        shared kernel
  <- validate, anonymize  schema and rules
  <- convert              the pipeline; also imports anonymize
  <- audit                reads the pipeline's output
  <- cli.py, __init__.py  the two declared surfaces
edityaml                  standalone: imports nothing else in the package
```

A new edge that points up this list is a defect. `display` is the kernel by
use, not by name: `config_store.py` and `constants.py` are a data structure and
a schema-flag table, not display logic.

**One interchange format.** Every conversion is `format -> dict IR -> format`;
there is no direct format-to-format path and adding one is the "second way to
do the same thing" that section 1 calls a defect. XML input and XML-to-YAML
share the display kernel's `xml_to_dict()` walker; conversion input normalizes
its result directly without a serialization round trip. One configuration has
one IR whatever format it arrived in: leaf values are strings, leaf-lists are
arrays, and `KEY_ALIASES` is applied on every input path.

**Generated artifacts are never hand-edited.** Everything under
`validate/data/` comes from the XSD pipeline. A correction goes in
`xsd_fixes.py` as Python so that it survives the next regeneration; editing the
JSON is a change that the next `--regen-schema` silently reverts.

**Errors and diagnostics leave through separate deliberate doors.** Schema
validation returns a `ValidationResult`; a structural failure raises
(`SchemaLoadError`, `AuditLoadError`, `FieldValidationError`, `ValueError`);
and non-fatal conversion events are immutable `Diagnostic` values on a
`ConversionResult`. Library calls never write those events to a terminal. The
CLI renders their stable text to stderr, while in-process consumers decide how
to route or suppress them.

**Not applicable here.** No money, no wall-clock time, no user identity or
authorization: junoscfg is a pure text-to-text transformation with no session
and no clock. The one identity-shaped concern is anonymization, whose mapping
is deterministic from a caller-supplied salt — see `anonymize/config.py`.
