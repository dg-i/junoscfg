## Context

Readers and writers dispatch on format-name strings in `to_dict`, `from_dict`,
`pipeline_result` (relative output unwraps `json`/`yaml`) and top-level `validate_config`.
The JSON writer builds a normalized copy (`_native_groups`, `_normalize_presence_flags`,
`_coerce_scalar_leaves`, `_ensure_name_first`) and serializes it in one function; the JSON
reader parses and calls `find_configuration` in one function. `yaml` input strips meta keys
and promotes leaf-lists; JSON does neither and loads no schema.

## Reuse ladder

| Candidate | Coverage | Gap | Maintenance signal, lookup date | Verdict |
|---|---|---|---|---|
| JSON writer and reader in convert/output/json_output.py, convert/input/json_input.py | All Junos JSON rules, both directions | Object stage fused with text | In-repo, 2026-10-15 | Split each into object stage plus serializer/parser; share the object stage |
| PyYAML (`yaml.safe_load`, `SafeDumper`), already a runtime dependency | YAML text both ways | Aliases for shared objects | pyyaml in uv.lock, 2026-10-15 | Use; a `SafeDumper` subclass ignoring aliases |
| JSON text round trip (`json.dumps` then the JSON reader) | Everything | Re-parses text; owner and backlog reject it | n/a | Rejected |

## Decisions

1. `json_output.junos_json_object(config, *, wrap)` returns the object `dict_to_json` serializes;
   `dict_to_json` and the new `dict_to_junos_yaml` serialize it. `json_input.ir_from_junos_json_object(data, *, label)`
   is the reader's object stage; `json_to_dict` and the new `junos_yaml_to_dict` parse into it.
   Both YAML functions live beside their JSON twins: one module per direction owns Junos JSON.
2. `junos_yaml_to_dict` loads with `yaml.safe_load` (the parser `yaml` uses), refuses values
   with no JSON spelling by kind and path through `junoscfg.input.find_non_json_value`, which
   validation shares (kernel layer, as `find_unsupported_set_brackets`), then hands the object
   to the shared stage. No meta-key strip, no leaf-list promotion: JSON's shapes.
3. `convert/formats.py` holds `FORMAT_IMPLEMENTATIONS` (name to implementation id), a dict read
   at each call so a test rehearses the rename by patching it, and `implementation(fmt,
   direction)`; `to_dict`, `from_dict` and `validate_config` dispatch on the id.
   `pipeline_result` passes `wrap=not relative` (set and structured ignore `wrap`), dropping its
   format list. `junoscfg.convert` exports the table; tach exposes it (C7).
4. `Format.YAML_NEW = "yaml-new"` after `YAML`; `_SUPPORTED_CONVERSIONS` becomes every pair
   but XML output, which is what its twenty rows already listed.
5. Validation: `JsonYamlValidator.validate_yaml_as_json` (YAML parse errors as `validate_yaml`
   reports them, a non-JSON value as an error, then the JSON schema); `JunosValidator` delegates.
   `validate_yaml`'s parse-error result moves into a shared helper, unchanged.
6. CLI choices derive from `Format`; help text names yaml-new and the planned rename. Detection
   keeps returning `yaml` (YAML-new and YAML text cannot be told apart).
7. `yaml` reader and writer modules are not edited, so their bytes cannot change.

## Risks

- A consumer iterating `Format` sees one more member: additive, documented.
- yaml-new keeps JSON's `{}` to `[null]` rewrite, unproven on QFX 25.2 load (C8, device question).
- yaml-new input with Ansible meta keys fails JSON-schema validation and field validation;
  documented, and the migration strips them once.
- Implementation ids (`ir-yaml`, `junos-yaml`) are visible through the exported table; they are
  documented as stable until the rename change.
