## Why

YAML output dumps the IR while the JSON writer normalizes its own copy, so JSON's device
spellings never reach YAML (YAML-JSON-001: 39 of 484 catalogue conversions differ in shape).
The owner wants a YAML that is exactly the Junos JSON object, beside the unchanged `yaml`.

## What Changes

- New format `yaml-new` in `Format.YAML_NEW`, CLI `-i`/`-e`, audit `-i` and `validate_config`:
  output is the object the JSON writer builds, serialized as YAML; input is parsed YAML handed
  to the JSON reader's object stage. Shared object-level adapters; no JSON text round trip.
- yaml-new keeps JSON's behaviour exactly: `[null]` for `{}`/`true` flags, scalar leaves,
  native `groups`, `junoscfg:unplaced` as JSON writes it; no `_ansible_*`/`_meta_*` cleanup and
  no scalar leaf-list promotion on input. A YAML value JSON cannot hold (a date, a non-string
  key) is refused. yaml-new validates against the JSON schema.
- One table maps each format name to its implementation (`FORMAT_IMPLEMENTATIONS`); readers,
  writers and validation dispatch through it, so the later rename edits it and `Format` only.
- `yaml` stays byte-identical. Migration `-i yaml -e yaml-new` is documented and tested.
  The planned rename (`yaml` to `yaml-old`, `yaml-new` to `yaml`) and its deprecation policy
  go in a decision record, the user guide and ARCHITECTURE.md; `yaml` is not deprecated now.
- Format-name search (`"yaml"`, `Format.YAML`, `_FORMAT_CHOICES`, `CONVERSION_FORMATS`): `to_dict`,
  `from_dict`, `pipeline_result`, `validate_config`, CLI convert/audit; detection stays `yaml`.

## Capabilities

### New Capabilities

- `conversion/junos-json-yaml`: the yaml-new format, its equivalence to JSON, migration, the format table.
- `validation/junos-json-yaml`: validating yaml-new gives the JSON verdict.

### Modified Capabilities

None, because existing requirements keep their meaning; `yaml` is untouched.

## Non-goals

No change to `yaml`, JSON output, detection or the anonymizer; no deprecation; no rename;
no new device claim; YAML conveniences on yaml-new input stay absent.
