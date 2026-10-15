## Findings

Independent Test/Challenge (fresh agent, high risk floor), on tests commit
`08139866e06ccdd71998e1234ba23fdbf90d9e3d` against base `332523c`; its probes ran on the
base code. Each finding and how the Builder resolved it, fixed in `c84d07d`:

1. B1 (binding) validation through the YAML schema went undetected: the every-door rows hold
   no meta key. Fixed: `TestValidateConfig::test_junos_yaml_is_judged_by_the_json_schema`,
   `TestJunosValidator::test_validate_yaml_as_json_uses_the_json_schema`, and the
   `cli-validate-only-yaml-new` message row now holds `_meta_acme`. Mutating `validate_config`
   to the YAML schema fails the first.
2. B2 (binding) validating a YAML-only value crashed (`on:` key, TypeError) or passed (date).
   Fixed: the check moved to the kernel, `junoscfg.input.find_non_json_value`, shared by the
   reader and `validate_yaml_as_json`, which returns an invalid result with kind and path;
   requirement and scenario added to validation/junos-json-yaml. Tests
   `test_a_value_json_cannot_hold_is_invalid`, `test_a_yaml_new_value_json_cannot_hold_exits_one`
   (4 fail with the check removed).
3. B3 (binding) refusal kinds: the implementation was already an allow-list; rows added for
   bool, null, float and date keys, `!!omap`, `!!pairs`, siblings of `configuration` and the
   document itself, with marker values checked absent from the message.
4. B4 (binding) the audit test passed under legacy routing. Fixed:
   `TestInputFormats::test_a_value_json_cannot_hold_is_refused` (yaml-new refuses, yaml reads).
5. B5 (binding) nothing proved dispatch goes through the table. Fixed: the table is a dict
   read at call time; `TestFormatEnum::test_the_rename_is_a_change_to_the_table` swaps the two
   YAML rows and checks to_dict, from_dict, convert_config, validate_config and the CLI.
6. B6 (binding) nothing pinned `yaml` as the IR dump. Fixed:
   `TestTheYamlWriterDumpsTheIr::test_the_output_is_the_ir_as_read` over every catalogue
   source; byte identity also measured (Evidence below).
7. B7 (binding) relative selection covered only mappings. Fixed: rows for `{}` and a selected
   list. The probe also showed relative JSON output of a selected list is not normalized
   (`"any": {}` where absolute output writes `[null]`); yaml-new matches it. Pending owner
   decision below.
8. B8 (binding) the anchor test could not fail. Fixed: a bare shared list, wrapped and bare.
9. Advisory: A1 left to the Reviewer (no JSON text round trip); A2 YAML 1.1 implicit typing
   kept (PyYAML's dumper quotes against it; a 1.2 loader would mis-read `1e3` the dumper leaves
   bare), pinned by `test_unquoted_words_are_read_as_pyyaml_reads_them` and documented; A3
   loader named in the spec, `_TRICKY` extended; A4 `.inf`/`.nan` read as JSON input reads
   `Infinity`/`NaN`, documented, in the property's value pool; A5 scope pinned; A6 meta keys
   and `apply-groups` in the property; A7 `test_the_device_spellings_are_written_as_json_writes_them`;
   A8 tests renamed by implementation, rename consequence in the decision record; A9 help test
   asserts the rename wording; A10 to A12 accepted as reported.

## Already provided

The JSON writer's and reader's normalization (reused, not copied); PyYAML `SafeDumper`;
`find_configuration`; the shape catalogue and device captures; `tools/compare_device_outputs.py`.

## Specification challenges

None recorded by Test/Challenge as a criteria contradiction; B2's omitted criterion was
added to validation/junos-json-yaml before review.

## Pending owner decisions

- PO-1 (from B7): relative JSON output of a selected list keeps `{}` and `true` where absolute
  output writes `[null]` (base behaviour, `junos_json_object` normalizes mappings only).
  Fixing it changes `json` output, a non-goal of this change; yaml-new keeps equivalence.
  Options: a follow-up fix in the JSON writer, or a backlog entry. Not backlogged by the Builder.

## Evidence

- Catalogue, base vs head, every shape x reader x {set, structured, json, yaml}: 1,936
  conversions, 0 differ (484 yaml outputs byte-identical).
- Device corpus, `tools/compare_device_outputs.py`: 0 of 96 conversions differ.

## Verdict

Pending the fresh isolated Reviewer.

## Scope dispositions and follow-up evidence

Test/Challenge findings B1 to B8 resolved in the change; PO-1 awaits the owner.
