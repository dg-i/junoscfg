# CLI Guide

The `junoscfg` CLI converts and validates Junos configurations. Exact command,
argument, option, default, and choice details are in the generated
[command and option reference](cli-reference.md).

## Usage

```text
junoscfg [OPTIONS] COMMAND [ARGS]...
```

## Convert Command

Convert Junos configurations between formats. This is the default command.

```text
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

`conf` is a CLI alias for `structured` — they are interchangeable in `-i` and `-e` options.

Auto-detection examines parsed input content: JSON objects/arrays, YAML mappings
or lists, XML tags, display-set commands (`set`, `deactivate`, `protect`,
`activate`, or `delete`), or structured curly-brace blocks.
JSON is tried before YAML because JSON is also valid YAML; flow-style YAML that
starts with `{` is recognized when JSON parsing fails.

### Schema Validation

Use `-v` alone (without `-e`) to validate without converting. `--artifacts`
selects the schema artifacts directory for conversion and validation alike.

### Field Validation

Field-level validation checks leaf values against schema constraints (enums, patterns,
IP addresses, integer bounds, mandatory fields). It runs by default during conversion,
printing warnings to stderr. Use `--strict` to make validation errors fatal, or
`--no-field-validate` to skip it entirely.

### Path Filtering

Use `--path` to select a dot-separated subtree such as `system.syslog`. Add
`--relative` to omit that prefix from rendered output.

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

A statement the schema cannot place is still anonymized: each word a rule knows by its
shape alone (an address, a password hash, a sensitive word) is replaced, every other
word is left as written, and an `anonymize:` warning on stderr names its schema path,
never its text. Stop on that warning, or add `--strict`, when no such word may be
published. Groups named `re0`, `re1`, `node0`, `node1`, `member<N>` or a `$` variable
keep their names. See [validation](validation.md).

A value written inside free text is replaced by the rule that owns it: under
`--anonymize-ips` an address in a URL, a description or an annotation (the address
alone in a free-text leaf too, an SNMP OID aside), under `--anonymize-identities` and
`--anonymize-passwords` a URL's user and password (`scp://operator:secret@...`, the user
with the login user's pseudonym), under `--anonymize-passwords` a password hash in prose,
and with `--anonymize-as-numbers-in-strings` a target AS number inside text, never inside
an address. A sensitive word's pseudonym follows its spelling, so `ACME` and `acme`
revert each to its own. An `apply-path` names configuration: its names take the
pseudonyms of the names they name, its keywords stay. `--anonymize-ips-in-strings` only
adds an address that is a whole value where the schema says syntax (an SNMP OID, an area
reference).

A wildcard name in a group (`<*>`, `<ge-*>`, `<EBGP-*>`) is a pattern that selects
names, not a name. `<*>` is never replaced. Any other wildcard keeps its angle brackets
and its text is replaced as the names at its place are: `<EBGP>` names the renamed
group `EBGP`, and with `--anonymize-ips` `<203.0.114.*>` becomes the pattern of that
prefix's replacement. A rule that renames whole names cannot keep `<EBGP-*>` selecting
`EBGP-A`: such a wildcard, and one whose text no rule could rewrite (an address pattern
that is no pattern of whole octets, a sensitive word behind a class such as
`<[Aa]cme-*>`, an AS number behind `?`), is named by its schema path in an `anonymize:` warning, never by its
text. Stop on that warning when the group must keep applying to the same names.

No message of an anonymized run quotes the configuration, original or replaced: a
field-validation message keeps its path, reason and expected value and withholds the
value; a refusal to read the input says it could not be read, with its line where the
parser gives one; `-v` prints each error's line without its text or path; a failure no
handler expects prints only its class, with no traceback. Exit codes are those of the
same run without anonymization; run without `--anonymize-*` to see the full messages.
Only `--anonymize-log-level debug` prints originals: each one beside its replacement,
on stderr, by design.

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

#### Anonymization Path Filtering

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

# Subnet-aware anonymization: auto-detect subnets from the config
junoscfg -e json --anonymize-all --anonymize-networks auto config.json

# Subnet-aware anonymization: explicit subnets
junoscfg -e json --anonymize-all --anonymize-networks "10.0.0.0/8-24" config.json

# Load subnet specs from a file
junoscfg -e json --anonymize-all --anonymize-network-file subnets.txt config.json
```

- `--anonymize-preserve-prefixes` — IP addresses within these CIDR prefixes are left unchanged
- `--anonymize-networks` — Subnet-aware host-bit locking: only permute the network portion of IPs,
  preserving host bits so anonymized addresses never land on broadcast or network addresses.
  Accepts plain CIDRs (`192.168.1.0/29`), range notation (`10.0.0.0/8-24`), or `auto` to
  auto-detect subnets from the input config. Repeatable.
- `--anonymize-network-file` — Load subnet specs from a file (one per line, `#` comments allowed)
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
Unambiguous mappings from earlier releases still work. A configuration using
plain and zero-padded spellings of the same IPv4 address can produce one
replacement for both. Equivalent compressed, expanded or differently cased IPv6
spellings can also share a replacement; ambiguity is rejected before output with a
value-free error. Use one spelling per address in the original configuration
and anonymize again. An old map with multiple originals for one IP replacement
is also rejected before restoration: it cannot recover the lost occurrences.
Every successful run restores each replaced spelling exactly.

An apply-path's own include/exclude filter governs its names. Its targets follow
their own filters. If a literal or wildcard selector then selects different
names, conversion warns by the apply-path's schema path without printing values.
This also reports an excluded selector kept unchanged while its target is renamed.
Match-all and selectors that keep their meaning remain quiet.

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

**A random salt is generated automatically** when no salt is provided — whether
that means omitting `--anonymize-salt` or leaving `salt:` blank in an
`--anonymize-config` file. Supply one explicitly only when you need two runs
to produce the same output.
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
  networks:
    - "10.0.0.0/8-24"
    - "192.168.0.0/16-24"
  # network_file: subnets.txt
  ignore_subnets: false
  ignore_reserved: false
  ips_in_strings: true
  as_numbers_in_strings: true

  # Logging
  log_level: normal  # quiet, normal, or debug (debug prints each original beside its replacement)
```

## Schema Commands

Build and inspect validation schema artifacts.

First, retrieve the NETCONF XSD dump from your router:

```bash
echo "<rpc> <get-xnm-information> <type>xml-schema</type> <namespace>junos-configuration</namespace> </get-xnm-information> </rpc>" | ssh -Csp 830 router.example.com netconf > netconf.xml
```

### schema generate

Generate schema artifacts from a NETCONF XSD dump. They are written
gzipped; readers accept either form, so an older uncompressed directory still
works.

```text
junoscfg schema generate XSD_SOURCE -o OUTPUT_DIR
```

Example:

```bash
echo "<rpc> <get-xnm-information> <type>xml-schema</type> <namespace>junos-configuration</namespace> </get-xnm-information> </rpc>" | ssh -Csp 830 router.example.com netconf > netconf.xml
junoscfg schema generate netconf.xml -o ./my-artifacts/
```

### schema info

Display schema artifact information.

```text
junoscfg schema info [--artifacts PATH]
```

Example:

```bash
junoscfg schema info
# Schema version: 25.2R0
# Generated at:   2026-10-08T09:24:16.924958+00:00

junoscfg schema info --artifacts ./my-artifacts/
```

## edityaml Commands

Transform YAML for Ansible consumption. See [edityaml](../edityaml.md) for full documentation.

### edityaml addvars

Add derived keys to YAML using transform rules.

```text
junoscfg edityaml addvars [OPTIONS] [FILE]
```

Examples:

```bash
junoscfg edityaml addvars -r rules.yaml config.yaml
junoscfg edityaml addvars --path "a.b[*]" --set "_x=copy(name)" config.yaml
```

### edityaml ansibilize

Extract leaf values into Ansible `host_vars` and templatize `group_vars`.

```text
junoscfg edityaml ansibilize [OPTIONS] [FILE]
```

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

## Audit Commands

Analyze configurations for problems. See the [Audit guide](audit.md) for
concepts, the registry format, and limitations.

### audit unused

Find config objects (policy statements, prefix lists, firewall filters,
config groups, ...) that are defined but never referenced. Works on the
parsed configuration — any input format — and classifies each finding as
strict `unused` or `probably-unused`. Findings are suggestions requiring
human review.

```bash
junoscfg audit unused [OPTIONS] [FILE]
```

Output styles — each also available as `<style>-verbose`:

| Style | Line format |
|-------|-------------|
| `pathname` | `policy-options policy-statement FOO` |
| `delete-script` | `delete policy-options policy-statement FOO` |
| `show-script` | `show policy-options policy-statement FOO` (configuration mode) |
| `show-configuration-script` | `show configuration policy-options policy-statement FOO` (operational mode) |
| `deactivate-script` | `deactivate policy-options policy-statement FOO` |

Non-verbose output contains only command/path lines (pipe- and
paste-clean). Verbose output adds a comment block per finding (confidence,
duplicate-definition hints, unresolved occurrences for probably-unused
findings) and a summary line. `delete-script` and `deactivate-script`
contain only strict `unused` findings unless `--include-probably-unused`
is given; omitted findings still appear as comments in the verbose
variants.

### Examples — Audit

```bash
# List unused objects (all registry types)
junoscfg audit unused config.conf

# Generate a delete script with review comments
junoscfg audit unused -o delete-script-verbose config.conf

# Only check policy-statements and prefix-lists named legacy-*
junoscfg audit unused --types policy-statement,prefix-list --match '^legacy-' config.set

# CI gate: fail the pipeline when strictly unused objects exist
junoscfg audit unused --fail-on unused config.json

# From stdin, JSON input
cat config.json | junoscfg audit unused -i json -o show-script
```

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success (valid config or conversion succeeded) |
| 1 | Invalid configuration (validation or field validation errors), or audit findings at the `--fail-on` threshold |
| 2 | Usage error (bad arguments) |
| 3 | Schema error (cannot load/generate artifacts) or broken audit registry |

## Full Help

Display combined help for all commands and subcommands at once:

```bash
junoscfg fullhelp
```

## Environment Variables

| Variable | Description |
|----------|-------------|
| `JUNOSCFG_ARTIFACTS` | Default path to validation artifacts directory (overridden by explicit `--artifacts` flag) |
| `JUNOSCFG_AUDIT_REGISTRY` | Default path to the audit type-registry YAML (overridden by explicit `--registry` flag) |
