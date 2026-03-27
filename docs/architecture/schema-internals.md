# Schema Internals

This document describes the XSD schema pipeline that powers both format conversion
and configuration validation.

## XSD Source

The Junos XSD schema is embedded in a NETCONF `get-xnm-information` dump (typically
named `output.xml`). This is a 3.3M-line file containing the full schema for a
specific Junos platform and version.

The schema starts at the `<xsd:schema>` element inside `<rpc-reply>` and ends at
`</xsd:schema>`. The `xsd_extractor` module efficiently scans the file line-by-line
to extract just the schema portion.

### Schema Statistics

| Metric | Count |
|--------|-------|
| `xsd:element` tags | 136,868 |
| `xsd:complexType` tags | 47,113 |
| `xsd:enumeration` values | 80,254 |
| `<match>` regex patterns | 2,883 |
| `<flag>` appinfo elements | 148,494 |
| `<identifier/>` key markers | 3,140 |
| Named complexTypes (top-level) | ~919 |

## Key XSD Patterns

### 1. Top-Level Configuration Element

```xml
<xsd:element name="configuration">
  <xsd:complexType>
    <xsd:sequence>
      <xsd:choice minOccurs="0" maxOccurs="unbounded">
        <xsd:element name="system" type="juniper-system" minOccurs="0"/>
        <xsd:element name="interfaces" type="juniper-interfaces" minOccurs="0"/>
        <xsd:element name="protocols" type="juniper-protocols" minOccurs="0"/>
      </xsd:choice>
    </xsd:sequence>
  </xsd:complexType>
</xsd:element>
```

The dominant Junos pattern is `<xsd:choice minOccurs="0" maxOccurs="unbounded">`,
meaning "any combination of these child elements, in any order, repeated any
number of times." This maps to a JSON object with all-optional properties.

### 2. Keyed Lists (Named Entries)

```xml
<xsd:element name="interface" maxOccurs="unbounded">
  <xsd:complexType>
    <xsd:sequence>
      <xsd:element name="name">
        <xsd:annotation>
          <xsd:appinfo>
            <flag>identifier</flag>
            <flag>nokeyword</flag>
            <identifier/>
          </xsd:appinfo>
        </xsd:annotation>
      </xsd:element>
      <!-- child elements follow -->
    </xsd:sequence>
  </xsd:complexType>
</xsd:element>
```

Identifying marks:

- Parent has `maxOccurs="unbounded"`
- First child is `<xsd:element name="name">` (or another key element)
- Key element has `<flag>identifier</flag>`, `<identifier/>`, and `key` attribute
- Key element has `<flag>nokeyword</flag>` (value is freeform, not a keyword)

### 3. Enumerations

```xml
<xsd:simpleType>
  <xsd:restriction base="xsd:string">
    <xsd:enumeration value="all"/>
    <xsd:enumeration value="rule-engine"/>
    <xsd:enumeration value="core"/>
  </xsd:restriction>
</xsd:simpleType>
```

Often wrapped in `xsd:union` with numeric types, allowing either an enum keyword
or a numeric value.

### 4. Regex Validation Patterns

```xml
<xsd:appinfo>
  <match>
    <pattern>^[[:alnum:]._-]+$</pattern>
    <message>Must be a string of alphanumericals, dashes or underscores</message>
  </match>
</xsd:appinfo>
```

Patterns prefixed with `!` are negated (value must NOT match).

### 5. Appinfo Flags

| Flag | Count | Meaning |
|------|-------|---------|
| `nokeyword` | 5,719 | Value is freeform (not a keyword enum) |
| `mandatory` | 3,762 | Element is required |
| `identifier` | 2,919 | Element is a list key |
| `oneliner` | 2,676 | Display format hint (set command structure) |
| `mustquote` | 1,604 | Value may contain spaces/special chars |
| `positional` | 72 | Positional argument (no keyword in set path) |
| `hidden-from-cli` | 1,408 | Not visible in CLI (skip in set validation) |

## SchemaNode Data Structure

The XSD is parsed into a tree of `SchemaNode` objects — a condensed intermediate
representation that uses 10-20x less memory than the full lxml tree:

```python
@dataclass
class SchemaNode:
    name: str
    children: dict[str, "SchemaNode"]
    is_key: bool = False
    is_list: bool = False
    is_mandatory: bool = False
    is_leaf: bool = False
    is_presence: bool = False
    enums: list[str] | None = None
    pattern: str | None = None
    pattern_negated: bool = False
    type_ref: str | None = None
    flags: set[str] = field(default_factory=set)
```

## Artifact Pipeline

```
NETCONF XSD dump (output.xml)
    │
    ▼
xsd_extractor.py ─── Extract <xsd:schema> text
    │
    ▼
xsd_parser.py ────── Parse into SchemaNode tree
    │
    ▼
xsd_fixes.py ─────── Apply structural corrections (Groups A-H)
    │
    ├──► artifact_builder.py ──► junos-structure-tree.json (conversion)
    ├──► schema_generator.py ──► junos-json-schema.json   (JSON validation)
    ├──►                     ──► junos-yaml-schema.json   (YAML validation)
    ├──► grammar_generator.py ─► junos-set.lark           (set validation)
    └──►                     ──► junos-schema-meta.json   (metadata)
```

### Generated Artifacts

| Artifact | File | Purpose |
|----------|------|---------|
| Structure tree | `junos-structure-tree.json` | Compact schema for conversion and field validation |
| JSON Schema | `junos-json-schema.json` | Validates Junos-native JSON format |
| YAML Schema | `junos-yaml-schema.json` | Validates standard YAML format |
| Lark grammar | `junos-set.lark` | Validates set commands |
| Metadata | `junos-schema-meta.json` | Version, generation date, stats |

### Bundled Artifacts

The package ships with pre-generated artifacts in `src/junoscfg/validate/data/`,
generated from the Junos 21.4R0 XSD. These are used by default when no custom
artifacts are specified.

## Structure Tree Compact Format

The `junos-structure-tree.json` uses single-letter keys for compactness:

| Key | Type | Meaning | Set by |
|-----|------|---------|--------|
| `c` | `{...}` | Children dict | xsd_parser |
| `l` | `true` | Leaf node | xsd_parser |
| `p` | `true` | Presence flag (no value) | xsd_parser |
| `L` | `true` | Named list | xsd_parser |
| `ll` | `true` | Leaf-list (repeated leaf, always array in JSON) | artifact_builder |
| `nk` | `true` | Nokeyword | Group F fixes |
| `o` | `true` | Oneliner (flat entry) | Group B2/H fixes |
| `t` | `"child"` | Transparent container | Group H fix |
| `tk` | `true` | Transparent list key | Group H fix |
| `pk` | `true` | Positional key (nesting) | Group H fix |
| `pkf` | `true` | Positional key (flat) | Group H fix |
| `fd` | `true` | Flat dict element | Group H fix |
| `fe` | `{"k":"..","p":".."}` | Flat entry config | Group H fix |
| `frnk` | `true` | Freeform NK key | Group H fix |
| `e` | `int` | Enum list index (into `_enums` table) | artifact_builder |
| `r` | `int` | Regex pattern index (into `_patterns` table) | artifact_builder |
| `m` | `true` | Mandatory field | xsd_parser |
| `tr` | `"type"` | XSD type reference (e.g. `"ipaddr"`, `"uint32"`) | xsd_parser |

### Deduplication Tables

The structure tree includes two top-level deduplication tables to reduce file size:

| Table | Description |
|-------|-------------|
| `_enums` | Array of enum value lists. Nodes reference by index via `e`. |
| `_patterns` | Array of regex pattern strings. Nodes reference by index via `r`. Patterns prefixed with `!` are negated. |

These tables allow many schema nodes to share the same enum or pattern definition
without duplicating the data in every node.

## User-Generated Artifacts

Users can generate artifacts from their own Junos device's NETCONF XSD dump:

### CLI

```bash
# Generate all validation artifacts from a NETCONF dump
junoscfg schema generate output.xml -o ./my-artifacts/

# Use custom artifacts for validation
junoscfg -v --artifacts ./my-artifacts/ -i json config.json

# Or set via environment variable
export JUNOSCFG_ARTIFACTS=./my-artifacts/
junoscfg -v -i json config.json
```

### Python API

```python
from junoscfg.validate.artifact_builder import ArtifactBuilder
from junoscfg.validate.validator import JunosValidator

# Generate artifacts
builder = ArtifactBuilder()
artifacts = builder.build("output.xml", "./my-artifacts/")

# Use custom artifacts
validator = JunosValidator(artifacts_dir="./my-artifacts/")
result = validator.validate_json(config)
```

## XSD Fix Groups

The `xsd_fixes.py` module applies structural corrections to the SchemaNode tree
after parsing. Fixes are organized into groups:

| Group | Description | Count |
|-------|-------------|-------|
| A | Variable placeholders (`$junos-*`) | — (handled in parser) |
| B | Complete structure replacement (`groups`) | 1 |
| B2 | Missing flags (oneliner) | 1 |
| C | Literal symbol names (`=`, `+`, `-`) | 3 |
| D | Missing elements | 13 |
| E | Wrong element names | 5 |
| F | Nokeyword / generic name fixes | 4 |
| G | Structure/combinator fixes | 6 |
| H | Conversion hints (transparent, flat entry, etc.) | 7 |

Groups A-G fix genuine XSD deficiencies. Group H encodes conversion-hint flags
that tell the runtime converters how to handle specific elements. All fixes persist
across XSD regeneration because they are applied in Python code, not stored in the
artifacts.

### Example: Ephemeral Instance Fix (Group D/G)

The XSD models `system configuration-database ephemeral instance` as a presence-only
node, but in practice each instance has a name (e.g., `"dgipingtest"`, `"0"`). Without
a fix, instance names are lost during set→set round-trips.

The schema fix changes ephemeral `instance` from a presence node to a named list,
preserving instance names through the IR. This is a typical example of a Group D
(missing element) or Group G (structure/combinator) fix.

See the [Conversion Bugfix Guide](conversion-bugfix-guide.md) for the methodology
for diagnosing and fixing conversion bugs using these fix groups.
