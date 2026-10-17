# Conversion Guide

Junoscfg converts Junos configurations between six formats:

| Format | Description |
|--------|-------------|
| **Display set** | Flat `set` commands (one per line) |
| **Structured** | Curly-brace hierarchical format |
| **XML** | Junos native XML |
| **JSON** | Junos native JSON |
| **YAML** (`yaml`) | junoscfg's IR written as YAML; to be renamed `yaml-old` |
| **yaml-new** (`yaml-new`) | Junos native JSON written as YAML; to become `yaml` |

The two YAML formats, and how to move from one to the other, are described in
[Two YAML formats](#two-yaml-formats-yaml-and-yaml-new).

## Raw set command boundary

Set input is what a device exports: the file `show configuration | display set`
writes, `set`, `deactivate` and `protect` lines, one statement a line (the QFX5120
and vMX captures under `tests/data/device/`). Raw set conversion reads `set`,
`deactivate`, `protect`, `delete` and `activate` commands with a path. `delete` and
`activate` record Junos's own `operation` and `active` markers on a statement; they
are not edit commands, and a `delete` never removes an earlier line. Blank lines,
full-line `#` comments and leading `/* ... */` comments are ignored. Words inside
values remain values. The rule and its reasons:
[Set input is what a device exports](../decisions/2026-10-17-set-input-is-a-device-export.md).

Edit commands that need a state machine, and typed CLI forms an export never holds,
are unsupported, each named in an error; conversion refuses all but several statements
on one line, which it reads:

| Construct | Example | Conversion | Validation (`-v`) |
|---|---|---|---|
| An edit command: `insert`, `rename`, `copy`, `annotate`, `unprotect`, `edit`, `replace pattern`, `load`, `commit`, any other word | `insert system syslog file a before file b` | refused: "Unsupported command in set input on line N" | the same error |
| A verb without a path | `deactivate` | refused, as above | the same error |
| A bracket list | `set system name-server [ 192.168.0.1 192.168.0.2 ]` | refused: "Unsupported bracket syntax in set input on line N" | the same error |
| Several statements on one line | `set interfaces ge-0/0/1 hold-time up 0 down 0` | read, as the statements one a line | "Unsupported in set input, one statement a line: <line>" |

A verb line names one statement the device can tag: a container, a list entry after
its whole key, a leaf, leaf-list or flag before its value, or a list the schema marks
`homogeneous` as a whole. The QFX5120 refuses `protect policy-options
policy-statement` (a list's keyword without its entry's name) and `deactivate
routing-options static route 198.51.100.0/24 community 64496:2` (one value of a
leaf-list); conversion refuses such a line with `ValueError` ("Metadata commands
cannot target ..."), and `-v` reports it invalid. A tag on `family` itself, which
the device refuses ("missing argument"), is reported by field validation, invalid
for `-v`, and dropped with a note by set and structured output.

An unsupported command refuses conversion of the entire input with `ValueError` and
its physical line number; CLI conversion exits 2 without partial output. Validation
reports these lines as errors and validation-only CLI exits 1. Command errors
withhold input values. The unquoted-bracket refusal takes precedence. There is no
silent-ignore option: apply an edit script on a device and export the result.

## Conversion Matrix

All 30 format pairs are supported (including identity conversions on the diagonal).
All conversions go through the unified `convert_config()` API:

| From \ To | Set | Structured | JSON | YAML | yaml-new |
|-----------|-----|------------|------|------|----------|
| **Set commands** | `convert_config()` | `convert_config()` | `convert_config()` | `convert_config()` | `convert_config()` |
| **Structured** | `convert_config()` | `convert_config()` | `convert_config()` | `convert_config()` | `convert_config()` |
| **JSON** | `convert_config()` | `convert_config()` | `convert_config()` | `convert_config()` | `convert_config()` |
| **YAML** | `convert_config()` | `convert_config()` | `convert_config()` | `convert_config()` | `convert_config()` |
| **yaml-new** | `convert_config()` | `convert_config()` | `convert_config()` | `convert_config()` | `convert_config()` |
| **XML** | `convert_config()` | `convert_config()` | `convert_config()` | `convert_config()` | `convert_config()` |

!!! note
    XML output is not yet supported. All other 30 format pairs (including identity
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

The `Format` enum has these members: `SET`, `STRUCTURED`, `JSON`, `YAML`, `YAML_NEW`
(`"yaml-new"`), `XML`.

`convert_config()` includes field-level validation by default. Use `validate=False` to
disable it or `strict=True` to make validation errors fatal:

```python
# Disable field validation
result = convert_config(source, from_format=Format.SET, to_format=Format.JSON, validate=False)

# Strict mode: raises FieldValidationError on errors
result = convert_config(source, from_format=Format.SET, to_format=Format.JSON, strict=True)
```

In-process callers that need non-fatal validation messages, anonymization debug
traces, or rendering notes can opt into a structured result. Library calls do
not write these messages to process stderr:

```python
from junoscfg import Format, convert_config_result

result = convert_config_result(source, from_format=Format.SET, to_format=Format.JSON)
for diagnostic in result.diagnostics:
    logger.warning(diagnostic.render())
json_output = result.output
```

The CLI uses this API and remains responsible for rendering diagnostics to its
stderr stream.

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
from junoscfg.convert import pipeline, pipeline_result, to_dict, from_dict, validate_ir

# Full pipeline (equivalent to convert_config for pipeline-based conversions)
result = pipeline("set system host-name r1", from_format="set", to_format="json")

# Full pipeline with structured diagnostics
result = pipeline_result("set system host-name r1", from_format="set", to_format="json")

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
`from_dict()` never changes the IR it is given, so one IR can be rendered to
several formats in turn. The JSON writer applies the device's spellings
(`[null]` presence flags, the native `groups` list) to its own copy.

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

These text filters match the path's words as written, without the schema; use
`convert_config(path=..., relative=...)` or the CLI for output that knows the
schema context. Path filtering is also available via the CLI with `--path` and
`--relative`:

```bash
junoscfg -i json -e set config.json --path "system.syslog"
junoscfg -i json -e set config.json --path "system.syslog" --relative
```

`convert_config(path=..., relative=True)` and `--relative` write what the absolute
output writes at the path, without the path, in every format: JSON, `yaml-new` and
`yaml` write the value there (a single leaf, a flag or an annotation spelled as the
absolute output spells it), set and structured the statements less the words the
path is written as (a list name the schema hides, such as `interface` under
`interfaces`, has none), so a selected list writes its entries' statements and a
selected leaf its value. A path whose value is `null` writes it; only a missing key
writes nothing. A key holding a dot (`ieee-802.1`, `inet.0`) is matched as written,
the exact key first.

An absolute selection (`--path` without `--relative`) keeps the tags of the statement
it ends at and of every statement along its path: `--path system.host-name` of a
deactivated host name writes `set system host-name r1` and `deactivate system
host-name`, and under `deactivate system` it writes `set system host-name r1` and
`deactivate system`, as the device prints a statement inside a deactivated one, in
every format.

A relative selection cannot write a tag at or above its path: no statement is left to
carry it. Every format drops it and says so in one note, "N tag(s) at or above the
selected path dropped: relative output writes what lies below the path"; set output
never writes a bare `deactivate` or `protect`, which a device refuses. A selected
container's own tag stays in the value JSON, `yaml-new` and `yaml` write; a comment there
is dropped with a note of its own. Set and structured output write no comment in any
selection. Set and
structured output also note a tag on one value of a leaf-list, which set and structured
text have no form for: "N tag(s) on single values of a leaf-list dropped"; JSON and YAML keep it.

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

## Two YAML formats: `yaml` and `yaml-new`

`yaml` writes junoscfg's IR as YAML and reads YAML with two conveniences: it drops
`_ansible_*` and `_meta_*` keys, and it turns a single value of a leaf-list into a
one-element list. Its output is not quite the device's JSON: it can keep `groups`
in a `group` wrapper, presence flags as `true` or `{}`, and one-element lists for
single leaves.

`yaml-new` is exactly the object `-e json` writes, spelled in YAML, and it reads
YAML exactly as JSON input is read. A file means the same configuration whether
it is written in JSON or in `yaml-new`, and both validate against the JSON schema:

- presence flags and empty containers are `[null]` (a `- null` list), single
  leaves are scalars, `groups` is the list of groups, and a `junoscfg:unplaced`
  record is written as JSON writes it (a `--path --relative` selection is
  written exactly as JSON writes it too);
- `_ansible_*` and `_meta_*` keys are kept, as JSON keeps them, so field and
  schema validation report them;
- a scalar given for a leaf-list stays a scalar, as in JSON;
- a value JSON cannot hold is refused with its path: an unquoted date or time
  (`2026-10-15`), a key that is not a string (`1: x`, `on: x`), binary data, a
  set, an ordered map. Quote such a value (`'2026-10-15'`);
- a block shared through an anchor and an alias (`contents: &c ...`, then
  `contents: *c`) is read as if written out at each place, as JSON would hold
  it, however often and wherever it is reused. A block that contains itself is
  refused as a `cycle`, and a value nested more than 64 levels below the
  document's root (no Junos configuration comes near it) is refused with its
  path. An alias of a single value is read as that value. junoscfg treats
  configuration input as trusted, in every format
  ([decision record](../decisions/2026-10-15-configuration-input-is-trusted.md)): a file of nested aliases ("billion laughs") is
  expanded at the cost of time and memory, and text nested past about 490
  levels fails inside PyYAML's own loader, so bound untrusted YAML before
  handing it to junoscfg.

YAML is read with PyYAML's YAML 1.1 rules, as for `yaml`: unquoted `on`, `off`,
`yes` and `no` are booleans, `010` is the number 8 and `1:30` the number 90.
Quote such words in hand-written files (`location: 'on'`); junoscfg's own output
quotes them. `.inf` and `.nan` are read as JSON input reads `Infinity` and `NaN`.

YAML that is detected rather than named with `-i` is read as `yaml`. The `yaml`
reader refuses a cycle, a value nested more than 64 levels deep and a key that is
not a string (`64496: x`, an unquoted `on: x`) the same way, with the same message
(its IR is the JSON dictionary, hence "has no JSON spelling"), except inside the
`_ansible_*` and `_meta_*` keys it drops unread; quote such a key (`'64496': x`), as
junoscfg's own `yaml` output does. `-v -i yaml` reports them as errors.

JSON and XML input nested more than 64 levels deep are refused with their path in
the same way ("a JSON value at ... is nested deeper than 64 levels"; a repeated XML
element counts as a list and its entry); no Junos configuration nests deeper than
about 26 levels.

### Moving a YAML file to yaml-new

Convert it once; the conveniences of the `yaml` reader are applied on the way:

```bash
junoscfg convert -i yaml -e yaml-new old.yaml > new.yaml
```

```python
from junoscfg import Format, convert_config

new_text = convert_config(old_text, from_format=Format.YAML, to_format=Format.YAML_NEW)
```

The result reads as `yaml-new` to the same configuration the old file read as
`yaml`. A value JSON cannot hold, such as an unquoted date, stops the migration
with its path; quote it in the old file and convert again. Remove `_ansible_*` and `_meta_*` keys that your own tooling adds before
feeding a file to `yaml-new`.

### Planned rename

`yaml-new` will be renamed `yaml`, and today's `yaml` will become `yaml-old`, in a
later release, once `yaml-new` has been tested in use and its users have had time
to migrate ([decision record](../decisions/2026-10-15-yaml-new-before-renaming-yaml.md)).
That release declares the change of meaning of `yaml` and raises the minor
version. Following the beta deprecation policy, `yaml-new` then stays accepted as
a deprecated alias, and `yaml-old` is deprecated before it is removed, each for at
least one minor release. Nothing is deprecated yet.
