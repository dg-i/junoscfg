## Why

The validators reject what the device printed: on the committed captures (QFX5120 25.2R2, vMX 23.2R2) `-v` and field validation report statements Juniper's XSD leaves out (the device wraps them in `<undocumented>`), JSON names the Ruby-inherited renames replace (`end-range`, `ieee-802.3ad`), `protect` lines, `$junos-` variables and an `isis-instance` list; JSON messages reprint whole subtrees, secrets included. Device output is the oracle, and no test ran validation over the captures.

## What Changes

- One naming rule: a fix that renames an element records the element name the device writes in XML and JSON on the node (structure tree key `x`). The set grammar and set/structured I/O use the CLI keyword; the JSON schema, the JSON/yaml-new writer and every reader of XML, JSON, yaml-new and yaml use the recorded name; the IR holds the tree's key whatever the reader (one IR). `KEY_ALIASES`/`resolve_key_alias`, the hand-kept copy, are removed; the unused `XsdFix.applies_to` goes with them. Group E gains `hello-padding-type` → `hello-padding` (isis interface).
- Group D models the undocumented statements committed captures show, shaped as their XML: login user `shell`; grpc `clear-text port`, `skip-authentication`; ddos-protection `autoconf aggregate bandwidth|burst`; inet6 labeled-unicast `per-prefix-label`; dhcp-local-server `stale-timer`, `no-stale-timer-refresh`.
- Keyed singleton entries: the path list gains `isis-instance` and the routing-instance, logical-system and tenant copies; no general rule (P).
- The set validator reads every verb conversion reads (`protect`, `activate`, `delete`, `deactivate`) and prints whole lines; field validation leaves `$junos-` variables unchecked; JSON-schema messages name the path and the offending keys, never the instance.
- Artifacts regenerated from the 25.2R2 dump; fix counts updated in the developer guide and schema internals.
- Tests: a device-capture validation law over every capture and rendering against one recorded expected-findings file (replacing `UNPLACED_IN_THE_EXAMPLE` and its strict xfails); unit rows per rule; records shrunk through their tools.
- Not a break (`.openspec.yaml`): false errors disappear, JSON output moves to the device's spelling; patch.

## Capabilities

### New Capabilities

- `validation/device-captures`: every capture validates with only recorded findings.

### Modified Capabilities

- `schema-pipeline/conversion-hints`: renames record the XML/JSON name.
- `validation/set-command-validation`: the verbs, whole lines.
- `validation/junos-json-yaml`: XSD names, path-and-key messages.
- `conversion/junos-json-yaml`: the yaml-new reader, like the JSON reader, loads the tree.

## Non-goals

`-v` on XML (no XSD ships); hold-time mandatory warning (device question); statements no committed capture shows (`chassis dump-on-panic`, grpc `clear-text address`); the rest of the `xml-element-name-leak` class unless one rule covers it; no-op fixes.
