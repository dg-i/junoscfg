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

Junos configurations can include operational attributes like `inactive:`, `replace:`, and `protect:`.

### Inactive Elements

Inactive elements are preserved through conversion:

- **JSON/XML to set**: Emits `deactivate` commands
- **Set to structured**: Adds `inactive:` prefix

### Replace and Protect

The `replace:` and `protect:` attributes are preserved through the JSON→structured
conversion path. The pipeline handles these via `DictWalker._read_attrs()` →
`StructuredWalkOutput.emit_replace()` → `ConfigStore.mark_replaced()`.

```python
from junoscfg import convert_config, Format

# Pipeline preserves replace: and protect: attributes
json_with_attrs = '{"configuration":{"system":{"@":{"replace":"replace"},"host-name":"router1"}}}'
result = convert_config(json_with_attrs, from_format=Format.JSON, to_format=Format.STRUCTURED)
```

## Inline Meta Commands

Meta commands (`deactivate`, `protect`, `activate`, `delete`) are emitted inline with
their related `set` commands, preserving logical ordering. For example, when converting
a JSON configuration where `system ntp` is inactive:

```
set system ntp server 10.0.0.1
deactivate system ntp
set system syslog host 10.0.0.2
```

The `deactivate` line appears immediately after the related `set` commands, not deferred
to the end of the output. This makes the output easier to read and apply in sequence.

## Delete Operations

The conversion pipeline supports `delete` operations via the Junos JSON `@` attribute.
Use the `{"@": {"operation": "delete"}}` format to generate `delete` commands in set output:

```python
from junoscfg import convert_config, Format

json_with_delete = '{"configuration":{"system":{"host-name":{"@":{"operation":"delete"}}}}}'
result = convert_config(json_with_delete, from_format=Format.JSON, to_format=Format.SET)
# delete system host-name
```
