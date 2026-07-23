# Operational Attributes (`@` Annotations)

Junos encodes configuration metadata — operational attributes such as
`inactive`, `replace`, and `protect`, comments, and read-only commit
information — in JSON keys containing the `@` character. Junoscfg understands these annotations
in JSON and YAML input and translates them into the matching meta commands
(`deactivate`, `activate`, `protect`, `delete`) in set output and statement
prefixes (`inactive:`, `replace:`, `protect:`) in structured output.

There are two annotation forms, matching Juniper's JSON encoding.

## Container Annotation: `"@"`

A bare `"@"` key inside an object annotates *the object itself*:

```json
{
  "configuration": {
    "system": {
      "@": {"operation": "replace"},
      "host-name": "router1",
      "location": "dc-a"
    }
  }
}
```

Converted to structured format, the annotation becomes a prefix on the block:

```
replace: system {
    host-name router1;
    location dc-a;
}
```

## Leaf Annotation: `"@leaf-name"`

A leaf (a plain key/value pair) cannot contain an `@` member of its own, so
its metadata lives in a *sibling* key named `@` concatenated with the leaf
name:

```json
{
  "configuration": {
    "system": {
      "host-name": "router1",
      "@host-name": {"inactive": true}
    }
  }
}
```

Converted to set commands:

```
set system host-name router1
deactivate system host-name
```

!!! note "YAML quoting"
    `@` is a reserved indicator character in YAML, so annotation keys must be
    quoted in YAML documents: `'@':` and `'@host-name':`. Junoscfg quotes them
    automatically when emitting YAML.

## Supported Attributes

Junoscfg recognizes the following attributes inside an annotation object
(either form). Documented variant spellings — boolean/string forms and the
YANG (jcmd) encoding — are normalized to these canonical forms when input is
parsed (see
[Encoding Variants](#encoding-variants-and-unrecognized-attributes)).

| Attribute | Meaning | CLI / text equivalent |
|-----------|---------|-----------------------|
| `"inactive": true` | Statement is deactivated but kept in the configuration | `deactivate` command; `inactive:` tag in text format |
| `"active": "active"` | Reactivate a previously deactivated statement | `activate` command |
| `"operation": "replace"` | Replace this hierarchy on load | `load replace`; `replace:` tag in text format |
| `"operation": "delete"` | Delete the statement on load | `delete` command |
| `"protect": "protect"` | Protect the statement from modification | `protect` command; `protect:` tag in text format |
| `"comment": "..."` | Comment attached to the statement — passed through, never interpreted | `annotate` command |

!!! note "`replace` and JSON loads"
    Junos itself does not accept the replace operation when loading JSON
    configuration data — replace semantics exist only for text and XML loads
    ([Juniper: Replace Elements in Configuration Data](https://www.juniper.net/documentation/us/en/software/junos/junos-xml-protocol/topics/task/junos-xml-protocol-configuration-data-elements-replacing.html)).
    `"operation": "replace"` is still useful with junoscfg: convert to
    structured output to obtain a `replace:`-prefixed text configuration for
    `load replace`.

## Availability by Conversion

Which annotations junoscfg *reads* from each input format:

| Attribute | JSON / YAML input | Set input | Structured input |
|-----------|-------------------|-----------|------------------|
| inactive | `"@": {"inactive": true}` | `deactivate <path>` | `inactive:` prefix |
| active | `"@": {"active": "active"}` | `activate <path>` | — (active statements carry no marker) |
| replace | `"@": {"operation": "replace"}` | — (no set command exists) | `replace:` prefix |
| delete | `"@": {"operation": "delete"}` | `delete <path>` | `delete:` prefix (legacy junoscfg output only) |
| protect | `"@": {"protect": "protect"}` | `protect <path>` | `protect:` prefix |
| comment | preserved, not interpreted | `annotate` lines silently dropped | `/* ... */` and `#` comments silently dropped |
| `junos:*` metadata | preserved, not interpreted | — | — |

Which annotations junoscfg *writes* to each output format:

| Attribute | JSON / YAML output | Set output | Structured output |
|-----------|--------------------|------------|-------------------|
| inactive | `"@": {"inactive": true}` | `deactivate <path>` | `inactive:` prefix |
| active | `"@": {"active": "active"}` | `activate <path>` | no marker (active is the default state) |
| replace | preserved | dropped — no set equivalent | `replace:` prefix |
| delete | preserved | `delete <path>` | dropped with a stderr note |
| protect | preserved | `protect <path>` | `protect:` prefix |
| comment, `junos:*`, unrecognized | preserved verbatim | dropped | dropped |

## Worked Example: `replace` Through the Pipeline

Round-trip a `replace` annotation from JSON through YAML to structured format:

```console
$ cat replace-system.json
{
  "configuration": {
    "system": {
      "@": {"operation": "replace"},
      "host-name": "router1",
      "location": "dc-a"
    }
  }
}

$ junoscfg convert -i json -e yaml < replace-system.json | tee replace-system.yaml
configuration:
  system:
    '@':
      operation: replace
    host-name: router1
    location: dc-a

$ junoscfg convert -i yaml -e conf < replace-system.yaml
replace: system {
    host-name router1;
    location dc-a;
}
```

In set output the same annotation is dropped, because display-set syntax has
no replace command:

```console
$ junoscfg convert -i json -e set < replace-system.json
set system host-name router1
set system location dc-a
```

## Inline Meta Commands

In set output, meta commands (`deactivate`, `protect`, `activate`, `delete`)
are emitted inline with their related `set` commands, preserving logical
ordering. For example, when converting a JSON configuration where `system ntp`
is inactive:

```
set system ntp server 10.0.0.1
deactivate system ntp
set system syslog host 10.0.0.2
```

The `deactivate` line appears immediately after the related `set` commands,
not deferred to the end of the output. This makes the output easier to read
and apply in sequence.

## Delete Operations

Use `{"@": {"operation": "delete"}}` on a node to generate `delete` commands
in set output:

```python
from junoscfg import convert_config, Format

json_with_delete = '{"configuration":{"system":{"host-name":{"@":{"operation":"delete"}}}}}'
result = convert_config(json_with_delete, from_format=Format.JSON, to_format=Format.SET)
# delete system host-name
```

!!! note "Structured output"
    The structured (curly-brace) format has no way to express delete
    operations. Delete annotations are dropped from structured output with a
    note on stderr — use set output for delete operations. `delete:` prefixes
    in structured *input* (emitted by junoscfg versions before 0.5.14) are
    still parsed for backward compatibility.

## Comments (`annotate`)

Junos attaches comments to configuration statements with the CLI `annotate`
command. In JSON, a comment appears as a `comment` attribute in the annotation
object:

```json
{
  "configuration": {
    "system": {
      "@": {"comment": "/* managed by ansible */"},
      "host-name": "router1"
    }
  }
}
```

Junoscfg does not interpret comments — it only carries them along where the
format allows:

- **JSON ↔ YAML**: the `comment` attribute passes through verbatim.
- **Set output / structured output**: comments are dropped.
- **Set input**: `annotate` lines are accepted but silently discarded
  (`show configuration | display set` does not emit them either).
- **Structured input**: `/* ... */` and `#` comment lines are accepted but
  silently discarded.

## Read-Only `junos:*` Metadata

Device-emitted JSON (e.g. `show configuration | display json`) can include
read-only metadata annotations alongside the operational attributes:

| Annotation | Meaning |
|------------|---------|
| `junos:commit-seconds` | UNIX timestamp of the last commit that changed the object |
| `junos:commit-localtime` | The same timestamp in human-readable local time |
| `junos:commit-user` | Username that performed the last commit |
| `junos:changed-seconds` / `junos:changed-localtime` | When the object was last modified |
| `junos:key` | Marks which member is the identifier of a list entry, for programmatic tools |

Junoscfg preserves these verbatim in JSON↔YAML conversion and ignores them
when rendering set or structured output. They never cause an error, so device
output can be fed straight into `junoscfg` without stripping metadata first:

```console
$ junoscfg convert -i json -e yaml < device-output.json
configuration:
  system:
    '@':
      inactive: true
      junos:commit-seconds: '1500000000'
      junos:commit-user: admin
    host-name: router1

$ junoscfg convert -i json -e set < device-output.json
deactivate system
set system host-name router1
```

## Encoding Variants and Unrecognized Attributes

Juniper's documentation describes several encodings of the same operations.
Junoscfg normalizes these variants to the canonical spellings when parsing
input, so every output format — including JSON and YAML — emits the canonical
form:

| Variant | Normalized to |
|---------|---------------|
| `"inactive": "inactive"` (string form, mirroring the XML attribute) | `"inactive": true` |
| `"protect": true` / `"protect": false` (boolean forms from current Juniper JSON docs) | `"protect": "protect"` / removed |
| `"active": true` / `"active": false` | `"active": "active"` / `"inactive": true` |
| `"junos-configuration-metadata:active"` (YANG `jcmd` module, boolean) | `"active": "active"` / `"inactive": true` |
| `"junos-configuration-metadata:protect"` (boolean) | `"protect": "protect"` / removed |
| `"junos-configuration-metadata:comment"` | `"comment"` (still uninterpreted) |

Truly unrecognized attributes are preserved verbatim in JSON and YAML output
and silently ignored in set and structured output:

- `"operation": "create"` and `"operation": "merge"` — NETCONF-style load
  operations (only `replace` and `delete` are interpreted)
- `"openconfig-metadata:protobuf-metadata"` — OpenConfig metadata at the
  configuration root
- Read-only `junos:*` metadata and `comment` content (see above)

## References

- [Map Junos OS Configuration Statements to JSON](https://www.juniper.net/documentation/us/en/software/junos/junos-xml-protocol/topics/concept/junos-xml-protocol-configuration-mapping-to-json.html)
  — Juniper's official reference for the `@` annotation encoding, including
  `inactive`, `protect`, and `comment`
- [Create, Modify, or Delete Configuration Elements Using the Junos XML Protocol](https://www.juniper.net/documentation/us/en/software/junos/junos-xml-protocol/topics/task/junos-xml-protocol-configuration-data-elements-creating-changing-deleting.html)
  — includes the `"operation": "delete"` JSON attribute
- [Replace Elements in Configuration Data Using the Junos XML Protocol](https://www.juniper.net/documentation/us/en/software/junos/junos-xml-protocol/topics/task/junos-xml-protocol-configuration-data-elements-replacing.html)
  — documents that JSON loads do not support the replace operation
- [Change a Configuration Element's Activation State Using the Junos XML Protocol](https://www.juniper.net/documentation/us/en/software/junos/junos-xml-protocol/topics/task/junos-xml-protocol-configuration-data-elements-activating-deactivating.html)
  — deactivate/activate semantics
- [Protect or Unprotect a Configuration Object Using the Junos XML Protocol](https://www.juniper.net/documentation/us/en/software/junos/junos-xml-protocol/topics/task/junos-xml-protocol-protecting-unprotecting-configuration.html)
  — protect semantics
- [YANG Metadata Annotations for Junos Devices](https://www.juniper.net/documentation/us/en/software/junos/netconf/topics/topic-map/yang-module-junos-configuration-metadata.html)
  — the `junos-configuration-metadata` (jcmd) encoding variant
- [JSON Support for Junos OS](https://higherlogicdownload.s3.amazonaws.com/JUNIPER/MigratedAttachments/BD2B2715-FA41-4B55-93C4-B6F775D18EE0-2-JSON-Whitepaper.pdf)
  — Juniper whitepaper (2017) with XML/JSON examples of both annotation forms
