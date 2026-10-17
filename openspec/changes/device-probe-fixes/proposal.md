## Why

A QFX5120 (25.2R2-S1.5) probe on 2026-10-16 settled eight open device questions: junoscfg's set validator accepts verb lines the device refuses and refuses lines it takes, `--path` output loses or misplaces tags the device keeps, and five undocumented statements the device takes are rejected.

## What Changes

- Evidence: a sanitized probe record in `tests/data/device/probes/`; the BACKLOG entries carry it, with status and a link here.
- Rule (owner, 2026-10-17): set input is what a device exports. ARCHITECTURE.md section 8 and decision 2026-10-17-set-input-is-a-device-export; the unsupported constructs are listed in `docs/guide/conversion.md` and refused by name. Several statements on one line (`hold-time up 0 down 0`) are read by conversion and named unsupported by `-v`; the widened grammar was measured and not taken.
- Verb lines (VERB-PREFIX-001, A2, S7): one read-only walk in `junoscfg.display` (`meta_target`) decides what a verb line names, for the set reader and for `-v`. A container, a list entry after its whole key, a leaf before its value, or a homogeneous list as a whole is a statement; another list's bare keyword, a leaf's value and a stop inside a key are not, and both refuse them; a tag on `family` itself is invalid for `-v`, and set output drops it with a note (Reviewer A1).
- `--path` (ANCESTOR-TAGS-001, RELATIVE-TAGS-001): absolute selections keep the tags along the path; relative output drops a tag at or above the path with one note in every writer, never a bare verb.
- Per-value leaf-list tags (LEAF-LIST-VALUE-TAGS-001): set and structured output note the tag they drop.
- Schema: `_UNDOCUMENTED` gains grpc `clear-text address`, the system flags, chassis `dump-on-panic` and the empty `system dump-on-panic` (UNDOCUMENTED-001); the grammar takes `then community = | + | -`. Artifacts and records regenerated; still 44 XSD fixes.
- Records: HOLD-TIME-001, RENAME-EVIDENCE-001 (NAT open) and JSON-KEYWORD-ALIAS-001 (the alias is permanent, ruling 1) closed.
- Not a break (`.openspec.yaml`): `-v` and the set reader refuse only lines the device refuses or no export holds; output changes only where it loaded with another meaning or not at all.

## Capabilities

### New Capabilities
- `conversion/selection-tags`: a selection's tag rules, moved from `conversion/path-filtering` (modified) and widened.
### Modified Capabilities
- `validation/raw-set-input`: the verb rule (moved from `validation/set-command-validation`) and the one-statement rule; `conversion/entry-keys`: a whole-list tag.
- `conversion/writers`: per-value notes; `conversion/tag-acceptance`: the `family` tag; `validation/device-captures`: probe statements; `schema-pipeline/conversion-hints`: the alias and the literals.

## Non-goals

The QFX refusing set `ether-options speed 1g` (platform-unsupported, the XSD lists it); bracket lists in set input; whether a device loads per-value tags from JSON; a whole-list tag that JSON or curly input carries (WHOLE-LIST-TAGS-001); comments in relative output; the NAT rename; edit-command semantics.

## Completion

Every item above fixed or recorded; every device capture's verb line still validates; the device checks and the before/after comparison show only explained differences.
