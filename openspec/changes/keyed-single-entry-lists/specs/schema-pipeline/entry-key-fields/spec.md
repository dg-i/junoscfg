## ADDED Requirements

### Requirement: Device-backed keyed singletons use the existing list model
WHEN a singleton schema type declares a positional identifier for a keyed entry THEN the corrected schema model SHALL represent the entry as a list without losing children or key order; ordinary containers, unkeyed homogeneous nodes and positional value leaves SHALL retain their classification. The bounded baseline is port-mirroring routing-instance, SRGB label-range and IS-IS attribute-group. This does not promise that multiple entries load on a device.
Tests: `tests/unit/convert/test_convert_roundtrip.py::TestKeyedSingletonMetadata::test_device_backed_slots_are_lists`, `tests/unit/convert/test_convert_roundtrip.py::TestKeyedSingletonMetadata::test_ordinary_containers_keep_their_classification`

#### Scenario: Three named paths
- **WHEN** bundled metadata resolves those paths at root and grouped copies
- **THEN** each is a keyed list with its original children and positional metadata

#### Scenario: Negative controls
- **WHEN** metadata resolves transport-class, snmp, trace filename and port-mirroring family
- **THEN** none becomes a list from its name or homogeneous flag alone
