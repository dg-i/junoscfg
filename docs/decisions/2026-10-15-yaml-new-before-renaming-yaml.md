---
status: accepted
scope: ["src/junoscfg/convert/formats.py", "src/junoscfg/__init__.py", "src/junoscfg/cli.py"]
enforced-by: tests
review-by: 2027-04-15
---

# Add yaml-new beside yaml before renaming it

## Context

The `yaml` format dumps the IR, while the JSON writer normalizes its own copy for the
device (`[null]` flags, scalar leaves, native `groups`); YAML-JSON-001 measured 39 of 484
catalogue conversions with a different shape. Replacing `yaml` at once would change what
the production consumer (ARCHITECTURE.md section 3) reads and writes under the same name.
The owner asked on 2026-10-15 for the normalized YAML under a new name first.

## Decision

`yaml-new` is added: the Junos JSON object as YAML, written by the JSON writer's object
stage and read by the JSON reader's. `yaml` is unchanged and not deprecated. Each format
name selects its implementation through one table, `junoscfg.convert.FORMAT_IMPLEMENTATIONS`
(`yaml` to `ir-yaml`, `yaml-new` to `junos-yaml`); `Format`'s values must equal its names.
Adding a format is additive: a patch release.

The rename is a later change, once `yaml-new` has been tested in use and its users have
migrated (`junoscfg convert -i yaml -e yaml-new old.yaml`). It edits the table and `Format`:
`yaml` selects `junos-yaml`, `yaml-old` selects `ir-yaml`, and `yaml-new` stays an accepted
alias of `yaml` that warns. Because `yaml` then changes meaning on both named surfaces, that
change declares a break, raises the minor and states the migration. In beta a removal is
deprecated first: `yaml-new` as an alias, and later `yaml-old`, each warn for at least one
minor release before a change removes them.

## Consequences

Conversion and validation dispatch follow the table; `test_the_rename_is_a_change_to_the_table`
rehearses the swap today. The rename change also owns: a way for the `yaml-new` alias to warn,
which the table cannot express; detection, which returns `yaml`, so undeclared YAML changes
meaning; `validate_yaml` and `JunosValidator.validate_yaml`, which keep the YAML schema and
must follow `yaml-old` or be re-pointed; `_READERS`/`_WRITERS` in `__init__.py`, CLI help and
error text; tests using `Format.YAML` as the IR-dump oracle; and measuring the consumer's
pipelines, since yaml-new keeps `_ansible_*`/`_meta_*` keys and scalar leaf-lists as JSON does.
