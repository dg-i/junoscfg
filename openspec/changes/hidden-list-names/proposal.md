## Why

Device captures hide XML list names in display set, but current conversion leaks them or retains valid statements unplaced. The same configuration must have one keyed IR across its representations.

## What Changes

- Repair DEV-10..14 / DEV-V2 hidden shapes / DEV-V4 for the proven route-filter-list rf_list, nested DHCP server-group/address, predefined-variable-defaults other-variables, bridge-domains domain, and dynamic-tunnels dynamic-tunnel shapes.
- **BREAKING**: consumer and CLI conversion produces device-shaped keyed arrays and omits hidden XML names. Preserve address-plus-choice keys and prefer real keyword children over positional keys.
- Derive hidden-list behaviour from schema structure at the owning layer; measure current L+nk slots and preserve ordinary keyworded, leaf, unknown and unkeyed models. Retire named t/tk rules only if equivalence and blast-radius evidence permit it.
- No new overrides, resources, parameters, environment reads or dependencies.

## Capabilities

### New Capabilities

- `conversion/hidden-list-names`: device-backed hidden lists retain declared entry keys across readers and writers.
- `schema-pipeline/hidden-list-hints`: conversion hints recognize structurally keyed hidden lists without broadening unrelated models.

### Modified Capabilities

None; existing entry-key and conversion-hint requirements remain baseline.

## Non-goals

Daemon-process without capture; NEW-R15 LRF single-choice name spelling (current node lacks L+nk); #13 numeric-alias/normalization, #14 meta-walker, #24 deferred features; P1/P6/P7/P8 guesses; schema release-gap repairs.

## Impact

Future production paths overlap #11 and remain parked. Tests own a new convert unit file; no shared catalogue edits. Public product generation, known differences and final full schemas require root sequencing. Device evidence: committed synthetic vMX/QFX junoscfg-oracle set/JSON/XML, with vMX bridge domains and predefined defaults; QFX platform rejection is not global invalidity.
