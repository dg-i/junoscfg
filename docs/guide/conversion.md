# Conversion Guide

Junoscfg converts Junos configurations between five formats:

| Format | Description |
|--------|-------------|
| **Display set** | Flat `set` commands (one per line) |
| **Structured** | Curly-brace hierarchical format |
| **XML** | Junos native XML |
| **JSON** | Junos native JSON |
| **YAML** | Standard YAML (1:1 mapping of Junos JSON) |

## Conversion Matrix

All 20 format pairs are supported (including identity conversions on the diagonal).
All conversions go through the unified `convert_config()` API:

| From \ To | Set | Structured | JSON | YAML |
|-----------|-----|------------|------|------|
| **Set commands** | `convert_config()` | `convert_config()` | `convert_config()` | `convert_config()` |
| **Structured** | `convert_config()` | `convert_config()` | `convert_config()` | `convert_config()` |
| **JSON** | `convert_config()` | `convert_config()` | `convert_config()` | `convert_config()` |
| **YAML** | `convert_config()` | `convert_config()` | `convert_config()` | `convert_config()` |
| **XML** | `convert_config()` | `convert_config()` | `convert_config()` | `convert_config()` |

!!! note
    XML output is not yet supported. All other 20 format pairs (including identity
    conversions) are fully supported through the unified conversion pipeline with
    field-level validation.

## Unified Conversion API

The `convert_config()` function provides a single entry point for all format conversions:

```python
from junoscfg import convert_config, Format

# JSON to set commands
result = convert_config(
    '{"configuration":{"system":{"host-name":"router1"}}}',
    from_format=Format.JSON,
    to_format=Format.SET,
)

# Set commands to JSON
result = convert_config(
    "set system host-name router1",
    from_format=Format.SET,
    to_format=Format.JSON,
)

# YAML to JSON
result = convert_config(yaml_content, from_format=Format.YAML, to_format=Format.JSON)

# XML to set commands
result = convert_config(xml_content, from_format=Format.XML, to_format=Format.SET)

# Structured to set commands
result = convert_config(
    "system {\n    host-name router1;\n}",
    from_format=Format.STRUCTURED,
    to_format=Format.SET,
)

# Set commands to structured
result = convert_config(
    "set system host-name router1",
    from_format=Format.SET,
    to_format=Format.STRUCTURED,
)
```

The `Format` enum has these members: `SET`, `STRUCTURED`, `JSON`, `YAML`, `XML`.

`convert_config()` includes field-level validation by default. Use `validate=False` to
disable it or `strict=True` to make validation errors fatal:

```python
# Disable field validation
result = convert_config(source, from_format=Format.SET, to_format=Format.JSON, validate=False)

# Strict mode: raises FieldValidationError on errors
result = convert_config(source, from_format=Format.SET, to_format=Format.JSON, strict=True)
```

## Identity Conversions

Identity conversions (same format in and out) parse the input and re-render it through the
pipeline. This is useful for normalizing or canonicalizing configuration files and for testing
roundtrip fidelity:

```python
from junoscfg import convert_config, Format

# Normalize JSON formatting
result = convert_config(json_content, from_format=Format.JSON, to_format=Format.JSON)

# Normalize set command ordering
result = convert_config(set_content, from_format=Format.SET, to_format=Format.SET)

# Normalize YAML formatting
result = convert_config(yaml_content, from_format=Format.YAML, to_format=Format.YAML)

# Normalize structured formatting
result = convert_config(struct_content, from_format=Format.STRUCTURED, to_format=Format.STRUCTURED)
```

Identity conversions support field validation (`validate`/`strict`) like all other
conversions. XML→XML is not supported since XML output is not yet implemented.

## Low-Level Pipeline

For advanced use cases, the `junoscfg.convert` module exposes the internal pipeline
functions:

```python
from junoscfg.convert import pipeline, to_dict, from_dict, validate_ir

# Full pipeline (equivalent to convert_config for pipeline-based conversions)
result = pipeline("set system host-name r1", from_format="set", to_format="json")

# Input stage: parse any format into the JSON dict IR
ir = to_dict('{"configuration": {"system": {"host-name": "r1"}}}', "json")

# Output stage: render the IR dict into any format
output = from_dict(ir, "set")

# Standalone field validation on the IR dict
result = validate_ir(ir)
print(result.valid)    # True
print(result.errors)   # []
print(result.warnings) # []
```

The IR (intermediate representation) is a plain Python dict matching the Junos JSON format:
`{"configuration": {"system": {"host-name": "r1"}}}`.

## Path Filtering

Filter output to show only configuration under a specific path:

```python
from junoscfg.display import filter_set_by_path

set_output = """set system host-name router1
set system domain-name example.com
set interfaces ge-0/0/0 unit 0 family inet address 10.0.0.1/30
"""

# Show only system config
filtered = filter_set_by_path(set_output, ["system"])
print(filtered)
# set system host-name router1
# set system domain-name example.com

# Show relative paths (strip prefix)
filtered = filter_set_by_path(set_output, ["system"], relative=True)
print(filtered)
# set host-name router1
# set domain-name example.com
```

Path filtering is also available via the CLI with `--path` and `--relative`:

```bash
junoscfg -i json -e set config.json --path "system.syslog"
junoscfg -i json -e set config.json --path "system.syslog" --relative
```

## Operational Attributes

Junos configurations carry operational attributes — `inactive:`, `replace:`,
`protect:`, and delete operations — encoded in JSON and YAML as `@` annotation
keys. Junoscfg preserves these through conversion and renders them as meta
commands (`deactivate`, `activate`, `protect`, `delete`) in set output and as
statement prefixes (`inactive:`, `replace:`, `protect:`) in structured output:

```python
from junoscfg import convert_config, Format

json_with_attrs = '{"configuration":{"system":{"@":{"operation":"replace"},"host-name":"router1"}}}'
result = convert_config(json_with_attrs, from_format=Format.JSON, to_format=Format.STRUCTURED)
# replace: system host-name router1;
```

See [Operational Attributes (`@` Annotations)](annotations.md) for the full
syntax (container vs. leaf annotations), the supported attribute table,
per-format behavior, and read-only `junos:*` metadata.
