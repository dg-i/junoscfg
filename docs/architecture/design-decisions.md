# Design Decisions

Key architectural and design decisions made during the Python reimplementation of Junoscfg.

## Principles

### Library-First Design

All logic that is not a reasonable CLI-only feature (such as displaying help or
argument parsing) must be implemented in the library and the CLI must call into
it. The CLI is a thin wrapper around the public API — it should never contain
business logic that downstream consumers (e.g. an Ansible collection) would need
to duplicate.

Examples:
- **Path filtering** (`--path`, `--relative`) is implemented in `convert_config()`
  with `path` and `relative` parameters, not in the CLI.
- **Format conversion** is handled by `convert_config()`, not by CLI-specific code.
- **Validation** is exposed via `validate_*()` functions in the public API.
- **Validation dispatch** (`validate_config()`) handles format-based routing in the
  library, so the CLI's `_run_validation()` is a thin wrapper for output formatting
  and exit codes.

## Python vs Ruby Patterns

### Input Handling

- **Ruby**: `io_or_string.respond_to?(:read)` duck typing
- **Python**: `str | TextIO` type hints with `hasattr(io_or_string, 'read')` check

All public conversion functions accept either a string or a file-like object (`TextIO`).

### Class vs Module Design

- **Ruby**: Classes in nested modules (`Junoser::Display::JsonToSet`)
- **Python**: Classes in flat packages (`junoscfg.display.json_to_set.JsonToSet`)

Follows standard Python package conventions with one class per module.

### Boolean Checking

In Python, `bool` is a subclass of `int`. Code that checks for integers must
test `isinstance(v, bool)` before `isinstance(v, int)` to avoid treating `True`/`False`
as numeric values.

## Set-to-Structured Conversion: Schema-Driven Approach

### Why Not a Trie

The original approach used a prefix trie built from all set command tokens. This
heuristic could not distinguish:

- **Named list containers** (e.g., `policy-statement NAME { ... }`) from regular containers
- **Context-dependent keywords** (e.g., `community` is a named list under `policy-options`
  but a leaf under `from`)

### Why Not a Grammar

A Lark grammar was considered, but the flat rule namespace cannot handle the 160+ element
names that have conflicting `is_list` status at different tree depths (e.g., `filter` is
a named list under `firewall family inet` but a regular container elsewhere).

### Schema Tree Walk

The current approach walks the token sequence against the schema hierarchy
(`junos-structure-tree.json`), maintaining path context at each step. This gives perfect
context-aware hierarchy inference.

The schema tree is generated from the Junos XSD via the artifact pipeline. When the
schema is unavailable or a token path doesn't match (vendor extensions, `apply-macro`
content), the trie-based heuristic is used as a fallback.

## JSON/XML to Structured (via Set Intermediate)

Both `JsonToSet.to_structured()` and `XmlToSet.to_structured()` use a direct path
through `_WalkOutput` in structured mode, which pushes hierarchy paths into `ConfigStore`.
This preserves operational attributes (`replace:`, `protect:`, `inactive:`) that would
be lost in the set-command intermediate format.

Only `inactive:` survives the set-command roundtrip (via `deactivate`); `replace:` and
`protect:` require the direct path.

## Dependencies

### Runtime

| Package | Rationale |
|---------|-----------|
| **click** | Cleaner API than argparse, better help formatting, industry standard |
| **lxml** | Faster than `xml.etree`, better namespace handling, XSD validation support |
| **pyyaml** | Standard YAML parsing |
| **jsonschema** | JSON Schema validation for JSON/YAML config validation |
| **lark** | LALR parser for set command validation, better performance than PEG |

### Development

| Package | Rationale |
|---------|-----------|
| **ruff** | Single fast tool replaces flake8 + black + isort |
| **mypy** | Strict mode type checking catches real bugs |
| **pytest** | More pythonic than unittest, better fixtures and output |

## Value Quoting

Both JSON and XML converters need to quote values containing special characters.
Policy expressions (containing `&&`, `||`, `!`) are never quoted despite containing
spaces. Shared quoting logic lives in `value_format.py`.

## Anonymization Design

### Schema-Guided Walker

Anonymization walks the schema tree in parallel with the IR dict, the same approach
used by the field validator. This is necessary because the same element name can have
different semantics at different tree depths (e.g., `name` under `interface` is an
interface name, but `name` under `user` is a username). A brute-force string replacement
approach would not be able to distinguish these cases and would either miss sensitive
data or incorrectly anonymize structural identifiers.

### Rule Priority System

Rules are ordered by priority, and only the first matching rule processes each leaf
value. This prevents double-anonymization — if a password rule matches a value, the
sensitive-word rule does not also replace it. The priority order is chosen so that
rules with the most specific schema-based matching criteria run first.

### Multi-Pass Architecture

The primary schema-guided walk handles leaves that are reachable through the schema
tree. However, some values are embedded inside larger strings (e.g., an IP address
inside an SSH known-hosts entry like `"server.example.com,10.1.2.3"`), and some
values live in schema-empty nodes like `apply-groups`. These require separate
passes that operate on the primary rule's replacement maps, which is why
IPs-in-strings and AS-in-strings run after the main walk.

### Separate `--anonymize-sensitive-patterns` Option

Sensitive patterns (regex) are a separate CLI option from sensitive words (literal
strings) for three reasons: (1) no ambiguity about whether a value is a regex or a
literal, (2) backward compatible with the existing `--anonymize-sensitive-words` flag
that uses comma-separated values, and (3) regex patterns can contain commas, which
would conflict with the comma-separated word list format. Patterns use Click's
`multiple=True` so each `--anonymize-sensitive-patterns` flag adds one regex.

### ipanon Dependency

IP anonymization uses the `ipanon` library rather than a custom implementation because
IP anonymization has subtle correctness requirements: it must be prefix-preserving
(IPs in the same subnet must map to IPs in the same anonymized subnet), deterministic
with a salt, and correctly handle both IPv4 and IPv6 addresses with CIDR notation.
The `ipanon` library handles all of these cases including edge cases around subnet
boundaries and reserved ranges.
