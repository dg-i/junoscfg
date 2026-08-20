# Unused-Object Audit

`junoscfg audit unused` finds configuration objects — policy statements,
prefix lists, firewall filters, config groups, ... — that are defined but
never referenced, and emits them as paths or ready-to-paste cleanup
scripts. It works on the parsed configuration (the IR), so any input
format junoscfg supports (set, structured, JSON, YAML, XML) can be
audited.

Working on the IR instead of `display set` text with word-boundary regex
counting — the approach used by typical on-box op scripts — fixes that
approach's known weaknesses:

- **Name collisions**: a community and a prefix-list may share a name;
  regex counting sees one name, the audit sees two namespaces
  (see [classification rules](#classification-rules) below).
- **Comments**: names in `annotate` comments never count as references.
- **Quoting**: quoted names and policy expressions such as
  `"( POL-A && ! POL-B )"` are parsed structurally — the names inside the
  expression count as references, and `POL-B` never accidentally
  "matches" an unrelated `POL-B-OLD`.

Findings are suggestions requiring human review — see
[Limitations](#limitations).

## Quick Start

Given `config.set`:

```
set policy-options prefix-list CUSTOMER-ROUTES 10.0.0.0/8
set policy-options prefix-list OLD-PEERS 192.168.0.0/16
set policy-options policy-statement EXPORT-CUSTOMERS term customers from prefix-list CUSTOMER-ROUTES
set policy-options policy-statement EXPORT-CUSTOMERS term customers then accept
set policy-options policy-statement LEGACY-EXPORT term reject-all then reject
set protocols bgp group PEERS export EXPORT-CUSTOMERS
set firewall family inet filter PROTECT-RE term ssh then accept
set groups NODE-DEFAULTS system host-name router1
```

List everything that is defined but never referenced:

```console
$ junoscfg audit unused config.set
policy-options policy-statement LEGACY-EXPORT
policy-options prefix-list OLD-PEERS
firewall family inet filter PROTECT-RE
groups NODE-DEFAULTS
```

Generate a delete script with review comments:

```console
$ junoscfg audit unused -o delete-script-verbose config.set
# unused: policy-statement LEGACY-EXPORT
delete policy-options policy-statement LEGACY-EXPORT

# unused: prefix-list OLD-PEERS
delete policy-options prefix-list OLD-PEERS

# unused: firewall-filter PROTECT-RE
delete firewall family inet filter PROTECT-RE

# unused: config-group NODE-DEFAULTS
delete groups NODE-DEFAULTS

# summary: 6 definitions checked, 4 unused, 0 probably-unused
```

Restrict the check to certain types and names:

```console
$ junoscfg audit unused --types prefix-list --match '^OLD-' -o show-script config.set
show policy-options prefix-list OLD-PEERS
```

The same audit is available from Python as `junoscfg.audit.find_unused`:

```python
from junoscfg.audit import find_unused
from junoscfg.convert import to_dict

ir = to_dict(source, "set")
result = find_unused(ir, match="^OLD-")
for finding in result.findings:
    print(finding.confidence, " ".join(finding.path))
```

## Concepts

### Definitions and References

The audit walks the configuration tree guided by the bundled schema and
collects every name-like string occurrence. A [type registry](#the-type-registry)
declares, per object type, where objects are **defined** (e.g.
`policy-options policy-statement`) and where their names may legitimately
appear as **references** (e.g. any import/export leaf typed as a policy
expression). An object with a definition but no reference is a finding.

Two scoping rules matter:

- **Definitions** inside `groups`, `logical-systems`, and
  `routing-instances` are audited too; emitted commands use the original
  full path (e.g. `delete groups NODE-DEFAULTS policy-options ...`).
- **References** count anywhere in the configuration — including inside
  config groups that are never applied. Group inheritance is not resolved
  in v1, so a reference inside a never-applied group still marks the
  target object as used (a false "used" at worst — the safe direction).

Occurrences inside an object's own definition subtree are
self-references and never count as usage. There is also no transitive
analysis: a reference from an object that is itself unused still counts,
so after deleting findings, re-run the audit to surface the next layer.

### Classification Rules

For every occurrence of an object's name outside its own definition, the
engine classifies the position:

| Rule | Position of the occurrence | Classification |
|------|----------------------------|----------------|
| (a) | Reference position of the object's **own** type | Real reference — object is used |
| (b) | Position unambiguously owned by **other** types' namespaces only | Name collision — not a reference |
| (c) | Definition of a same-named object of the **same** type at another path | Not a reference — finding flagged `duplicate definition` |
| (d) | **Unknown** position (owned by no registry namespace) | Conservatively a potential reference |

Rule (d) is the **safety property** of the whole feature: an incomplete
registry may reduce precision, but it can never produce a confident
delete suggestion for an object that is actually referenced. Rule (b) is
only applied when the position is unambiguously owned by another
namespace; when in doubt, the occurrence falls through to (d).

### Confidence Levels

| Confidence | Meaning | In delete/deactivate scripts |
|------------|---------|------------------------------|
| `unused` | No potential reference at all: no occurrence outside the definition, or all occurrences classified as (b)/(c) | Yes |
| `probably-unused` | No known reference, but occurrences at unknown positions (d) exist | Only with `--include-probably-unused` |

Operationally: `unused` findings are safe delete candidates as far as
the configuration itself can tell. `probably-unused` findings need a
human decision — the verbose output styles list every unresolved
occurrence (path and value) so you can check whether it is a real
reference. If none of them is, the object is unused; if one is, consider
[extending the registry](#custom-registries) so the position is known
next time.

## Output Styles

Five styles (`pathname`, `delete-script`, `show-script`,
`show-configuration-script`, `deactivate-script`), each with a
`-verbose` variant. Non-verbose output contains only command/path lines
(pipe- and paste-clean); verbose adds a comment block per finding and a
summary line. See the [CLI reference](cli.md#audit-unused) for the
option and style tables.

A verbose run with a probably-unused finding — `OLD-PEERS` is only
mentioned inside an `apply-macro`, which the audit cannot interpret:

```console
$ cat macro.set
set policy-options prefix-list CUSTOMER-ROUTES 10.0.0.0/8
set policy-options prefix-list OLD-PEERS 192.168.0.0/16
set policy-options policy-statement EXPORT-CUSTOMERS term customers from prefix-list CUSTOMER-ROUTES
set policy-options policy-statement EXPORT-CUSTOMERS term customers then accept
set protocols bgp group PEERS export EXPORT-CUSTOMERS
set routing-options apply-macro provisioning peer-list OLD-PEERS

$ junoscfg audit unused -o pathname-verbose macro.set
# probably-unused: prefix-list OLD-PEERS
#   unresolved: routing-options apply-macro data value = "OLD-PEERS"
policy-options prefix-list OLD-PEERS

# summary: 3 definitions checked, 0 unused, 1 probably-unused
```

In `delete-script` and `deactivate-script` output this finding would be
omitted (shown only as a comment in the verbose variant) unless
`--include-probably-unused` is given.

## The Type Registry

Which object types exist, where they are defined, and where they are
referenced is data, not code: a YAML registry bundled at
`src/junoscfg/audit/data/unused-types.yaml` and validated at load time
(a broken registry exits with code 3 and a clear error message).

### Format Reference

```yaml
version: 1
types:                    # insertion order defines report output order
  policy-statement:
    source: curated       # curated | generated
    definition:           # path patterns where objects of the type are DEFINED
      - policy-options policy-statement
    references:           # where names of the type may legitimately appear
      paths: []           # path patterns ending at the reference position
      schema-types: []    # schema `tr` type names marking reference positions
    implicit: []          # name globs that are never reported as unused
    report: true          # false = namespace-only anchor, produces no findings
```

| Field | Required | Meaning |
|-------|----------|---------|
| `version` | yes | Registry format version; must be `1` |
| `types` | yes | Non-empty mapping of type name to entry; insertion order defines finding order |
| `source` | yes | `curated` (hand-written) or `generated` (emitted by tooling) — see [the planned YANG generator](#planned-yang-derived-registry-generation) |
| `definition` | yes | Non-empty list of path patterns where objects of this type are defined (the matched list's entry key is the object name) |
| `references.paths` | no | Path patterns where a name of this type may appear as a reference |
| `references.schema-types` | no | Schema type-reference (`tr`) names marking reference positions |
| `implicit` | no | Name globs (fnmatch) that are implicitly used and never reported — e.g. `re0`, `node*` for config groups |
| `report` | no (default `true`) | `false` marks a namespace-only entry that anchors collision classification (rules b/c) but never produces findings itself |

A reportable type must declare at least one reference path or
schema-type — otherwise every object of the type would be reported as
unused. A reference position may be a leaf (value = object name), a
leaf-list, or a named list whose entry key is the object name.

### Path-Pattern Semantics

Path patterns are space-separated **schema keys**: no instance names
(`policy-options policy-statement`, not `... policy-statement FOO`), and
transparent wrapper keywords included. Each segment is matched with
fnmatch globs, so `firewall family * filter` covers every address
family.

Patterns are matched **tail-anchored** against the schema-key path of an
occurrence: the pattern matches when the occurrence's path *ends* with
it. This is what makes patterns relative — `policy-options
policy-statement` also matches inside `groups group ...`,
`logical-systems ...`, and `dynamic-profiles ...` automatically. Do not
add prefixed variants.

### The `schema-types` Mechanism

Some reference positions are far too numerous to enumerate as paths:
policy names may appear at every import/export/policy leaf — 7636 leaf
positions in the schema tree. Instead of listing paths, an entry can
name the schema type reference (`tr`) that marks such positions in the
bundled schema tree; any leaf or named list carrying that type is a
reference position. This also enables structural parsing: values at
positions typed `policy-algebra` are parsed as policy expressions
(`( POL-A && ! POL-B )`) and the names inside are extracted — no
substring matching.

### Bundled Types

| Type | Defined at | Referenced from |
|------|-----------|-----------------|
| `policy-statement` | `policy-options policy-statement` | every import/export/policy leaf typed as a policy expression (schema-type `policy-algebra`, expressions parsed) |
| `prefix-list` | `policy-options prefix-list` | `from prefix-list` / `prefix-list-filter` and all firewall/services-filter `source-prefix-list` / `destination-prefix-list` match positions (incl. `ipv6-` variants) |
| `community` | `policy-options community` | `from` / `to` / `then community` |
| `as-path` | `policy-options as-path` | `from` / `to as-path` |
| `as-path-group` | `policy-options as-path-group` | `from` / `to as-path-group` |
| `as-list` | `policy-options as-list` | `from as-path-neighbors` / `as-path-origins` / `as-path-transits` |
| `as-list-group` | `policy-options as-list-group` | same match positions as `as-list` (shared namespace) |
| `condition` | `policy-options condition` | `from condition` |
| `damping` | `policy-options damping` | `then damping` |
| `route-filter-list` | `policy-options route-filter-list` | `from route-filter-list` |
| `firewall-filter` | `firewall filter`, `firewall family * filter` | interface `filter input/output` (both container families such as `inet` and bare-leaf families such as `ethernet-switching`/`mpls`), `filter input-list/output-list/input-chain/output-chain`, `forwarding-options family * filter input/output` |
| `policer` | `firewall policer` | `then policer`, interface `policer input/output/arp` |
| `rib-group` | `routing-options rib-groups` | schema-types `rib-group-type` / `rib-group-inet-type` (e.g. `protocols bgp family ... rib-group`, `routing-options interface-routes rib-group`) |
| `config-group` | `groups group` | `apply-groups` / `apply-groups-except` (a name in `apply-groups-except` counts as used); implicit: `re0`, `re1`, `global`, `node*`, `member*`, `fabric*` |
| `login-class` | `system login class` | `system login user class` |
| `snmp-view` | `snmp view` | `snmp community view`, `read-view` / `write-view` / `notify-view` |

Two namespace-only anchors (`report: false`) round out the registry:
`as-path-group-member` and `as-list-group-member` mark the nested
member namespaces inside `as-path-group` / `as-list-group`, so
same-named top-level objects are classified as collisions (rule b)
rather than falling through to rule (d).

`apply-macro` objects are deliberately not audited: macro bodies are
free-form key/value data consumed by off-box automation, so there is no
schema-backed notion of a "reference" to them. Their *contents* are
still collected as unknown occurrences (rule d), as shown in the
[verbose example](#output-styles) above.

### Custom Registries

Point the audit at your own registry file with `--registry FILE` or the
`JUNOSCFG_AUDIT_REGISTRY` environment variable (the flag wins). A custom
registry **replaces** the bundled one, so start from a copy of
`src/junoscfg/audit/data/unused-types.yaml` when extending it — e.g. to
add SRX object classes or site-specific reference positions that
currently downgrade findings to `probably-unused`.

### Planned: YANG-Derived Registry Generation

A follow-up will generate registry entries from Juniper's
`junos-conf-*.yang` modules ([github.com/Juniper/yang](https://github.com/Juniper/yang),
`conf-with-extensions` variant) by extracting `junos:must` constraints
containing `$$` placeholders and leafs of type `jt:policy-algebra`. The
`source: curated | generated` field exists in registry version 1
precisely so generated entries can later be merged alongside the curated
ones.

## CI Usage

`--fail-on` turns findings into an exit code:

| `--fail-on` | Exit 1 when |
|-------------|-------------|
| `never` (default) | Never — exit 0 even with findings |
| `unused` | At least one strict `unused` finding exists |
| `probably-unused` | At least one finding of either confidence exists |

| Exit code | Meaning |
|-----------|---------|
| 0 | Audit ran; no findings at or above the `--fail-on` threshold |
| 1 | Findings at or above the `--fail-on` threshold exist |
| 2 | Usage error (unknown `--types` value, invalid `--match` regex, bad arguments) |
| 3 | Broken registry or missing schema artifacts |

Sample GitHub Actions step failing the pipeline on strictly unused
objects while printing the review-friendly verbose report:

```yaml
- name: Audit config for unused objects
  run: junoscfg audit unused --fail-on unused -o pathname-verbose configs/router1.conf
```

## Limitations

The audit sees only the configuration it is given. Findings are
**suggestions requiring human review**, never an automatic cleanup:

- **External references are invisible.** References from ephemeral DB
  instances, from op/event/commit scripts, and from external automation
  (provisioning systems, NETCONF tooling) do not appear in the
  configuration and cannot be counted.
- **`apply-macro` contents are opaque.** Macro bodies only produce
  conservative unknown occurrences (rule d, downgrading affected
  findings to `probably-unused`); macro objects themselves are never
  reported.
- **Flat namespace across logical systems and routing instances (v1).**
  A reference inside one logical system marks a same-named object in
  another as used. This can only cause a false "used", never a false
  delete suggestion — the safe direction.
- **Group inheritance is not resolved (v1).** References inside config
  groups count as usage even when the group is never applied — again a
  false "used" at worst.
