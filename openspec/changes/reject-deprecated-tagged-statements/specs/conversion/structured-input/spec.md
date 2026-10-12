## MODIFIED Requirements

### Requirement: The schema-free set writer of the lexer is deprecated

WHEN a caller uses `SetConverter.to_set()` THEN it SHALL emit a
`DeprecationWarning` naming `convert_config(..., from_format=Format.STRUCTURED,
to_format=Format.SET)` and removal in the next minor release. It keeps its
schema-free route and token lexer, so one-line text yields its lines, but SHALL
refuse terminal statements tagged `inactive`, `protect`, or `delete` whose
stripped lexer text contains a space (the conservative multiword boundary). A `ValueError` names the
schema-aware replacement and SHALL contain no source path, key or value.
The lexer already joins terminal tokens with single spaces and retains quotes;
this boundary SHALL use that existing normalized text, without resolving the
schema or parsing a second time. Block-opening tags, one-token tagged terminal
statements, `replace`-only stripping, untagged legacy output and `statements()`
SHALL retain their existing behavior.
Tests: `tests/unit/display/test_set_converter.py::TestToSetIsDeprecated::test_it_warns_and_keeps_its_output`, `tests/unit/display/test_terminal_tag_refusal.py::TestTerminalMetadataRequiresTheSchema::test_to_set_refuses_a_multiword_terminal_tag`, `tests/unit/display/test_terminal_tag_refusal.py::TestTerminalMetadataRequiresTheSchema::test_unambiguous_legacy_statements_keep_their_output`

#### Scenario: A caller of the deprecated writer

- **WHEN** `SetConverter("system {\n host-name router1;\n}").to_set()` is called
- **THEN** it warns and returns `set system host-name router1`

#### Scenario: An inactive route with a child

- **WHEN** deprecated `to_set()` reads `routing-options { static { inactive: route 10.98.0.0/16 reject; } }`
- **THEN** it raises before returning incorrect child metadata, while supported conversion retains the route's inactivity at `routing-options static route 10.98.0.0/16`

#### Scenario: A multiword tagged leaf or list

- **WHEN** terminal `protect: host-name router1;`, `delete: host-name router1;`, `inactive: location baz;`, or `inactive: apply-groups [ foo bar ];` reaches deprecated `to_set()`
- **THEN** it raises with the replacement named, while supported conversion keeps positive set content and metadata on the owning statement

#### Scenario: Existing unambiguous schema-free rendering

- **WHEN** a tag leads a block opener, a one-token terminal flag, a replace-only statement, or an untagged terminal statement
- **THEN** deprecated output is preserved and `statements()` still exposes the original tagged terminal tokens
