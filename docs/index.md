# Junoscfg

Convert and validate Junos configurations between JSON, structured, YAML, and display set formats.

Junoscfg is a Python toolkit for working with Junos configuration formats, originally inspired by the [Ruby Junoser gem](https://github.com/codeout/junoser).
It provides both a CLI tool and a Python library for converting, validating, and anonymizing Junos configurations.

## Features

- **Format conversion** — Convert between display set, structured (curly-brace), XML, JSON, and YAML formats (20 format pairs, including identity conversions)
- **Unified conversion API** — `convert_config()` with `Format` enum for any-to-any conversion
- **Validation** — Validate configurations against the Junos XSD schema in any supported format
- **Field-level validation** — Check leaf values against schema constraints (enums, patterns, IP addresses, integer bounds, mandatory fields)
- **Path filtering** — Extract specific configuration sections by path
- **Custom schemas** — Generate validation artifacts from your own Junos device's XSD dump
- **Anonymization** — Replace sensitive data (IPs, passwords, hostnames, communities, SSH keys) with deterministic pseudonyms; supports regex patterns and revert dictionaries

## Quick Example

```python
from junoscfg import convert_config, Format, validate_json

# Convert JSON config to set commands
json_config = '{"configuration":{"system":{"host-name":"router1"}}}'
result = convert_config(json_config, from_format=Format.JSON, to_format=Format.SET)
print(result)
# set system host-name router1

# Convert set commands to structured format
result = convert_config(
    "set system host-name router1",
    from_format=Format.SET,
    to_format=Format.STRUCTURED,
)

# Validate a JSON config
result = validate_json(json_config)
print(result.valid)  # True
```

## Getting Started

See the [Getting Started](getting-started.md) guide for installation and usage examples.

## Documentation

- [Getting Started](getting-started.md) — Installation and first steps
- **User Guide**
    - [Conversion](guide/conversion.md) — Format conversion with examples
    - [Validation](guide/validation.md) — Configuration validation
    - [CLI Reference](guide/cli.md) — Command-line interface (including anonymization)
    - [edityaml](edityaml.md) — Transform YAML for Ansible (addvars + ansibilize)
- [API Reference](api/index.md) — Python API documentation
- **Architecture**
    - [Developer Guide](architecture/developer-guide.md) — Comprehensive architecture overview
    - [Design Decisions](architecture/design-decisions.md) — Why things are built the way they are
    - [Schema Internals](architecture/schema-internals.md) — XSD schema pipeline details
    - [Conversion Bugfix Guide](architecture/conversion-bugfix-guide.md) — Diagnosing conversion issues
