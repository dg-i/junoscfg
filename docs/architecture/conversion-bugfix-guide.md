# Conversion Bugfix Guide

Step-by-step methodology for diagnosing and fixing JSON/XML-to-structured conversion bugs.

## 1. Diagnosis Workflow

1. **Reproduce** the error: `uv run junoscfg convert -s --from-json input.json > /tmp/generated.conf`
2. **Diff** against the original: `diff -ur original.conf /tmp/generated.conf`
3. **Correlate** router errors to diff sections — each error message references a config path
4. **Classify** the root cause (see section 2)

## 2. Root Cause Classification

### Schema-flag level (Group H xsd_fix)

The schema tree doesn't have the right conversion hint for this element. Fix via xsd_fixes.py Group H — sets a flag that persists across XSD regeneration and is serialized into the schema artifact.

**Symptoms:**
- Transparent container not recognized (child keyword leaks into set commands)
- Flat entry emits key names instead of values only
- Positional key not recognized
- Flat dict not flattened to single line

**Fix location:** `src/junoscfg/validate/xsd_fixes.py` (Group H functions)

### Schema-level (missing flag or wrong structure)

The XSD schema doesn't model the element correctly. Fix via xsd_fixes.py Groups A-G.

**Symptoms:**
- Element renders as container block instead of oneliner (missing `oneliner` flag)
- Element renders with wrong nesting depth (wrong `is_list` or container structure)
- Element children appear as separate set lines instead of flat line

**Fix location:** `src/junoscfg/validate/xsd_fixes.py`

### Runtime-level (missing alias or XML-compat constant)

The schema is correct but the runtime conversion code needs a name mapping or XML-compat constant.

**Symptoms:**
- JSON input uses original XML name that differs from set command keyword
- XML/YAML converter doesn't recognize element (these walk XML trees, not the schema)

**Fix location:** `src/junoscfg/display/constants.py`

### Field-validation level (false positive or missing fallback)

The field validator rejects a valid configuration value. Fix in `convert/field_validator.py`.

**Symptoms:**
- Valid numeric value rejected in an enum-only field (XSD union type not handled)
- Valid IPv6 address rejected in a dual-stack field (`ipaddr`/`ipprefix`)
- List of values rejected because the list was validated as a single string
- Mandatory field warning fires for a flat-dict child that is functionally optional

**Fix location:** `src/junoscfg/convert/field_validator.py`

**Validation pass order:**
1. **Enum check** — Definitive if no fallback types exist
2. **Numeric/range fallback** — For enum fields, accept values matching `[0-9]+(-[0-9]+)?`
3. **Pattern check** — Fallback for fields with both enum and regex constraints
4. **Type check** — Fallback for fields with both enum and type constraints

## 3. Fix Checklist

For each bug, apply fixes in this order:

1. **XSD fix in `xsd_fixes.py`** — Set the appropriate schema flag. Register in `ALL_FIXES`. This persists when artifacts are regenerated from any Junos XSD.

   | Need | Flag to add | Group H function |
   |------|-----------|-----------------|
   | Transparent container | `transparent:{child}` | `_fix_transparent_containers()` |
   | Transparent list key | `transparent-list-key` | `_fix_transparent_list_keys()` |
   | Flat dict | `flat-dict` | `_fix_flat_dict_elements()` |
   | Flat entry | `flat-entry:{key}:{position}` + `oneliner` | `_fix_flat_entry_keys()` |
   | Positional key (nesting) | `positional-key` | `_fix_positional_keys()` |
   | Positional key (flat) | `positional-key-flat` | `_fix_positional_keys()` |
   | Freeform NK key | `freeform-nk` | `_fix_freeform_nk_keys()` |
   | Oneliner rendering | `oneliner` | (add directly or via `_fix_flat_entry_keys()`) |

2. **Regenerate schema** — `uv run pytest tests/ -q --regen-schema` to rebuild `junos-structure-tree.json` with new flags.

3. **Constants (only for XML/YAML converters)** — If the fix affects the XML→YAML bridge (`to_yaml.py`), also update the XML-compat constants in `constants.py` (they mirror schema flags for converters that walk XML trees).

4. **Key aliases** — If JSON input uses an original XML name, add to `KEY_ALIASES` in `constants.py`. The set input parser also resolves `KEY_ALIASES` during schema lookup so that aliased keywords (e.g., `802.3ad` → `ieee-802.3ad`) match the correct schema node.

5. **Regression test** — Add a test in `tests/test_convert_roundtrip.py` (for format conversions) and/or `tests/test_set_converter.py` (for set/structured output).

## 4. Key Files and Their Roles

### Schema Pipeline (build time)

| File | Role |
|------|------|
| `src/junoscfg/validate/xsd_parser.py` | Parse XSD into SchemaNode tree |
| `src/junoscfg/validate/xsd_fixes.py` | Apply structural corrections (Groups A-G) and conversion hints (Group H) |
| `src/junoscfg/validate/artifact_builder.py` | Serialize schema tree to `junos-structure-tree.json` with all flags |
| `src/junoscfg/validate/data/junos-structure-tree.json` | Bundled schema artifact used at runtime |

### Conversion Pipeline (runtime)

| File | Role |
|------|------|
| `src/junoscfg/display/constants.py` | Schema flag helpers, XML-compat constants, key aliases |
| `src/junoscfg/convert/output/dict_walker.py` | Dict IR → set/structured via `DictWalker` + `WalkOutput` strategy pattern |
| `src/junoscfg/convert/output/set_output.py` | `SetWalkOutput` — renders set commands from dict IR |
| `src/junoscfg/convert/output/structured_output.py` | `StructuredWalkOutput` — renders structured format from dict IR |
| `src/junoscfg/display/config_store.py` | Ordered tree for structured output (supports `replace:`, `protect:`, `inactive:` prefixes) |
| `src/junoscfg/display/value_format.py` | Value formatting (quoting, escaping) |

### Schema Tree Compact Format

The `junos-structure-tree.json` uses compact keys on each node:

| Flag | Type | Meaning | Set by |
|------|------|---------|--------|
| `c` | `{...}` | Children dict | xsd_parser |
| `l` | `true` | Leaf node | xsd_parser |
| `p` | `true` | Presence (flag-only, no value) | xsd_parser |
| `L` | `true` | Named list | xsd_parser |
| `nk` | `true` | Nokeyword | Group F fixes |
| `o` | `true` | Oneliner/flat entry | Group B2/H fixes |
| `t` | `"child"` | Transparent container child name | Group H fix |
| `tk` | `true` | Transparent list key | Group H fix |
| `pk` | `true` | Positional key (nesting) | Group H fix |
| `pkf` | `true` | Positional key (flat) | Group H fix |
| `fd` | `true` | Flat dict element | Group H fix |
| `fe` | `{"k":"..","p":".."}` | Flat entry config (key + position) | Group H fix |
| `frnk` | `true` | Freeform NK key | Group H fix |

## 5. Architectural Patterns

### Transparent Containers

Some Junos elements have a wrapper child that exists in XML/JSON but not in set commands. Example: `interfaces` → `interface` (the array wrapper).

Encoded as schema flag `t: "interface"` on the `interfaces` node.

**For JSON→set:** `_walk()` calls `get_transparent_child(child_schema, set_key)` to find and skip the wrapper.

**For set→structured:** `_schema_walk()` reads `node.get("t")` to detect when a token should be treated as a named list entry name. Transparent named lists are emitted as separate hierarchy levels.

### Flat Entries (Oneliners)

Some named lists render everything on a single line rather than as a container block. Example: `route-filter 0.0.0.0/0 exact;`

Two mechanisms work together:
1. **Schema flag `o: true`** — Tells `structured_output.py` to emit all tokens on one line
2. **Schema flag `fe: {"k": key, "p": position}`** — Tells `dict_walker.py` how to flatten the dict (read via `get_flat_entry_config()` helper)

Positions:
- `"first"` — positional key value appears before remaining keys
- `"last"` — positional key value appears after remaining keys
- `"values-only"` — all dict values emitted without key names

## 6. Worked Examples

### Example A: `groups` nesting (24 errors)

**Symptom:** Each named group renders as a separate `groups name { }` block instead of nested under `groups { name { } }`.

**Root cause:** Schema-level — `_fix_groups()` set `groups.is_list = True` with children directly, instead of creating a container→named-list pattern.

**Fix:**
1. `xsd_fixes.py` — Changed `_fix_groups()` to create `groups` (container) → `group` (named list)
2. `xsd_fixes.py` — Group H `_fix_transparent_containers()` adds `transparent:group` flag
3. `constants.py` — `"groups": "group"` in `TRANSPARENT_CONTAINERS` (XML-compat)
4. `structured_output.py` — Reads `"t"` flag for transparent named list handling

### Example B: `attributes-match` flattening (2 errors)

**Symptom:** Array entries emitted as three separate set lines with key names instead of one flat line with values only.

**Root cause:** Schema-level — XSD had no `oneliner` flag for `attributes-match`.

**Fix:**
1. `xsd_fixes.py` — Group B2: `_fix_attributes_match_oneliner()` adds `oneliner` flag
2. `xsd_fixes.py` — Group H: `_fix_flat_entry_keys()` adds `flat-entry::values-only` flag + `oneliner`
3. `dict_walker.py` — `get_flat_entry_config()` reads `fe` flag for flattening config
