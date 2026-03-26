# edityaml: Post-Process YAML with Transform Rules

`junoscfg edityaml` is a command group for transforming YAML output. It has two subcommands:

- **`addvars`** — Add derived keys to YAML documents using declarative transform rules.
- **`ansibilize`** — Extract selected leaf values into Ansible host_vars and replace them with Jinja2 `{{ variable }}` references in the template.

## Overview

After converting Junos configs to YAML with `junoscfg convert`, you may need to post-process the output for Ansible consumption. The two subcommands serve different purposes:

**`addvars`** enriches YAML nodes with new keys derived from existing values (regex extraction, copies, templates). Use it to add metadata keys like `_ansible_bgp_peername` extracted from descriptions.

**`ansibilize`** splits a YAML config into two documents for Ansible's lazy loading pattern: host_vars (per-host values) and group_vars (shared template with Jinja2 references). Use it to make specific leaf values overridable per-host.

## addvars CLI Usage

### Rule file mode

```bash
junoscfg edityaml addvars -r rules.yaml config.yaml
```

### Inline mode (--path + --set)

```bash
# Extract BGP peer name from description with regex
junoscfg edityaml addvars \
  --path "configuration.protocols.bgp.group[*].neighbor[*]" \
  --set "_ansible_bgp_peername=regex_extract(description, 'overlay: (\\w+)')" \
  config.yaml

# Copy interface name to a new key
junoscfg edityaml addvars \
  --path "configuration.interfaces.interface[*]" \
  --set "_intf=copy(name)" \
  config.yaml

# Add a static boolean flag
junoscfg edityaml addvars \
  --path "configuration.system" \
  --set "_ansible_managed=static(true)" \
  config.yaml

# Set a bare string value (shorthand for static)
junoscfg edityaml addvars \
  --path "configuration.system" \
  --set "_env=production" \
  config.yaml

# Build a label from multiple fields using a template
junoscfg edityaml addvars \
  --path "configuration.interfaces.interface[*]" \
  --set "_label=template('intf-{name}')" \
  config.yaml

# Multiple --set expressions on the same path
junoscfg edityaml addvars \
  --path "configuration.protocols.bgp.group[*].neighbor[*]" \
  --set "_peer=copy(name)" \
  --set "_role=regex_extract(description, '(\\w+):')" \
  config.yaml
```

### Combined (file rules execute first, then inline)

```bash
junoscfg edityaml addvars -r rules.yaml \
  --path "configuration.system" \
  --set "_ansible_managed=static(true)" \
  config.yaml
```

### Stdin

```bash
# Pipe from another command
cat config.yaml | junoscfg edityaml addvars -r rules.yaml

# Convert and add vars in one pipeline
junoscfg -i json -e yaml config.json | \
  junoscfg edityaml addvars \
    --path "configuration.system" \
    --set "_managed=static(true)"
```

Output goes to stdout, consistent with the `convert` command.

## Rule File Format

```yaml
rules:
  - path: "configuration.protocols.bgp.group[*].neighbor[*]"
    transforms:
      - type: regex_extract
        source: description
        pattern: "overlay: (\\w+)"
        target: _ansible_bgp_peername
        group: 1                    # optional, defaults to 1

  - path: "configuration.system"
    transforms:
      - type: static
        target: _ansible_managed
        value: true

  - path: "configuration.interfaces.interface[*]"
    transforms:
      - type: copy
        source: name
        target: _intf_name

      - type: rename
        source: old-key
        target: new-key

      - type: template
        target: _ansible_intf_label
        template: "intf-{name}-{unit}"

      - type: conditional
        when:
          key: description
          matches: ".*uplink.*"
        transforms:
          - type: static
            target: _is_uplink
            value: true
```

## Path Syntax

Dot-separated keys with wildcards, named matches, and glob patterns for traversing nested structures:

| Segment | Syntax | Meaning |
|---------|--------|---------|
| Fixed key | `system` | Navigate into the `system` dict |
| List wildcard | `interface[*]` | Iterate each item in the `interface` list |
| Named match | `groups[ansible-managed]` | Select the list item where `name == "ansible-managed"` |
| Glob match | `groups[ansible-*]` | Select list items where `name` matches the glob pattern |
| Dict wildcard | `*` | Iterate all dict-valued children of the current node |
| Dict glob | `inet*` | Iterate dict children whose key matches the glob pattern |

### Examples

| Pattern | Meaning |
|---------|---------|
| `configuration.system` | Navigate to the `system` dict |
| `configuration.interfaces.interface[*]` | Each item in the `interface` list |
| `configuration.protocols.bgp.group[*].neighbor[*]` | Each neighbor in each group |
| `configuration.groups[ansible-managed].interfaces` | Interfaces under the group named exactly `ansible-managed` |
| `configuration.groups[ansible-*].interfaces.interface[*]` | Interfaces under any group whose name starts with `ansible-` |
| `configuration.interfaces.interface[*].unit[*].family.inet*.address[*]` | Addresses under `inet` and `inet6` families (but not `mpls`) |
| `configuration.groups[ansible-*].interfaces.interface[*].unit[*].family.inet*.address[*]` | Full glob path: filter group by name pattern, match address families by key pattern |

The `*` dict wildcard iterates *all* dict-valued children. Use `inet*` (dict glob) when you want to match only keys fitting a pattern — e.g. `family.inet*` matches `inet` and `inet6` but not `mpls`.

The `[name]` named match is a fixed filter — it selects exactly one list item. Use `[pattern*]` (glob match) when the name might vary or you want to match a prefix.

Glob patterns use Python's `fnmatch` syntax: `*` matches anything, `?` matches one character, `[seq]` matches character ranges.

Missing keys at any point silently produce zero matches (no error).

The same path syntax is used across all `junoscfg` commands that accept `--path`: `convert`, `edityaml addvars`, and `edityaml ansibilize`.

## Transform Types

| Type | Required fields | Behavior |
|------|----------------|----------|
| `regex_extract` | source, pattern, target | Apply regex to sibling key, store capture group |
| `static` | target, value | Set literal value (string, number, boolean) |
| `copy` | source, target | Copy sibling key value |
| `rename` | source, target | Move key (delete old, create new) |
| `template` | target, template | Format string with `{sibling_key}` references |
| `conditional` | when, transforms | Apply nested transforms if condition matches |

### regex_extract

Applies a regex to the value of `source`. If it matches, stores the capture group (default group 1) in `target`.

```yaml
- type: regex_extract
  source: description
  pattern: "overlay: (\\w+)"
  target: _ansible_bgp_peername
  group: 1  # optional, defaults to 1
```

### static

Sets a literal value.

```yaml
- type: static
  target: _ansible_managed
  value: true
```

### copy

Copies the value of an existing sibling key to a new key.

```yaml
- type: copy
  source: name
  target: _intf_name
```

### rename

Moves a key (deletes old, creates new).

```yaml
- type: rename
  source: old-key
  target: new-key
```

### template

Format string using sibling keys as `{key}` references. Skipped if any referenced key is missing.

```yaml
- type: template
  target: _label
  template: "intf-{name}-{unit}"
```

### conditional

Apply nested transforms only when a condition matches. Supports `matches` (regex) and `equals` (exact match).

```yaml
- type: conditional
  when:
    key: description
    matches: ".*uplink.*"
  transforms:
    - type: static
      target: _is_uplink
      value: true
```

## Inline --set Expression Reference

| Expression | Equivalent rule type |
|-----------|---------------------|
| `_foo=regex_extract(key, 'pattern')` | regex_extract |
| `_foo=regex_extract(key, 'pattern', 2)` | regex_extract with group |
| `_foo=static(true)` | static (boolean) |
| `_foo=static(42)` | static (integer) |
| `_foo=copy(key)` | copy |
| `_foo=template('text {key}')` | template |
| `_foo=bar` | static (bare string value) |

## addvars Worked Examples

### BGP Peer Name Extraction

**Input YAML** (`config.yaml`):
```yaml
configuration:
  protocols:
    bgp:
      group:
        - name: overlay
          neighbor:
            - name: 10.0.0.1
              description: "overlay: spine1"
            - name: 10.0.0.2
              description: "overlay: spine2"
```

**Rule file** (`rules.yaml`):
```yaml
rules:
  - path: "configuration.protocols.bgp.group[*].neighbor[*]"
    transforms:
      - type: regex_extract
        source: description
        pattern: "overlay: (\\w+)"
        target: _ansible_bgp_peername
```

**Command**:
```bash
junoscfg edityaml addvars -r rules.yaml config.yaml
```

**Output**:
```yaml
configuration:
  protocols:
    bgp:
      group:
        - name: overlay
          neighbor:
            - name: 10.0.0.1
              description: "overlay: spine1"
              _ansible_bgp_peername: spine1
            - name: 10.0.0.2
              description: "overlay: spine2"
              _ansible_bgp_peername: spine2
```

The same thing inline, without a rule file:

```bash
junoscfg edityaml addvars \
  --path "configuration.protocols.bgp.group[*].neighbor[*]" \
  --set "_ansible_bgp_peername=regex_extract(description, 'overlay: (\\w+)')" \
  config.yaml
```

### Copy Interface Names for Ansible Lookups

Add an `_intf` key to every interface — useful when Ansible playbooks need to reference the interface name after further nesting:

```bash
junoscfg edityaml addvars \
  --path "configuration.interfaces.interface[*]" \
  --set "_intf=copy(name)" \
  config.yaml
```

**Input**:
```yaml
configuration:
  interfaces:
    interface:
      - name: ge-0/0/0
        unit: "0"
      - name: ge-0/0/1
        unit: "1"
```

**Output**:
```yaml
configuration:
  interfaces:
    interface:
      - name: ge-0/0/0
        unit: "0"
        _intf: ge-0/0/0
      - name: ge-0/0/1
        unit: "1"
        _intf: ge-0/0/1
```

### Multiple Transforms in One Command

Extract both the peer address and the role from a BGP description:

```bash
junoscfg edityaml addvars \
  --path "configuration.protocols.bgp.group[*].neighbor[*]" \
  --set "_peer=copy(name)" \
  --set "_role=regex_extract(description, '(\\w+):')" \
  --set "_managed=static(true)" \
  config.yaml
```

### Build Labels from Multiple Fields

Use templates to combine fields into a single label:

```bash
junoscfg edityaml addvars \
  --path "configuration.interfaces.interface[*]" \
  --set "_label=template('intf-{name}')" \
  config.yaml
```

**Output** (each interface gets a label):
```yaml
- name: ge-0/0/0
  _label: intf-ge-0/0/0
- name: ge-0/0/1
  _label: intf-ge-0/0/1
```

### Conditional Transforms (Mark Uplink Interfaces)

Only add `_is_uplink: true` to interfaces whose description contains "uplink":

**Rule file** (`uplinks.yaml`):
```yaml
rules:
  - path: "configuration.interfaces.interface[*]"
    transforms:
      - type: conditional
        when:
          key: description
          matches: ".*uplink.*"
        transforms:
          - type: static
            target: _is_uplink
            value: true
```

```bash
junoscfg edityaml addvars -r uplinks.yaml config.yaml
```

**Input**:
```yaml
configuration:
  interfaces:
    interface:
      - name: xe-0/0/0
        description: "uplink to spine1"
      - name: ge-0/0/1
        description: "server port"
```

**Output** (only the uplink gets tagged):
```yaml
configuration:
  interfaces:
    interface:
      - name: xe-0/0/0
        description: "uplink to spine1"
        _is_uplink: true
      - name: ge-0/0/1
        description: "server port"
```

### Multi-Path Rules

A single rule file can target different schema paths:

```yaml
rules:
  - path: "configuration.system"
    transforms:
      - type: static
        target: _ansible_managed
        value: true

  - path: "configuration.protocols.bgp.group[*].neighbor[*]"
    transforms:
      - type: regex_extract
        source: description
        pattern: "overlay: (\\w+)"
        target: _ansible_bgp_peername

  - path: "configuration.interfaces.interface[*]"
    transforms:
      - type: copy
        source: name
        target: _intf_name
```

```bash
junoscfg edityaml addvars -r multi-rules.yaml config.yaml
```

### Real-World Pipeline: BGP Overlay Peer Enrichment

A common workflow is to fetch a Junos config via SSH in JSON format, convert it to YAML, and then enrich it with derived keys for Ansible. Here is a complete end-to-end example.

**Fetch and convert** (the `junoscfg convert` output used as input below):

```bash
ssh switch01.example.net \
  "show configuration protocols bgp group overlay | display json" \
  | junoscfg convert -i json -e yaml
```

**Input YAML** (output of the convert step above):

```yaml
configuration:
  '@':
    junos:commit-seconds: '1711929600'
    junos:commit-localtime: 2024-04-01 12:00:00 UTC
    junos:commit-user: admin
  protocols:
    bgp:
      group:
      - name: overlay
        local-address: 192.168.100.2
        local-as:
          as-number: '4200000001'
        neighbor:
        - name: 192.168.100.15
          description: 'overlay: switch02'
          peer-as: '4200000002'
        - name: 172.16.50.204
          description: 'overlay: switch03'
          peer-as: '4200000003'
        - name: 172.16.50.61
          description: 'overlay: switch04'
          peer-as: '4200000004'
        - name: 172.16.50.49
          description: 'overlay: switch05'
          peer-as: '4200000005'
        - name: 10.200.80.195
          description: 'overlay: switch06'
          peer-as: '4200000006'
        - name: 172.16.50.199
          description: 'overlay: switch07'
          peer-as: '4200000007'
```

**Extract peer names** using `addvars` inline:

```bash
ssh switch01.example.net \
  "show configuration protocols bgp group overlay | display json" \
  | junoscfg convert -i json -e yaml \
  | junoscfg edityaml addvars \
      --path "configuration.protocols.bgp.group[*].neighbor[*]" \
      --set "_ansible_bgp_peername=regex_extract(description, 'overlay: (\\w+)')"
```

**Output** (each neighbor is enriched with `_ansible_bgp_peername`):

```yaml
configuration:
  '@':
    junos:commit-seconds: '1711929600'
    junos:commit-localtime: 2024-04-01 12:00:00 UTC
    junos:commit-user: admin
  protocols:
    bgp:
      group:
      - name: overlay
        local-address: 192.168.100.2
        local-as:
          as-number: '4200000001'
        neighbor:
        - name: 192.168.100.15
          description: 'overlay: switch02'
          peer-as: '4200000002'
          _ansible_bgp_peername: switch02
        - name: 172.16.50.204
          description: 'overlay: switch03'
          peer-as: '4200000003'
          _ansible_bgp_peername: switch03
        - name: 172.16.50.61
          description: 'overlay: switch04'
          peer-as: '4200000004'
          _ansible_bgp_peername: switch04
        - name: 172.16.50.49
          description: 'overlay: switch05'
          peer-as: '4200000005'
          _ansible_bgp_peername: switch05
        - name: 10.200.80.195
          description: 'overlay: switch06'
          peer-as: '4200000006'
          _ansible_bgp_peername: switch06
        - name: 172.16.50.199
          description: 'overlay: switch07'
          peer-as: '4200000007'
          _ansible_bgp_peername: switch07
```

**Adding multiple vars** — extract the peer name and also copy the neighbor IP and mark as managed:

```bash
ssh switch01.example.net \
  "show configuration protocols bgp group overlay | display json" \
  | junoscfg convert -i json -e yaml \
  | junoscfg edityaml addvars \
      --path "configuration.protocols.bgp.group[*].neighbor[*]" \
      --set "_ansible_bgp_peername=regex_extract(description, 'overlay: (\\w+)')" \
      --set "_ansible_peer_ip=copy(name)" \
      --set "_ansible_managed=static(true)"
```

**Using a rule file** for the same pipeline — useful when transforms are complex or reused across multiple switches:

```yaml
# bgp-overlay-rules.yaml
rules:
  - path: "configuration.protocols.bgp.group[*].neighbor[*]"
    transforms:
      - type: regex_extract
        source: description
        pattern: "overlay: (\\w+)"
        target: _ansible_bgp_peername
      - type: copy
        source: name
        target: _ansible_peer_ip
      - type: static
        target: _ansible_managed
        value: true
```

```bash
ssh switch01.example.net \
  "show configuration protocols bgp group overlay | display json" \
  | junoscfg convert -i json -e yaml \
  | junoscfg edityaml addvars -r bgp-overlay-rules.yaml
```

### Convert-and-Transform Pipeline

Convert from JSON and add metadata in one pipeline:

```bash
junoscfg -i json -e yaml router-config.json | \
  junoscfg edityaml addvars \
    --path "configuration.system" \
    --set "_managed=static(true)" \
    --set "_env=production" > enriched.yaml
```

### Combine Rule File with Inline Overrides

Use a shared rule file for standard transforms, and add one-off inline transforms per invocation:

```bash
# Standard rules in file, plus a one-off environment tag
junoscfg edityaml addvars -r standard-rules.yaml \
  --path "configuration.system" \
  --set "_datacenter=dc1" \
  config.yaml

# Same rules, different datacenter
junoscfg edityaml addvars -r standard-rules.yaml \
  --path "configuration.system" \
  --set "_datacenter=dc2" \
  config.yaml
```

## ansibilize: Extract Values for Ansible Lazy Loading

The `ansibilize` subcommand splits a YAML config into Ansible-ready documents:

**Literal mode (`-p`)** — Outputs two documents:

1. **host_vars** — A flat map of variable names to their original values. These go into Ansible `host_vars/` files so each host can override them.
2. **group_vars** — The original YAML structure with selected leaf values replaced by `{{ variable_name }}` Jinja2 references. This goes into Ansible `group_vars/` as a shared template.

**Offset mode (`-P`)** — For multi-router deployments where addresses follow an offset pattern (Router1 = base, Router2 = base+1, etc.). Outputs three documents:

1. **host_vars** — Contains `base_address_offset: 0` (override per host with `1`, `2`, etc.)
2. **offset_vars** — Computed address variables using Jinja2 offset expressions (e.g. `{{ '10.0.2.64' | ansible.utils.ipmath(base_address_offset) }}/31`)
3. **group_vars** — Template YAML with `{{ variable_name }}` references

Offset mode auto-detects value types and generates appropriate expressions:

| Value type | Example input | Generated expression |
|-----------|---------------|---------------------|
| IPv4/IPv6 address | `10.0.2.64/31` | `{{ '10.0.2.64' \| ansible.utils.ipmath(offset_var) }}/31` |
| MAC address | `00:11:22:33:44:a5` | `00:11:22:33:44:{{ '%02x' % (165 + offset_var) }}` |
| Trailing digits | `router04` | `router{{ '%02d' % (4 + offset_var) }}` |

IP offset expressions use the `ansible.utils.ipmath` filter (requires `ansible-galaxy collection install ansible.utils`).

### CLI Usage

```bash
# Literal extraction (-p): values go directly into host_vars
junoscfg edityaml ansibilize \
  -p "junos_addr:configuration.interfaces.interface[*].unit[*].family.*.address[*].name" \
  config.yaml

# Multiple prefix:path pairs in one invocation:
junoscfg edityaml ansibilize \
  -p "junos_addr:configuration.interfaces.interface[*].unit[*].family.*.address[*].name" \
  -p "bgp_peer:configuration.protocols.bgp.group[*].neighbor[*].name" \
  config.yaml

# Offset extraction (-P): generates ipmath/offset expressions
junoscfg edityaml ansibilize \
  -P "addr:interfaces.interface[*].unit[*].family.*.address[*].name" \
  config.yaml

# Custom offset variable name (default: base_address_offset)
junoscfg edityaml ansibilize \
  --offset-var my_offset \
  -P "addr:interfaces.interface[*].unit[*].family.*.address[*].name" \
  config.yaml

# Mix literal and offset in one invocation:
junoscfg edityaml ansibilize \
  -p "host:system.host-name" \
  -P "addr:interfaces.interface[*].unit[*].family.*.address[*].name" \
  config.yaml
```

| Option | Required | Description |
|--------|----------|-------------|
| `-p`/`--prefix_path PREFIX:PATH` | no* | Repeatable prefix:path pair for literal extraction (split on first `:`) |
| `-P`/`--offset-prefix-path PREFIX:PATH` | no* | Repeatable prefix:path pair for offset-mode extraction |
| `--offset-var NAME` | no | Name of the per-host offset variable (default: `base_address_offset`) |
| `--root PATTERN` | no | Top-level key glob to descend into (repeatable). Overrides auto-descend. |
| `FILE` | no | Input YAML file (reads from stdin if omitted) |

\* At least one of `-p` or `-P` is required.

Each `-p` or `-P` value is `prefix:path`. The last segment of the path is the leaf key — the scalar value to extract and templatize. Everything before it is the navigation path.

With `-p` only: output is two YAML documents (host_vars, group_vars).
With `-P`: output is three YAML documents (host_vars, offset_vars, group_vars).

Multiple `-p` and `-P` options can be mixed freely. Literal extractions go to host_vars; offset extractions go to offset_vars.

**Jinja2 quoting**: Ansible requires values starting with `{` to be quoted in YAML, otherwise the YAML parser interprets them as flow mappings ([Ansible YAML Syntax](https://docs.ansible.com/ansible/latest/reference_appendices/YAMLSyntax.html)). The `ansibilize` output correctly quotes all `{{ }}` references (e.g. `'{{ junos_addr_xe_0_0_0_100_inet_0 }}'`), so the group_vars file is both valid YAML and valid Ansible.

### Variable Name Generation

Variable names are built from the `--prefix` plus a discriminator for each wildcard segment in the path. Special characters are replaced with underscores and lowercased.

| Wildcard type | Discriminator source | Example |
|---------------|---------------------|---------|
| `foo[*]` (list) | `item["name"]` | `xe-0/0/0` becomes `xe_0_0_0` |
| `*` (dict) | The dict key itself | `inet`, `inet6` |
| Terminal `foo[*]` when leaf is `name` | List index | `0`, `1`, `2` |

The terminal list rule applies when the leaf you're extracting IS the `name` field of the last list — since `name` is the value being extracted (not an identifier), the list index is used instead.

### Worked Example: Interface Addresses

**Input YAML** (`config.yaml`):

```yaml
configuration:
  interfaces:
    interface:
      - name: xe-0/0/0
        unit:
          - name: "100"
            family:
              inet:
                address:
                  - name: 10.0.0.1/30
              inet6:
                address:
                  - name: 2001:db8::1/64
```

**Command**:

```bash
junoscfg edityaml ansibilize \
  -p "junos_interface_address:configuration.interfaces.interface[*].unit[*].family.*.address[*].name" \
  config.yaml
```

**Output** (two YAML documents):

```yaml
junos_interface_address_xe_0_0_0_100_inet_0: 10.0.0.1/30
junos_interface_address_xe_0_0_0_100_inet6_0: 2001:db8::1/64
---
configuration:
  interfaces:
    interface:
      - name: xe-0/0/0
        unit:
          - name: "100"
            family:
              inet:
                address:
                  - name: '{{ junos_interface_address_xe_0_0_0_100_inet_0 }}'
              inet6:
                address:
                  - name: '{{ junos_interface_address_xe_0_0_0_100_inet6_0 }}'
```

The first document is your `host_vars` — copy it to `host_vars/router1.yml` and customize the IP addresses per host. The second document is your `group_vars` template — shared across all hosts in the group.

### Worked Example: BGP Neighbor Descriptions

Extract per-host BGP neighbor descriptions while keeping the rest of the config as a shared template:

**Command**:

```bash
junoscfg edityaml ansibilize \
  -p "bgp_desc:configuration.protocols.bgp.group[*].neighbor[*].description" \
  config.yaml
```

With input containing two BGP neighbors `10.0.0.1` and `10.0.0.2`, this produces:

```yaml
bgp_desc_10_0_0_1: "overlay: spine1"
bgp_desc_10_0_0_2: "overlay: spine2"
---
configuration:
  protocols:
    bgp:
      group:
        - name: overlay
          neighbor:
            - name: 10.0.0.1
              description: '{{ bgp_desc_10_0_0_1 }}'
            - name: 10.0.0.2
              description: '{{ bgp_desc_10_0_0_2 }}'
```

Note that the leaf is `description` (not `name`), so the `name` field (`10.0.0.1`) is used as the discriminator for each neighbor (not the list index), because `name` is not the field being extracted.

### Worked Example: System Hostname

Extract the hostname so each router can override it:

```bash
junoscfg edityaml ansibilize \
  -p "junos_hostname:configuration.system.host-name" \
  config.yaml
```

**Input**:
```yaml
configuration:
  system:
    host-name: router1
    domain-name: example.com
```

**Output**:
```yaml
junos_hostname: router1
---
configuration:
  system:
    host-name: '{{ junos_hostname }}'
    domain-name: example.com
```

Note: when the path has no wildcards, the variable name is just the prefix itself — no discriminator suffix is needed.

### Worked Example: BGP Neighbor Addresses

Extract the neighbor IP addresses so each router can have different peers:

```bash
junoscfg edityaml ansibilize \
  -p "bgp_peer:configuration.protocols.bgp.group[*].neighbor[*].name" \
  config.yaml
```

**Input**:
```yaml
configuration:
  protocols:
    bgp:
      group:
        - name: overlay
          neighbor:
            - name: 10.0.0.1
              description: "overlay: spine1"
            - name: 10.0.0.2
              description: "overlay: spine2"
```

**Output**:
```yaml
bgp_peer_overlay_0: 10.0.0.1
bgp_peer_overlay_1: 10.0.0.2
---
configuration:
  protocols:
    bgp:
      group:
        - name: overlay
          neighbor:
            - name: '{{ bgp_peer_overlay_0 }}'
              description: "overlay: spine1"
            - name: '{{ bgp_peer_overlay_1 }}'
              description: "overlay: spine2"
```

Here the leaf `name` is the value being extracted on the terminal `neighbor[*]` list, so the discriminator uses the list index (`0`, `1`) rather than the name itself. The non-terminal `group[*]` uses `item["name"]` → `overlay`.

### Worked Example: OSPF Area Interface Costs

Extract per-interface OSPF costs:

```bash
junoscfg edityaml ansibilize \
  -p "ospf_cost:configuration.protocols.ospf.area[*].interface[*].metric" \
  config.yaml
```

**Input**:
```yaml
configuration:
  protocols:
    ospf:
      area:
        - name: 0.0.0.0
          interface:
            - name: xe-0/0/0.0
              metric: 100
            - name: xe-0/0/1.0
              metric: 200
```

**Output**:
```yaml
ospf_cost_0_0_0_0_xe_0_0_0_0: 100
ospf_cost_0_0_0_0_xe_0_0_1_0: 200
---
configuration:
  protocols:
    ospf:
      area:
        - name: 0.0.0.0
          interface:
            - name: xe-0/0/0.0
              metric: '{{ ospf_cost_0_0_0_0_xe_0_0_0_0 }}'
            - name: xe-0/0/1.0
              metric: '{{ ospf_cost_0_0_0_0_xe_0_0_1_0 }}'
```

Since the leaf `metric` is not `name`, the discriminator for both `area[*]` and `interface[*]` uses `item["name"]`: `0.0.0.0` → `0_0_0_0`, `xe-0/0/0.0` → `xe_0_0_0_0`.

### Worked Example: Reading from stdin

Pipe converted output directly into ansibilize:

```bash
# Convert JSON config and ansibilize in one pipeline
junoscfg -i json -e yaml config.json | \
  junoscfg edityaml ansibilize \
    -p "junos_hostname:configuration.system.host-name"

# Convert from structured format
junoscfg -i structured -e yaml config.conf | \
  junoscfg edityaml ansibilize \
    -p "junos_addr:configuration.interfaces.interface[*].unit[*].family.*.address[*].name"
```

### Worked Example: Addvars Then Ansibilize Pipeline

First enrich the YAML with addvars, then ansibilize the enriched output:

```bash
# Step 1: Add BGP peer names from descriptions
junoscfg edityaml addvars \
  --path "configuration.protocols.bgp.group[*].neighbor[*]" \
  --set "_peer_role=regex_extract(description, 'overlay: (\\w+)')" \
  config.yaml | \
# Step 2: Ansibilize the enriched output to templatize addresses
  junoscfg edityaml ansibilize \
    -p "junos_addr:configuration.interfaces.interface[*].unit[*].family.*.address[*].name"
```

### Worked Example: Offset Mode — Multi-Router IP Addresses

Use `-P` when multiple routers share the same config template but with offset addresses (Router1 = base, Router2 = base+1, etc.):

**Input YAML** (`config.yaml`):

```yaml
configuration:
  interfaces:
    interface:
      - name: ge-0/0/0
        unit:
          - name: "0"
            family:
              inet:
                address:
                  - name: 10.0.2.64/31
              inet6:
                address:
                  - name: "2001:db8:44:11::1:2e/112"
```

**Command**:

```bash
junoscfg edityaml ansibilize \
  -P "addr:interfaces.interface[*].unit[*].family.*.address[*].name" \
  config.yaml
```

**Output** (three YAML documents):

```yaml
base_address_offset: 0
---
addr_ge_0_0_0_0_inet6_0: '{{ ''2001:db8:44:11::1:2e'' | ansible.utils.ipmath(base_address_offset) }}/112'
addr_ge_0_0_0_0_inet_0: '{{ ''10.0.2.64'' | ansible.utils.ipmath(base_address_offset) }}/31'
---
configuration:
  interfaces:
    interface:
    - name: ge-0/0/0
      unit:
      - name: '0'
        family:
          inet:
            address:
            - name: '{{ addr_ge_0_0_0_0_inet_0 }}'
          inet6:
            address:
            - name: '{{ addr_ge_0_0_0_0_inet6_0 }}'
```

For Router1, set `base_address_offset: 0` in host_vars. For Router2, set `base_address_offset: 1`. The `ipmath` filter handles octet overflow correctly (e.g. `10.0.0.255 + 1 → 10.0.1.0`).

### Worked Example: Mixed Literal and Offset

Extract the hostname as a literal per-host value, and addresses as offset expressions:

```bash
junoscfg edityaml ansibilize \
  -p "host:system.host-name" \
  -P "addr:interfaces.interface[*].unit[*].family.*.address[*].name" \
  config.yaml
```

The hostname goes into host_vars as a plain value; the addresses become offset expressions in the second document.

### Using the Output with Ansible

A typical workflow:

```bash
# 1. Convert Junos config to YAML
junoscfg -i json -e yaml config.json > config.yaml

# 2. Split into host_vars and group_vars
junoscfg edityaml ansibilize \
  -p "junos_addr:configuration.interfaces.interface[*].unit[*].family.*.address[*].name" \
  config.yaml > output.yaml

# 3. Manually split the two documents into Ansible directories:
#    - First document  -> host_vars/router1.yml
#    - Second document -> group_vars/junos_routers.yml

# 4. Customize host_vars per router:
#    host_vars/router1.yml:
#      junos_addr_xe_0_0_0_100_inet_0: 10.0.0.1/30
#    host_vars/router2.yml:
#      junos_addr_xe_0_0_0_100_inet_0: 10.0.0.5/30

# 5. Or use multiple -p to ansibilize different leaf types in one pass:
junoscfg edityaml ansibilize \
  -p "junos_hostname:configuration.system.host-name" \
  -p "junos_bgp_peer:configuration.protocols.bgp.group[*].neighbor[*].name" \
  config.yaml
```

## Error Handling

- **Missing source keys**: Silently skipped (no error). If a `regex_extract` or `copy` references a key that doesn't exist on a node, that transform is skipped for that node.
- **No regex match**: If `regex_extract` pattern doesn't match, the target key is not created.
- **Missing template keys**: If a `template` references a key not present on the node, the transform is skipped.
- **Bad YAML in rule file**: Raises a parse error with details.
- **Missing `rules` key**: Raises a validation error.
- **Non-dict list items**: When `[*]` iterates a list, non-dict items (strings, numbers) are silently skipped.
- **Missing leaf key** (ansibilize): If a matched node doesn't contain the leaf key (last segment of `--path`), that node is skipped — no variable is generated for it.

## Python API

### addvars

```python
from junoscfg.edityaml import apply_rules

data = {"configuration": {"system": {"host-name": "r1"}}}
ruleset = {
    "rules": [
        {
            "path": "configuration.system",
            "transforms": [
                {"type": "static", "target": "_managed", "value": True},
            ],
        }
    ]
}

result = apply_rules(data, ruleset)
# result["configuration"]["system"]["_managed"] == True
# Original data is not mutated
```

### ansibilize

```python
from junoscfg.edityaml.ansibilize import ansibilize, ansibilize_multi, format_output

data = {
    "configuration": {
        "system": {"host-name": "router1"},
        "interfaces": {
            "interface": [
                {
                    "name": "xe-0/0/0",
                    "unit": [
                        {
                            "name": "100",
                            "family": {
                                "inet": {
                                    "address": [{"name": "10.0.0.1/30"}]
                                }
                            },
                        }
                    ],
                }
            ]
        }
    }
}

# Single path (convenience wrapper):
host_vars, group_vars = ansibilize(
    data,
    path="configuration.interfaces.interface[*].unit[*].family.*.address[*].name",
    prefix="junos_addr",
)

# Multiple paths in one pass:
host_vars, group_vars = ansibilize_multi(
    data,
    [
        ("junos_addr", "configuration.interfaces.interface[*].unit[*].family.*.address[*].name"),
        ("junos_hostname", "configuration.system.host-name"),
    ],
)

# host_vars contains variables from all paths
# group_vars has all leaves replaced with Jinja2 references
# Original data is not mutated

# Format as two YAML documents:
print(format_output(host_vars, group_vars))
```

### ansibilize with offset

```python
from junoscfg.edityaml.ansibilize import ansibilize_with_offset, format_output_with_offset

data = {
    "interfaces": {
        "interface": [
            {
                "name": "ge-0/0/0",
                "unit": [
                    {
                        "name": "0",
                        "family": {
                            "inet": {"address": [{"name": "10.0.2.64/31"}]}
                        },
                    }
                ],
            }
        ]
    }
}

# Offset mode: generates ipmath expressions for IP addresses
host_vars, offset_vars, template = ansibilize_with_offset(
    data,
    literal_pairs=[],
    offset_pairs=[("addr", "interfaces.interface[*].unit[*].family.*.address[*].name")],
    offset_var="base_address_offset",  # default
)

# host_vars: {"base_address_offset": 0}
# offset_vars: {"addr_ge_0_0_0_0_inet_0": "{{ '10.0.2.64' | ansible.utils.ipmath(...) }}/31"}
# template: original structure with {{ addr_ge_0_0_0_0_inet_0 }} references

# Mix literal and offset extractions:
host_vars, offset_vars, template = ansibilize_with_offset(
    data,
    literal_pairs=[("host", "system.host-name")],
    offset_pairs=[("addr", "interfaces.interface[*].unit[*].family.*.address[*].name")],
)

# Format as three YAML documents:
print(format_output_with_offset(host_vars, offset_vars, template))
```
