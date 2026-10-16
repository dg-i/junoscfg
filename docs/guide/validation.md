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
    XML validation needs a `junos-validated.xsd` — a **cleaned** XSD — and
    nothing in this package produces one. A raw NETCONF dump does not compile:
    lxml rejects element names such as `openconfig-lldp:lldp`, which are not
    valid `xs:NCName` values, and a real 23.2R2 dump carries 85 of them.
    `junoscfg schema generate` builds the JSON, YAML and set artifacts from
    that dump but not the XSD, so you must supply a cleaned one yourself.
    JSON and YAML validation work out of the box.

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

What the `yaml` reader refuses is an error naming its kind and path: a key that is
not a string (`64496: x`, an unquoted `on: x`), a cycle, or a value nested more than
64 levels deep; values under `_ansible_*` and `_meta_*` keys are not walked, as the
schema admits them unread.

### yaml-new

`yaml-new` is the Junos JSON object in YAML, so it is validated by the JSON
schema: `_ansible_*` and `_meta_*` keys are errors, as they are in JSON. A block
shared through an alias is judged written out; a cycle, or a value nested more
than 64 levels deep ([conversion](conversion.md#two-yaml-formats-yaml-and-yaml-new)),
is an error naming its kind and path (text nested past about 490 levels fails
inside PyYAML's loader first).

```python
from junoscfg import validate_config

result = validate_config(
    "configuration:\n  system:\n    host-name: router1\n", format="yaml-new"
)
```

### Set Commands

!!! warning "Structural only, and it rejects some valid configuration"
    Set validation checks *shape*, not values: every leaf accepts any token.
    Nodes that share a name can share their grammar alternatives, so a line may
    also pass with a child the schema has only at another node of that name:
    `set protocols bgp group RR family inet6 labeled-unicast per-prefix-label`
    validates although the bundled schema has `per-prefix-label` under
    `family inet labeled-unicast`, not under `family inet6 labeled-unicast`.

    It also over-rejects. Of the 8,713 distinct `set` lines four lab devices
    printed for the configurations in `tests/data/device/`, all valid Junos, it
    rejects fewer than one in a hundred; `tests/data/device/grammar-corpus.json`
    records each, and `tests/corpus/test_set_corpus.py` fails when one is fixed
    or a new one appears. The same test lists the malformed input the grammar
    must refuse and the intentional exclusions. `set system location dc-a` is
    malformed, not an over-rejection: `location` takes keyworded children, as
    in the devices' `set system location building "B 2"`.

    Raw set input **intentionally rejects every unquoted `[` or `]`**. It
    accepts canonical device-produced `| display set` syntax, not interactive
    bracket-list shorthand. The rejection happens before conversion builds an
    IR, even with `validate=False` or without `strict=True`; validation returns
    a normal line-specific error instead of throwing. Brackets inside quoted
    values and ignored comments remain ordinary content.

    Migrate a bracket list to the repeated commands Junos itself emits. For
    example, replace `members [ v10 v20 ]` with one `members v10` command and
    one `members v20` command. Structured curly-brace input still accepts
    bracket lists and structured-to-set conversion performs that expansion.

    Flattened hierarchies marked by the schema accept both compact sibling
    runs and repeated paths. For example, one NTP server line may carry
    `version`, `prefer`, and `routing-instance`, while `maximum-prefixes` may
    carry its positional limit followed by `threshold` and `log-interval`.
    Only known keyworded siblings repeat; arbitrary trailing tokens remain
    invalid. Repeating a known keyword is structural syntax and is left for
    Junos to interpret.

    Artifacts ship gzipped and a set generated from your own device's XSD works
    the same way; `--artifacts DIR` and `JUNOSCFG_ARTIFACTS` select one, for
    conversion as well as validation. The committed performance guard checks
    100 compact sibling commands in under five seconds. Conversion to and from
    set format does not use the grammar, but raw set conversion applies the
    same intentional bracket boundary before it constructs the IR.

```python
from junoscfg import validate_set

result = validate_set("set system host-name router1\nset system domain-name example.com")
```

### Structured (Curly-Brace)

Each curly statement is validated as the set line conversion reads it, in the
input's own tokens: a one-line statement such as `hold-time up 2000 down 0;` is
split where each sibling starts, and a leaf read without its value
(`hold-time up 2000 down;`) is an error. The limitations above apply to the
lines. Malformed curly text (an unmatched brace, a statement without `;`) is
invalid, and a block that holds no statement, such as the device's
`{ /* OMITTED */ }` placeholder for `apply-flags omit`, is a warning.

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
from junoscfg.validate import JunosValidator

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
| **Unplaced statements** | A statement the schema cannot place is kept as written and reported as an error, never dropped | `'nonsense alpha' could not be placed in the schema` |

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
A missing schema-mandatory field remains a warning: it may be required at commit,
and the configuration loads without it. For example:

```text
Missing mandatory field 'secret': may be required at commit; the configuration loads without it
```

This warning also appears when no field-validation error exists. Strict mode raises
on errors only; a configuration with warnings alone still converts.

**Unplaced statements.** A statement the bundled schema cannot place, because the device
runs another release or platform, or because the set reader takes one value where the
line carries two, is kept whole in the output and reported as an *error*: printed by
default, fatal under `--strict`. Before 0.9.0 the set reader kept one token of such a
line and dropped the rest without a word. Anonymization replaces each word of such a
statement that a rule knows by its shape alone (an address, a password hash, a sensitive
word), leaves the others as written, and names its schema path in an `anonymize:`
warning; until 0.19.0 it refused the configuration. A set statement the reader cannot complete is kept and reported
the same way: a list entry whose key values run out (`as-path-neighbors as-list`), a
further token after an entry that is nothing but its key, `apply-groups` with two
names or none, or a leaf without its value (`set system host-name`). Such a statement
is kept in its level's record, the reserved key `junoscfg:unplaced` in JSON and YAML
output, as the words it was written with, quotes included:

```json
"system": {
    "host-name": "router1",
    "junoscfg:unplaced": {"host-name": [null]}
}
```

It never replaces or hides a statement placed beside it, and every writer writes it back
as read. JSON or YAML input may carry the record; one whose text is not one line of
words (a line break, an unquoted `;`, `{`, `}`, `[` or `]`) is refused with `ValueError`.
A leaf without its value from JSON or YAML (`"host-name": null`) is reported the same
way. An empty value is checked like any other: `description ""` is valid, as the device
writes it, while `""` on an enum, an integer or a pattern it fails is an invalid value. A
list entry's key fields are the ones the schema declares (`name` for most,
`list-type` and `list-name` for an AS-list reference) and are validated as the leaves
they are; a key field's closed enum is enforced. Not reported: `@` attributes, the
`apply-*` statements, and `enable` or `disable` written for a folded switch.

### Default Behavior

Field-level validation runs automatically during conversion. `convert_config_result()`
and `pipeline_result()` carry findings as diagnostics; library calls write nothing to
stderr, and string-only `convert_config()` discards diagnostics. The CLI prints
findings to stderr without changing configuration output. Warnings do not cause
failure, including under `--strict`:

```text
field-validate: system.syslog.file.facility: Invalid value 'bogus': must be one of [any, kernel, ...]
field-validate: interfaces: 'nonsense alpha beta gamma' under interfaces ge-0/0/0 could not be placed in the schema: kept as written, not validated
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

Use the conversion package door for standalone validation:

```python
from junoscfg.convert import to_dict, validate_ir

# Validate via the convenience function
ir = to_dict('{"configuration":{"system":{"host-name":"router1"}}}', "json")
result = validate_ir(ir)

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

The bundled validation artifacts are generated from a Junos 25.2R2 XSD dump. To validate
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
from junoscfg.validate import ArtifactBuilder

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
from junoscfg.validate import JunosValidator

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
