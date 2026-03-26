# Getting Started

## Installation

Install with pip:

```bash
pip install junoscfg
```

Or with uv:

```bash
uv add junoscfg
```

## Quick Start: CLI

Convert a structured config file to display set commands:

```bash
junoscfg -i structured -e set config.conf
```

Convert JSON to set commands:

```bash
junoscfg -i json -e set config.json
```

Read from stdin (input format is auto-detected when `-i` is omitted):

```bash
echo '{"configuration":{"system":{"host-name":"test"}}}' | junoscfg -e set
```

### Post-Processing for Ansible

Transform YAML configs for Ansible consumption with `edityaml`:

```bash
junoscfg edityaml ansibilize -p "junos_addr:configuration.interfaces.interface[*].unit[*].family.*.address[*].name" config.yaml
```

See [edityaml](edityaml.md) for full documentation.

### Anonymizing Configurations

Anonymize sensitive data before sharing configurations:

```bash
# Anonymize all sensitive data before sharing
junoscfg -i json -e json --anonymize-all --anonymize-dump-map revert.json config.json > anon.json

# Restore original values from the saved mapping
junoscfg -i json -e json --anonymize-revert-map revert.json anon.json
```

Python API:

```python
from junoscfg.anonymize import anonymize, AnonymizeResult
from junoscfg.anonymize.config import AnonymizeConfig

config = AnonymizeConfig(ips=True, passwords=True, salt="my-salt")
config.expand_all()

ir = {"configuration": {"system": {"host-name": "router1"}}}
result = anonymize(ir, config)
print(result.ir)      # anonymized IR
print(result.mapping)  # revert dictionary
```

See the [CLI Reference anonymization section](guide/cli.md#anonymization) for the full
list of options.

## Quick Start: Python API

### Unified Conversion API

Use `convert_config()` with the `Format` enum for any-to-any conversion:

```python
from junoscfg import convert_config, Format

# JSON to set commands
result = convert_config(
    '{"configuration":{"system":{"host-name":"router1"}}}',
    from_format=Format.JSON,
    to_format=Format.SET,
)
print(result)
# set system host-name router1

# Set commands to structured
result = convert_config(
    "set system host-name router1\nset system domain-name example.com",
    from_format=Format.SET,
    to_format=Format.STRUCTURED,
)
print(result)
# system {
#     host-name router1;
#     domain-name example.com;
# }

# JSON to structured
result = convert_config(
    '{"configuration":{"system":{"host-name":"router1"}}}',
    from_format=Format.JSON,
    to_format=Format.STRUCTURED,
)
print(result)
# system host-name router1;

# Set commands to JSON
result = convert_config(
    "set system host-name router1",
    from_format=Format.SET,
    to_format=Format.JSON,
)
```

`convert_config()` supports all 20 format pairs (including identity conversions) and includes field-level validation
by default (see [Field-Level Validation](guide/validation.md#field-level-validation)).

### Reading from Files

All conversion functions accept either a string or a file-like object:

```python
from junoscfg import convert_config, Format

# From a string
result = convert_config(
    '{"configuration":{"system":{"host-name":"test"}}}',
    from_format=Format.JSON,
    to_format=Format.SET,
)

# From a file
with open("config.json") as f:
    result = convert_config(f, from_format=Format.JSON, to_format=Format.SET)
```

### Validation

```python
from junoscfg import validate_json

result = validate_json('{"configuration":{"system":{"host-name":"router1"}}}')
if result.valid:
    print("Configuration is valid")
else:
    for error in result.errors:
        print(f"Error: {error.message}")
```

### Field-Level Validation

When using `convert_config()`, leaf values are automatically validated against
schema constraints (enums, patterns, IP addresses, integer bounds). Warnings are
printed to stderr by default:

```python
from junoscfg import convert_config, Format

# Strict mode — raises FieldValidationError on invalid values
result = convert_config(
    "set system host-name router1",
    from_format=Format.SET,
    to_format=Format.JSON,
    strict=True,
)
```

See the [Conversion Guide](guide/conversion.md) for detailed examples of every format pair,
and the [Validation Guide](guide/validation.md) for advanced validation and field-level
validation usage.
