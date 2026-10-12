## ADDED Requirements

### Requirement: Hidden hints belong to structurally keyed lists

WHEN deriving conversion hints for a proven hidden-list shape THEN the model SHALL identify the list's declared keys from its structure and nokeyword status rather than introduce another list-name mapping; ordinary keyworded, leaf, unknown and unkeyed models SHALL retain their existing treatment. Retirement of existing named transparent hints SHALL require explicit equivalence and slot-blast-radius evidence.
Tests: `tests/unit/validate/test_hidden_list_hints.py::TestHiddenHintsFollowTheDeclaredKey::test_a_hidden_key_needs_no_name_mapping`, `tests/unit/validate/test_hidden_list_hints.py::TestHiddenHintsFollowTheDeclaredKey::test_nonmatching_models_receive_no_hidden_hint`

#### Scenario: Proof before widening

- **WHEN** an L+nk shape has an address and choice key rather than name
- **THEN** its key structure drives transparency; the absence of a device capture does not prove new Junos syntax
