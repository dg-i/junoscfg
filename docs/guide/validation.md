# Validation Guide

Junoscfg validates Junos configurations against the Junos XSD schema. Validation is available
for all five supported formats.

## Quick Start

```python
from junoscfg import validate_json

result = validate_json('{"configuration":{"system":{"host-name":"router1"}}}')
print(result.valid)    # True
print(result.errors)   # ()
```

## Validating Each Format

### XML

!!! warning "Requires custom artifacts"
    XML validation needs a `junos-validated.xsd` file that is **not bundled** with the
    package. You must obtain a NETCONF XSD dump from a Juniper device and generate
    artifacts with `junoscfg schema generate`. See [Custom Artifacts](#custom-artifacts)
    below. JSON, YAML, set, and structured validation work out of the box.

```python
from junoscfg import validate_xml

# Requires junos-validated.xsd in your artifacts directory
result = validate_xml(
    '<configuration><system><host-name>r1</host-name></system></configuration>',
    artifacts_dir="./my-artifacts/",
)
```

### JSON

```python
from junoscfg import validate_json

result = validate_json('{"configuration":{"system":{"host-name":"router1"}}}')
```

### YAML

```python
from junoscfg import validate_yaml

result = validate_yaml("configuration:\n  system:\n    host-name: router1\n")
```

### Set Commands

```python
from junoscfg import validate_set

result = validate_set("set system host-name router1\nset system domain-name example.com")
```

### Structured (Curly-Brace)

```python
from junoscfg import validate_structured

result = validate_structured("system {\n    host-name router1;\n}")
```

## Working with Results

All validation functions return a `ValidationResult`:

```python
from junoscfg import validate_json

result = validate_json('{"configuration":{"invalid-section":{}}}')

if not result.valid:
    for error in result.errors:
        print(f"Error: {error.message}")
        if error.line:
            print(f"  Line: {error.line}")
        if error.path:
            print(f"  Path: {error.path}")

    for warning in result.warnings:
        print(f"Warning: {warning.message}")
```

### ValidationResult

- `valid` (`bool`) — `True` if the configuration passed validation.
- `errors` (`tuple[ValidationError, ...]`) — Validation errors found.
- `warnings` (`tuple[ValidationError, ...]`) — Non-fatal warnings.

### ValidationError

- `message` (`str`) — Human-readable error description.
- `line` (`int | None`) — Line number where the error was found.
- `path` (`str | None`) — Configuration path where the error was found.

## Using JunosValidator Directly

For repeated validation, use `JunosValidator` to avoid reloading artifacts:

```python
from junoscfg.validate.validator import JunosValidator

validator = JunosValidator()

# Validate multiple configs with the same validator instance
for config_file in config_files:
    with open(config_file) as f:
        result = validator.validate_json(f.read())
        print(f"{config_file}: {'OK' if result.valid else 'FAILED'}")

# Inspect loaded artifact info
print(f"Schema version: {validator.schema_version}")
print(f"Generated at: {validator.generated_at}")
```

## Field-Level Validation

In addition to schema validation (which checks structural correctness), Junoscfg supports
field-level validation that checks individual leaf values against schema constraints.

### What It Checks

| Check | Description | Example |
|-------|-------------|---------|
| **Enums** | Value must be one of the allowed keywords | `syslog facility` must be `any`, `kernel`, etc. |
| **Union types** | Enum fields that also accept numeric values or ranges | `destination-port` accepts `ssh` or `179` or `33434-33464` |
| **Patterns** | Value must match (or not match) a regex | Hostnames must match `^[[:alnum:]._-]+$` |
| **IP addresses** | Value must be a valid IPv4 or IPv6 address or prefix (dual-stack) | `10.0.0.1`, `3ffe:0b00:0001:f003::1` |
| **Integer bounds** | Value must be within the type's range | `uint16` must be 0–65535 |
| **Booleans** | Value must be `true` or `false` | |
| **List elements** | Each element in a list is validated individually | `ciphers: ["aes128-ctr", "aes256-ctr"]` |
| **Mandatory fields** | Required fields must be present (skipped for flat-dict children) | Reported as warnings |

### Validation Details

**Dual-stack IP addresses.** Fields with `ipaddr` or `ipprefix` types accept both IPv4 and
IPv6 values. For example, `protocols bgp local-address` accepts both `10.0.0.1` and
`3ffe:0b00:0001:f003::1`.

**XSD union types.** Many Junos fields use XSD union types that combine an enum with a
numeric type. The schema artifact only captures the enum portion, so the field validator
accepts numeric values and ranges (e.g., `179`, `33434-33464`) as a fallback when the
enum check fails. This applies to fields like `destination-port` (accepts both `ssh` and
`179`) and `vlan-id` (accepts both `none` and `7`).

**List element validation.** When a field contains a list of values (e.g.,
`ciphers: ["aes128-ctr", "aes256-ctr"]`), each element is validated individually rather
than validating the stringified list as a whole.

**Mandatory field checks.** Mandatory field warnings are suppressed for children of
flat-dict elements, since these children are functionally optional in the configuration.

### Default Behavior

Field-level validation runs automatically during conversion via `convert_config()` and the
CLI. Warnings are printed to stderr but do not cause failure:

```
field-validate: system.syslog.file.facility: Invalid value 'bogus': must be one of [any, kernel, ...]
```

### Strict Mode

Use strict mode to make field validation errors fatal:

=== "CLI"

    ```bash
    junoscfg -i json -e set --strict config.json
    ```

=== "Python"

    ```python
    from junoscfg import convert_config, Format

    try:
        result = convert_config(source, from_format=Format.JSON, to_format=Format.SET, strict=True)
    except Exception as e:
        # FieldValidationError with .result containing all errors
        print(e)
    ```

### Disabling Field Validation

Skip field-level validation entirely:

=== "CLI"

    ```bash
    junoscfg -i json -e set --no-field-validate config.json
    ```

=== "Python"

    ```python
    result = convert_config(source, from_format=Format.JSON, to_format=Format.SET, validate=False)
    ```

### Python API

Use `FieldValidator` directly for standalone validation:

```python
from junoscfg.convert import validate_ir, to_dict
from junoscfg.convert.field_validator import FieldValidator, FieldValidationResult

# Validate via the convenience function
ir = to_dict('{"configuration":{"system":{"host-name":"router1"}}}', "json")
result = validate_ir(ir)

# Or use FieldValidator directly
validator = FieldValidator()
result = validator.validate(ir)

if not result.valid:
    for error in result.errors:
        print(f"{error.path}: {error.message}")
for warning in result.warnings:
    print(f"{warning.path}: {warning.message}")
```

The `FieldValidationResult` has:

- `valid` (`bool`) — `True` if no errors were found
- `errors` (`list[FieldError]`) — Validation errors
- `warnings` (`list[FieldError]`) — Non-fatal warnings (e.g., missing mandatory fields)

Each `FieldError` has `path`, `message`, `value`, and `expected` fields.

## Custom Artifacts

The bundled validation artifacts are generated from the Junos 21.4R0 XSD. To validate
against a different Junos version, generate artifacts from your device's XSD dump.

### Obtaining the NETCONF XSD Dump

The schema artifacts are generated from a Junos device's NETCONF XSD dump. To obtain it,
run this NETCONF RPC via SSH to your Juniper router or switch:

```bash
echo '<rpc> <get-xnm-information> <type>xml-schema</type>
  <namespace>junos-configuration</namespace>
  </get-xnm-information> </rpc>' | \
  ssh -Csp 830 router.example.com netconf > netconf.xml
```

### Generating Artifacts

From the CLI:

```bash
# Generate artifacts from the NETCONF XSD dump
junoscfg schema generate netconf.xml -o ./my-artifacts/
```

From Python:

```python
from junoscfg.validate.artifact_builder import ArtifactBuilder

builder = ArtifactBuilder()
artifacts = builder.build("output.xml", "./my-artifacts/")
```

### Using Custom Artifacts

Pass the artifacts directory explicitly:

```python
from junoscfg import validate_json

result = validate_json(config, artifacts_dir="./my-artifacts/")
```

Or use `JunosValidator`:

```python
from junoscfg.validate.validator import JunosValidator

validator = JunosValidator(artifacts_dir="./my-artifacts/")
result = validator.validate_json(config)
```

### JUNOSCFG_ARTIFACTS Environment Variable

Set the `JUNOSCFG_ARTIFACTS` environment variable to use custom artifacts by default:

```bash
export JUNOSCFG_ARTIFACTS=./my-artifacts/
```

Artifact resolution order:

1. Explicit `artifacts_dir` argument
2. `JUNOSCFG_ARTIFACTS` environment variable
3. Bundled default artifacts

### Schema Info

Inspect artifact metadata:

```bash
junoscfg schema info
junoscfg schema info --artifacts ./my-artifacts/
```
