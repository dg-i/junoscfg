## Why

A QFX5120 (25.2R2-S1.5) probe on 2026-10-16 settled eight open device questions. It shows that junoscfg's set validator accepts verb lines the device refuses, that `--path` output loses or misplaces tags the device keeps, and that five undocumented statements the device takes are rejected.

## What Changes

- Evidence: a sanitized record of the probe in `tests/data/device/probes/` (statements, responses and renderings; no host, user or time). BACKLOG entries carry it, with status and a link here.
- Set validation (VERB-PREFIX-001, A2): a non-`set` verb line is valid only when it names a statement the device can tag: a container, a leaf before its value, or a list entry after its full key. A list's keyword without its name (`protect policy-options policy-statement`), a leaf's value, one value of a leaf-list (`deactivate ... community 64496:2`) and a stop inside an entry's key are invalid. The set reader's decision of what a verb line names moves to `junoscfg.display`, read only; the reader and the validator share it, and the validator reads the structure tree beside its grammar (the grammar alone cannot tell a list's name from a leaf's value).
- Absolute `--path` (ANCESTOR-TAGS-001): the selection keeps every annotation along its path, so a leaf under `deactivate system` is written inside the deactivated `system`, in every format, as the device prints it (C3).
- Relative `--path` (RELATIVE-TAGS-001, ruling 2): a tag at or above the path that the output cannot write is dropped with one note, in every writer; never a bare verb. The set writer gains diagnostics.
- Leaf-list value tags (LEAF-LIST-VALUE-TAGS-001): set and structured output note a per-value tag they drop.
- Schema (UNDOCUMENTED-001): `_UNDOCUMENTED` gains grpc `clear-text address`, `system dump-on-panic`, `debugger-on-break`, `debugger-on-panic` and `chassis dump-on-panic`; artifacts and records regenerated. The number of XSD fixes stays 44.
- Records: HOLD-TIME-001 closed (the device refuses `down` alone at commit; the expected finding is reclassified); RENAME-EVIDENCE-001 closed for five renames, NAT open; JSON-KEYWORD-ALIAS-001 closed: the alias is permanent, no longer deprecated (ruling 1).
- Not a break (`.openspec.yaml`): `-v` refuses only what the device or the reader refuses; output changes only where it loaded with another meaning or not at all.

## Capabilities

### New Capabilities
- `conversion/selection-tags`: a selection's tag rules, moved from `conversion/path-filtering` (modified) and widened.
### Modified Capabilities
- `validation/set-command-validation`: what a verb line may name; `conversion/writers`: a per-value leaf-list tag is noted.
- `validation/device-captures`: probe statements modelled; `schema-pipeline/conversion-hints`: the alias is permanent.

## Non-goals

The QFX refusing set `ether-options speed 1g` (platform-unsupported, the XSD lists it); bracket lists in set input; whether a device loads per-value tags from JSON; a `delete` of one leaf-list value (no device evidence; the rule follows the reader); the set reader's whole-list tag for a bare list keyword (left as is); comments in relative output; the NAT rename.

## Completion

Every item above fixed or recorded; every device capture's verb line still validates; the device checks and the before/after comparison show only explained differences.
