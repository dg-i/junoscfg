# CLAUDE.md

Instructions for AI assistants (and human contributors) working on this project.

## Project Overview

Python toolkit for converting, validating, and anonymizing Junos configurations between XML, JSON, structured, YAML, and display set formats. Originally inspired by the [Ruby Junoser gem](https://github.com/codeout/junoser).

## Development Commands

```bash
# Run tests (fast, for normal development)
uv run pytest tests/ -q -k 'not ExampleValidation and not ExampleRoundtrip'

# Full pre-commit validation — regenerates schema artifacts from XSD
# Use after modifying xsd_fixes.py, artifact_builder.py, or before final commit
uv run pytest tests/ -q -k 'not ExampleValidation and not ExampleRoundtrip' --regen-schema

# Run ALL tests including slow example validation
uv run pytest tests/ -q --regen-schema

# Lint
uv run ruff check src/ tests/

# Format
uv run ruff format src/ tests/
```

### Testing workflow

1. **During development**: Run fast tests without `--regen-schema`
2. **Before committing**: Run with `--regen-schema` to ensure XSD fixes are reflected in bundled artifacts
3. **After XSD/schema changes**: Always use `--regen-schema` to regenerate `junos-structure-tree.json`

### Private test data

Real-world router configurations for integration testing go in `private_test_data/`. All files there (except the README) are gitignored. These are not part of the public repository.

## Version Management

Every commit **must** include a version bump. Version is defined in three places that must all be updated together:

1. `pyproject.toml` — `version = "x.y.z"`
2. `src/junoscfg/__init__.py` — `__version__ = "x.y.z"`
3. `tests/test_cli.py` — version string assertion

Rules:

- Use **patch** bumps (e.g. 0.4.0 -> 0.4.1) for all changes including new features
- Include the version bump in the same commit as the code changes
- After committing, create a git tag: `git tag v{version}`

## Documentation Checklist

Before committing, verify that code changes are reflected in documentation:

1. **CLI options**: Every `@click.option` in `cli.py` must have a matching row in `docs/guide/cli.md`
2. **Public API**: Every member of `__all__` in `__init__.py` must appear in `docs/api/conversion.md`
3. **Code examples**: Python snippets in docs must use real function names from `__all__` — verify imports match actual exports
4. **File paths**: Any `src/junoscfg/...` path in `docs/architecture/` must point to an actual file
5. **mkdocs nav**: Every `.md` file in `docs/` must appear in `mkdocs.yml` `nav:` section
6. **XSD fix counts**: When adding/removing XSD fixes, update count tables in `docs/architecture/developer-guide.md` and `docs/architecture/schema-internals.md`
7. **README.md**: Must mention all major features and use only real imports in examples
8. **Ruby gem references**: Lines mentioning `[Ruby Junoser gem]` or `github.com/codeout/junoser)` refer to the upstream Ruby project — do not rename these

## Project Structure

```
src/junoscfg/
  cli.py              # CLI (convert, edityaml, schema)
  input.py            # Input parsing/normalization
  edityaml/           # Post-process YAML (addvars + ansibilize)
    __init__.py       # Public API: apply_rules(data, ruleset)
    path_walker.py    # resolve_path(), resolve_path_with_context()
    transforms.py     # Transform implementations (6 types)
    rules.py          # Rule file loader and inline --set parser
    ansibilize.py     # ansibilize() — split YAML into host_vars + Jinja2 group_vars
  convert/            # Unified conversion pipeline (any format -> IR -> any format)
    __init__.py       # pipeline(), to_dict(), from_dict(), validate_ir()
    ir.py             # IR utilities (find_configuration, wrap_configuration)
    input/            # Format -> dict IR parsers
    output/           # Dict IR -> format renderers
    field_validator.py  # Field-level value validation
  display/            # Shared conversion utilities
    __init__.py       # is_display_set(), filter_set_by_path()
    constants.py      # Schema flag helpers, XML-compat constants, key aliases
    to_yaml.py        # xml_to_yaml(), filter_yaml_by_path()
    set_converter.py  # Structured -> set commands
    value_format.py   # Value formatting (quoting, escaping)
    config_store.py   # Configuration tree storage and rendering
    xml_helpers.py    # XML element utilities
  anonymize/          # Configuration anonymization
    __init__.py       # Public API: anonymize(ir, config) -> AnonymizeResult
    config.py         # AnonymizeConfig — rule selection and settings
    walker.py         # IR tree walker
    revert.py         # Revert anonymization using saved mapping
    path_filter.py    # Include/exclude path glob matching
    rules/            # Per-category anonymization rules
  validate/           # Schema pipeline (XSD -> artifacts)
    xsd_extractor.py  # Extract XSD from NETCONF dump
    xsd_parser.py     # Parse XSD into SchemaNode tree
    xsd_fixes.py      # Structural corrections (Groups A-H)
    schema_node.py    # SchemaNode tree data structure
    artifact_builder.py   # Serialize schema tree to JSON artifacts
    schema_generator.py   # Generate JSON Schema for validation
    grammar_generator.py  # Generate Lark grammar for set commands
    validator.py      # Main validation orchestrator
    data/             # Bundled schema artifacts (runtime)
```

## Architecture

### Schema Pipeline (build time)

```
NETCONF XSD dump
  -> xsd_extractor.py (extract XSD text)
  -> xsd_parser.py (parse into SchemaNode tree)
  -> xsd_fixes.py (apply structural corrections, Groups A-H)
  -> artifact_builder.py (serialize to JSON artifacts)
  -> data/ (bundled schema artifacts)
```

XSD fixes are Python code (not stored in artifacts), so they persist across any XSD regeneration.

### Conversion Pipeline (runtime)

```
Any input format (JSON, XML, YAML, set, structured)
  -> convert/input/ (parse to dict IR)
  -> optional field validation
  -> convert/output/ (render to target format)
```

The pipeline uses the DictWalker + WalkOutput strategy pattern for set and structured output. XML input uses a bridge: xml_to_yaml() -> yaml_to_dict().

Operational attributes (`replace:`, `protect:`, `inactive:`) are preserved through the JSON->structured path via DictWalker._read_attrs() -> StructuredWalkOutput.emit_replace() -> ConfigStore.mark_replaced().

### edityaml Pipeline

```
addvars:      YAML -> resolve_path() -> apply_transform() -> enriched YAML
ansibilize:   YAML -> resolve_path_with_context() -> extract leaf -> (host_vars, group_vars)
ansibilize -P: YAML -> detect value type -> offset expressions -> (host_vars, offset_vars, group_vars)
```

### Where Fixes Go

| Symptom | Fix location |
|---------|-------------|
| Element renders as block instead of oneliner | `xsd_fixes.py` — add `oneliner` flag |
| Wrong nesting depth or structure | `xsd_fixes.py` — fix structure/combinator |
| Transparent container not recognized | `xsd_fixes.py` — add `transparent:{child}` flag |
| Flat entry emits keys instead of values | `xsd_fixes.py` — add `flat-entry:{k}:{p}` flag |
| Positional key not recognized | `xsd_fixes.py` — add `positional-key` flag |
| JSON input uses original XML name | `constants.py` — add to `KEY_ALIASES` |
| XML/YAML converter needs constant | `constants.py` — add to XML-compat section |

For detailed diagnosis and fix methodology, see `docs/architecture/conversion-bugfix-guide.md`.

## Test Data Conventions

All test data uses generic, non-identifying values. Never use real operator data in tests.

| Category | Standard values | Notes |
|----------|----------------|-------|
| AS numbers | 64496-64511 | RFC 5398 documentation range |
| IPv4 (to anonymize) | 203.0.114.x, 198.0.2.x | Public routable, outside documentation ranges |
| IPv4 (preserved) | 10.x, 192.168.x, 198.51.100.x | RFC 1918 / RFC 5737 |
| IPv6 (to anonymize) | `3ffe:0b00:*` | Old 6bone (RFC 3701), always anonymized |
| Passwords | `$9$ExAmPlEhAsH.KEY` | Synthetic $9$ format |
| Usernames | admin, operator, user1 | Generic |
| Hostnames | router1, switch1, r1, sw1 | Generic |

## Key Dependencies

- **netutils** — Juniper `$9$` encoding constants for the password anonymizer
- **ipanon** — IP address anonymization with prefix-preserving mapping
- **lark** — Grammar-based parser for set command validation
- **lxml** — XML parsing and XSD extraction
