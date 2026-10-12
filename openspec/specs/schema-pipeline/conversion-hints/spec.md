# schema-pipeline/conversion-hints Specification

## Purpose
Conversion hints preserve the XSD distinction between keyworded leaves, actual positional arguments and context-specific flattened containers.

## Requirements

### Requirement: Flat positional hints honor the owning node

WHEN a conversion-hint fix encounters a leaf named filename, as-number, confederation-as, path, limit or timeout THEN it SHALL add a flat positional hint only when the node declares nokeyword without freeform-nk; ordinary keyworded leaves SHALL retain their keyword, while genuine positional fields retain their supported spelling.
Tests: `tests/unit/validate/test_xsd_fixes.py::TestFlatPositionalHints::test_only_a_positional_leaf_receives_the_hint`

#### Scenario: The same name has different syntax

- **WHEN** timeout is keyworded under IS-IS overload but positional under another schema node
- **THEN** the keyworded node remains keyworded and the genuine positional node retains its syntax

### Requirement: Trigger flattening belongs to event options

WHEN flat-dict hints are applied THEN the system SHALL mark event-options policy within trigger and its configuration-group copy, while leaving unrelated trigger nodes unflattened; universal apply-macro retains its separate existing flat-dict treatment.
Tests: `tests/unit/validate/test_xsd_fixes.py::TestTriggerFlattening::test_only_event_options_trigger_is_flattened`

#### Scenario: Optical trigger contents remain hierarchical

- **WHEN** an interface trigger owns oc-los hold-time up
- **THEN** it is traversed as a hierarchy and its nested hold-time survives
