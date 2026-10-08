## Added

- `display.constants`: `INTEGER_TYPES`, `UNQUOTABLE_TYPES`,
  `UNIVERSAL_STATEMENTS`, `ENTRY_KEY_OVERRIDES`, `strip_type_prefix`,
  `statement_name_spellings`, `enum_is_fragment`. Exported through
  `junoscfg.display` and listed in `tach.toml`.
- `schema_generator`: `_entry_keys`, `_switch_spellings`.
- `grammar_generator`: `_takes_either_order`, `_EITHER_ORDER_SUFFIX`.
- `tests/test_round_trip_validates.py`; `bundled_validator` and
  `project_root` fixtures in `tests/conftest.py`.
- `changelog.d/+validate-own-output.bugfix.md`.

## Removed

- `field_validator._INTEGER_TYPES`. The kernel holds it now, and the local
  copy was unreachable: it held bare XSD names where the tree stores prefixed
  ones, so no leaf ever matched it.

## Changed, not removed

- In `tests/test_schema_generator.py`, `test_json_no_pattern_properties` becomes
  `test_json_has_no_ansible_patterns`, `test_a_tree_without_the_flag_gains_no_
  pattern` becomes `test_a_tree_without_the_flag_still_names_the_kernel_four`,
  `test_list_has_array` reads `anyOf`. Each pinned a state in which junoscfg
  rejected its own output.
- In `tests/test_artifact_resolution.py`,
  `test_a_missing_directory_is_none_not_a_crash` becomes
  `test_a_directory_the_caller_chose_reports_an_error`, with
  `test_only_the_bundled_directory_answers_none` beside it.
- In `tests/test_jvd_corpus.py`, the oneliner guard takes
  `bundled_set_validator` instead of building `data/junos-set.lark` by hand. That path stopped
  existing when the artifacts shipped gzipped, and the tier is opt-in, so the
  tier was red at HEAD and nothing said so.

## Not retired

- The `apply-*` bridge in `set_validator.py`. The grammar still has no rule
  for the four, because the structure tree carries no `universal` node; only
  the JSON and YAML schemas gained them.
