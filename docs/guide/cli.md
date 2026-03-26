# CLI Reference

The `junoscfg` CLI converts and validates Junos configurations.

## Usage

```
junoscfg [OPTIONS] COMMAND [ARGS]...
```

## Convert Command

Convert Junos configurations between formats. This is the default command.

```
junoscfg convert [OPTIONS] [FILE]
```

If `FILE` is omitted, reads from stdin.

### Help Options

Use `-h`, `--help`, or `-?` at any level to see help text:

```bash
junoscfg -h                # Main help
junoscfg convert -h        # Convert command help
junoscfg schema -?         # Schema group help
```

### Format Options

| Option | Description |
|--------|-------------|
| `-i`, `--import-format` | Input format: `set`, `structured`, `json`, `yaml`, `conf`. Auto-detected if omitted. |
| `-e`, `--export-format` | Output format: `set`, `structured`, `json`, `yaml`, `conf`. Required unless `-v` is used alone. |

`conf` is a CLI alias for `structured` — they are interchangeable in `-i` and `-e` options.

Auto-detection examines the input content: JSON objects/arrays, XML tags, `set`/`deactivate`
keywords, or structured curly-brace blocks.

### Schema Validation

| Option | Description |
|--------|-------------|
| `-v`, `--validate` | Validate configuration before converting |
| `--artifacts PATH` | Path to validation artifacts directory |

Use `-v` alone (without `-e`) to validate without converting.

### Field Validation

| Option | Description |
|--------|-------------|
| `--strict` | Fail on field-level validation errors (exit code 1) |
| `--no-field-validate` | Skip field-level value validation entirely |

Field-level validation checks leaf values against schema constraints (enums, patterns,
IP addresses, integer bounds, mandatory fields). It runs by default during conversion,
printing warnings to stderr. Use `--strict` to make validation errors fatal, or
`--no-field-validate` to skip it entirely.

### Path Filtering

| Option | Description |
|--------|-------------|
| `--path PATH` | Show only config under this path (dot-separated, e.g. `"system.syslog"`) |
| `--relative` | Show relative paths (omit `--path` prefix from output). Requires `--path`. |

### Examples — Conversion

```bash
# Structured config to set commands
junoscfg -i structured -e set config.conf

# JSON to set commands
junoscfg -i json -e set config.json

# JSON to YAML
junoscfg -i json -e yaml config.json

# Set commands to JSON
junoscfg -i set -e json config.set

# Auto-detect input format (omit -i)
junoscfg -e set config.json

# Use "conf" alias for structured
junoscfg -i conf -e set config.conf
junoscfg -i set -e conf config.set

# Identity conversions (normalize/canonicalize)
junoscfg -i json -e json config.json
junoscfg -i set -e set config.set
junoscfg -i yaml -e yaml config.yaml
```

### Examples — Validation

```bash
# Validate JSON then convert to set
junoscfg -v -i json -e set config.json

# Validate only (no conversion)
junoscfg -v -i json config.json
```

### Examples — Path Filtering

Path filtering is supported for all output formats: `set`, `structured`, `yaml`, and `json`.

```bash
# Filter to system section only
junoscfg -i json -e set config.json --path "system"

# Filter with relative paths
junoscfg -i json -e set config.json --path "system.syslog" --relative

# Filter JSON output to system section
junoscfg -i json -e json config.json --path "system"
```

### Examples — stdin

```bash
cat config.json | junoscfg -i json -e set
echo '{"configuration":{"system":{"host-name":"test"}}}' | junoscfg -e set
```

### Field Validation Examples

```bash
# Convert with strict field validation (fail on errors)
junoscfg -i json -e set --strict config.json

# Convert without field validation
junoscfg -i json -e set --no-field-validate config.json

# Field validation warnings are printed to stderr by default
junoscfg -i set -e json config.set 2>validation.log
```

### Anonymization

Replace sensitive data with deterministic pseudonyms.

| Option | Description |
|--------|-------------|
| `--anonymize-all` | Enable all boolean anonymization rules |
| `--anonymize-ips` | Anonymize IP addresses |
| `--anonymize-passwords` | Anonymize passwords and secrets |
| `--anonymize-communities` | Anonymize SNMP community strings |
| `--anonymize-ssh-keys` | Anonymize SSH public keys |
| `--anonymize-identities` | Anonymize usernames and identities |
| `--anonymize-groups` | Anonymize group and view names |
| `--anonymize-descriptions` | Anonymize description fields |
| `--anonymize-as-numbers` | Comma-separated AS numbers to anonymize; supports explicit mapping with `original:replacement` (e.g., `1234:100,5678:101`) |
| `--anonymize-sensitive-words` | Comma-separated literal strings to anonymize (case-insensitive) |
| `--anonymize-sensitive-patterns` | Regex pattern for sensitive data (repeatable) |
| `--anonymize-salt` | Shared salt for deterministic output |
| `--anonymize-dump-map` | Write revert dictionary to file |
| `--anonymize-revert-map` | Apply revert dictionary (restore originals) |
| `--anonymize-include` | Only anonymize paths matching this glob (repeatable) |
| `--anonymize-exclude` | Skip paths matching this glob (repeatable) |
| `--anonymize-preserve-prefixes` | IP prefixes to preserve unchanged (repeatable) |
| `--anonymize-ignore-subnets` | Treat sub-/8 private ranges as public (anonymize them fully instead of preserving the range) |
| `--anonymize-ignore-reserved` | Remove all reserved range handling (no ranges are preserved) |
| `--anonymize-ips-in-strings` | Also replace IPs embedded in larger strings |
| `--anonymize-as-numbers-in-strings` | Also replace AS numbers embedded in strings |
| `--anonymize-log-level` | Logging verbosity: `quiet`, `normal` (default), or `debug` |
| `--anonymize-config` | YAML config file with all anonymization options |

#### Examples — Anonymization

```bash
# Anonymize all sensitive data
junoscfg -i json -e json --anonymize-all config.json

# Anonymize IPs with a salt for deterministic output
junoscfg -e yaml --anonymize-ips --anonymize-salt s3cr3t config.json

# Anonymize using a YAML config file
junoscfg -e set --anonymize-config anon.yaml config.json

# Revert anonymization using a saved mapping
junoscfg -i json -e json --anonymize-revert-map revert.json anon.json

# Anonymize literal words (comma-separated)
junoscfg -e set --anonymize-sensitive-words "acmecorp,newyork" config.json

# Anonymize with regex patterns (repeatable)
junoscfg -e set --anonymize-sensitive-patterns 'LAX\d+' config.json

# Match FQDNs under example.com
junoscfg -e set \
  --anonymize-sensitive-patterns '([a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)+example\.com' \
  config.json

# Combine words and patterns
junoscfg -e set \
  --anonymize-sensitive-words "acmecorp" \
  --anonymize-sensitive-patterns 'LAX\d+' \
  --anonymize-sensitive-patterns 'corp-[a-z]+-\d+' \
  config.json

# Anonymize specific AS numbers
junoscfg -e set --anonymize-as-numbers 64496,64497 config.json

# Anonymize AS numbers with explicit mappings
junoscfg -e set --anonymize-as-numbers 64496:100,64497:101 config.json
```

#### YAML Config File

Both `sensitive_words` and `sensitive_patterns` can be specified in a YAML config file:

```yaml
anonymize:
  ips: true
  passwords: true
  salt: "my-salt"
  sensitive_words:
    - acmecorp
    - newyork
  sensitive_patterns:
    - 'LAX\d+'
    - 'corp-[a-z]+-\d+'
```

#### What `--anonymize-all` Enables

`--anonymize-all` enables the following boolean rules:

- `--anonymize-ips`
- `--anonymize-passwords`
- `--anonymize-communities`
- `--anonymize-ssh-keys`
- `--anonymize-identities`
- `--anonymize-groups`
- `--anonymize-descriptions`
- `--anonymize-ips-in-strings`
- `--anonymize-as-numbers-in-strings`

It does **not** enable `--anonymize-as-numbers`, `--anonymize-sensitive-words`, or
`--anonymize-sensitive-patterns` — these require explicit user-provided lists.

#### Path Filtering

Use `--anonymize-include` and `--anonymize-exclude` to restrict which configuration
sections are anonymized. Paths use dot-separated segments with glob matching.

```bash
# Only anonymize the interfaces section
junoscfg -e json --anonymize-ips --anonymize-include "interfaces" config.json

# Anonymize everything except system
junoscfg -e json --anonymize-all --anonymize-exclude "system" config.json

# Include with wildcards
junoscfg -e json --anonymize-ips --anonymize-include "protocols.bgp.*" config.json
```

**Precedence when both are specified:** exclude always wins over include. If a path
matches both an include and an exclude pattern, it is **excluded** (not anonymized).
Containers above included paths are still walked so the anonymizer can reach nested
matching paths.

```bash
# Include interfaces but exclude the loopback interface's addresses
junoscfg -e json --anonymize-ips \
  --anonymize-include "interfaces" \
  --anonymize-exclude "interfaces.interface.lo0" \
  config.json
```

#### IP-Specific Options

```bash
# Preserve IPs in specific subnets (e.g. management network)
junoscfg -e json --anonymize-ips --anonymize-preserve-prefixes "10.1.0.0/16" config.json

# Skip subnet-only addresses
junoscfg -e json --anonymize-ips --anonymize-ignore-subnets config.json

# Skip reserved/private IP ranges
junoscfg -e json --anonymize-ips --anonymize-ignore-reserved config.json
```

- `--anonymize-preserve-prefixes` — IP addresses within these CIDR prefixes are left unchanged
- `--anonymize-ignore-subnets` — Skip addresses that represent subnets (network/broadcast)
- `--anonymize-ignore-reserved` — Skip RFC 1918 and other reserved ranges

#### Revert Workflow

Anonymize a configuration, save the revert dictionary, share the anonymized config,
then restore originals when needed:

```bash
# Step 1: Anonymize and save the mapping
junoscfg -i json -e json --anonymize-all \
  --anonymize-dump-map revert.json config.json > anon.json

# Step 2: Share anon.json (the mapping file stays private)

# Step 3: Restore original values from the mapping
junoscfg -i json -e json --anonymize-revert-map revert.json anon.json
```

The mapping file is JSON with the structure:

```json
{
  "ip": {
    "8.8.8.8": "198.18.1.42",
    "10.1.2.3/24": "10.99.44.7/24"
  },
  "password": {
    "$9$ExAmPlEhAsH.KEY": "$9$RePlAcEdHaSh.KEY"
  }
}
```

Each key is the rule name; values are `{original: anonymized}` pairs.

#### Deterministic Output with Salt

When `--anonymize-salt` is provided, the same input + same salt always produces the
same output. This is useful for diff-friendly anonymization across runs:

```bash
# Both runs produce identical output
junoscfg -e set --anonymize-ips --anonymize-salt "team-salt" config.json > run1.set
junoscfg -e set --anonymize-ips --anonymize-salt "team-salt" config.json > run2.set
diff run1.set run2.set  # no differences
```

Without a salt, output is still deterministic within a single run but may vary
between runs.

#### Security Considerations

**IP anonymization preserves subnet structure.** The IP anonymizer uses prefix-preserving
permutation, which means two IPs sharing a /24 prefix in the original will also share
a common prefix in the output. An attacker who knows one IP mapping can identify
every other IP in the same subnet. This is a fundamental property of prefix-preserving
anonymization — it retains CIDR relationships for troubleshooting at the cost of
reduced confidentiality. If full IP confidentiality is required, use a non-prefix-preserving
approach instead.

**A random salt is generated automatically** when `--anonymize-salt` is not provided.
This prevents trivially reversible outputs but means results are not reproducible across
runs. Provide an explicit salt if you need deterministic output (e.g., for diff-friendly
anonymization).

**AS number anonymization uses sequential replacement** (64496, 64497, ...) from the
RFC 5398 documentation range. Use explicit mappings (`--anonymize-as-numbers 1234:100`)
if you need specific replacement values.

#### Rule Priority

When multiple rules could match a single value, the first matching rule wins.
Rules are checked in priority order: passwords, IPs, communities, SSH keys,
identities, groups, descriptions, AS numbers, sensitive words. For example,
a description field is handled by the description rule before the sensitive-word
rule gets a chance to match.

#### Complete YAML Config Example

```yaml
anonymize:
  # Boolean rules
  ips: true
  passwords: true
  communities: true
  ssh_keys: true
  identities: true
  groups: true
  descriptions: true

  # List-based rules
  as_numbers:
    - 64497
    - 64498
  sensitive_words:
    - acmecorp
    - newyork
  sensitive_patterns:
    - 'LAX\d+'
    - 'corp-[a-z]+-\d+'

  # Shared options
  salt: "my-salt"
  dump_map: "revert.json"

  # Path filters
  include:
    - interfaces
    - protocols.bgp
  exclude:
    - system.ntp

  # IP-specific
  preserve_prefixes:
    - "10.1.0.0/16"
  ignore_subnets: false
  ignore_reserved: false
  ips_in_strings: true
  as_numbers_in_strings: true

  # Logging
  log_level: normal  # quiet, normal, or debug
```

## Schema Commands

Build and inspect validation schema artifacts.

First, retrieve the NETCONF XSD dump from your router:

```bash
echo "<rpc> <get-xnm-information> <type>xml-schema</type> <namespace>junos-configuration</namespace> </get-xnm-information> </rpc>" | ssh -Csp 830 router.example.com netconf > netconf.xml
```

### schema generate

Generate validation artifacts from a NETCONF XSD dump.

```
junoscfg schema generate XSD_SOURCE -o OUTPUT_DIR
```

| Argument/Option | Description |
|-----------------|-------------|
| `XSD_SOURCE` | Path to NETCONF XSD dump file |
| `-o`, `--output-dir` | Output directory for generated artifacts (required) |

Example:

```bash
echo "<rpc> <get-xnm-information> <type>xml-schema</type> <namespace>junos-configuration</namespace> </get-xnm-information> </rpc>" | ssh -Csp 830 router.example.com netconf > netconf.xml
junoscfg schema generate netconf.xml -o ./my-artifacts/
```

### schema makedoc

Generate a YAML-like configuration reference from XSD.

```
junoscfg schema makedoc XSD_SOURCE [OPTIONS]
```

| Argument/Option | Description |
|-----------------|-------------|
| `XSD_SOURCE` | Path to NETCONF XSD dump file |
| `-o`, `--output` | Output file (prints to stdout if omitted) |
| `--max-depth` | Maximum nesting depth (0 = unlimited) |
| `--section` | Only show this section (e.g. `"system"` or `"system syslog"`) |
| `--no-enums` | Omit enum value listings |
| `--no-deprecated` | Omit deprecated elements |
| `--compact` | Omit descriptions, show only structure |

Examples:

```bash
junoscfg schema makedoc netconf.xml -o reference.yaml
junoscfg schema makedoc netconf.xml --section "system" --compact
junoscfg schema makedoc netconf.xml --max-depth 3 --no-deprecated
```

### schema info

Display schema artifact information.

```
junoscfg schema info [--artifacts PATH]
```

| Option | Description |
|--------|-------------|
| `--artifacts PATH` | Path to artifacts directory (defaults to bundled artifacts) |

Example:

```bash
junoscfg schema info
# Schema version: 21.4R0
# Generated at:   2026-02-13T12:00:00Z

junoscfg schema info --artifacts ./my-artifacts/
```

## edityaml Commands

Transform YAML for Ansible consumption. See [edityaml](../edityaml.md) for full documentation.

### edityaml addvars

Add derived keys to YAML using transform rules.

```
junoscfg edityaml addvars [OPTIONS] [FILE]
```

| Option | Description |
|--------|-------------|
| `-r`, `--rules` | YAML file containing transform rules |
| `--path` | Path expression for inline `--set` transforms |
| `--set` | Inline transform expression (repeatable). Requires `--path`. |

Examples:

```bash
junoscfg edityaml addvars -r rules.yaml config.yaml
junoscfg edityaml addvars --path "a.b[*]" --set "_x=copy(name)" config.yaml
```

### edityaml ansibilize

Extract leaf values into Ansible `host_vars` and templatize `group_vars`.

```
junoscfg edityaml ansibilize [OPTIONS] [FILE]
```

| Option | Description |
|--------|-------------|
| `-p`, `--prefix_path` | `prefix:path` pair for literal extraction (repeatable). Split on first `:`. |
| `-P`, `--offset-prefix-path` | `prefix:path` pair for offset-mode extraction (repeatable). Split on first `:`. |
| `--offset-var NAME` | Name of the per-host offset variable (default: `base_address_offset`). |
| `--root PATTERN` | Top-level key glob to descend into (repeatable). Overrides auto-descend. |

At least one of `-p` or `-P` is required. With `-p` only, outputs 2 YAML documents. With `-P`, outputs 3 YAML documents (host_vars, offset expressions, template).

Examples:

```bash
junoscfg edityaml ansibilize -p "addr:items[*].name" config.yaml
junoscfg edityaml ansibilize -p "host:system.host-name" \
  -p "addr:interfaces.interface[*].unit[*].family.*.address[*].name" \
  config.yaml
junoscfg edityaml ansibilize \
  -P "addr:interfaces.interface[*].unit[*].family.*.address[*].name" config.yaml
junoscfg edityaml ansibilize -p "host:system.host-name" \
  -P "addr:interfaces.interface[*].unit[*].family.*.address[*].name" config.yaml
```

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success (valid config or conversion succeeded) |
| 1 | Invalid configuration (validation or field validation errors) |
| 2 | Usage error (bad arguments) |
| 3 | Schema error (cannot load/generate artifacts) |

## Full Help

Display combined help for all commands and subcommands at once:

```bash
junoscfg fullhelp
```

## Environment Variables

| Variable | Description |
|----------|-------------|
| `JUNOSCFG_ARTIFACTS` | Default path to validation artifacts directory (overridden by explicit `--artifacts` flag) |
