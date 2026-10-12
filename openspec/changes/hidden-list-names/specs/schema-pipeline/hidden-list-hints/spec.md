## ADDED Requirements

### Requirement: Hidden hints belong to structurally keyed lists

WHEN deriving conversion hints for a proven hidden-list shape THEN the model SHALL identify the list's declared keys from its structure and nokeyword status rather than introduce another list-name mapping; ordinary keyworded, leaf, unknown and unkeyed models SHALL retain their existing treatment. Retirement of existing named transparent hints SHALL require explicit equivalence and slot-blast-radius evidence.
Tests: `tests/unit/convert/test_hidden_list_names.py::TestKeywordChildrenPrecedeHiddenKeys::test_the_keyword_is_not_an_entry_name`, `tests/unit/convert/test_hidden_list_names.py::TestUnrelatedModelsKeepTheirMeaning::test_models_outside_the_hidden_key_rule_are_preserved`

#### Scenario: Proof before widening

- **WHEN** an L+nk shape has an address and choice key rather than name
- **THEN** its key structure drives transparency; the absence of a device capture does not prove new Junos syntax
