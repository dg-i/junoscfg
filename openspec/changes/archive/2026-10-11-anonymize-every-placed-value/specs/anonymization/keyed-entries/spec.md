## MODIFIED Requirements

### Requirement: No value anonymized before escapes

WHEN the anonymization test configurations are anonymized with every rule on
THEN every value the previous release replaced SHALL still be replaced, with
the same replacement for the same salt, but a value from its leaf's own enum,
which the previous release turned into invalid configuration. The dumped
mapping of the device example SHALL be pinned byte for byte; it SHALL change
only by entries for values the previous release left in the output, each
named with the reason it is now replaced, and never by a dropped or altered
entry. Phase 5 SHALL stop and report any value whose treatment moves otherwise.
Tests: `tests/unit/anonymize/test_integration.py::TestKeyedEntriesSurvive::test_no_value_anonymized_before_escapes`, `tests/unit/anonymize/test_integration.py::TestKeyedEntriesSurvive::test_name_keyed_output_is_unchanged`, `tests/unit/anonymize/test_integration.py::TestKeyedEntriesSurvive::test_what_a_rule_once_missed_is_replaced`

#### Scenario: An IP key keyed name

- **WHEN** an interface `address` entry keyed `name` holds `203.0.114.1/24`
  and is anonymized with `--anonymize-ips`
- **THEN** it is replaced exactly as before

#### Scenario: What the previous release missed

- **WHEN** the device example is anonymized with every rule on
- **THEN** the `tacplus-server` addresses, the port-mirroring `routing-instance`
  address and the two `interface-range` descriptions are replaced, and the
  pinned mapping gains exactly their entries and those of the other values the
  change reaches, each explained in the change's evidence
