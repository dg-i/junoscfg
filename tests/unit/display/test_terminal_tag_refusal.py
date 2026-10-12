"""The deprecated schema-free writer refuses metadata it cannot place safely."""

from __future__ import annotations

import pytest

from junoscfg import Format, convert_config
from junoscfg.display import SetConverter
from junoscfg.validate import JunosValidator, StructuredValidator, ValidationResult


class TestTerminalMetadataRequiresTheSchema:
    """Held route oracle and frozen legacy fixtures; SC1 in reject-deprecated-tagged-statements.

    The route fixture comes from the synthetic vMX oracle. Refusal is a declared
    compatibility correction; supported conversion keeps the owning-node tags.
    """

    @pytest.mark.parametrize(
        ("source", "expected"),
        [
            (
                "routing-options { static { inactive: route 10.98.0.0/16 reject; } }",
                [
                    "set routing-options static route 10.98.0.0/16 reject",
                    "deactivate routing-options static route 10.98.0.0/16",
                ],
            ),
            (
                "routing-options { protect: autonomous-system 64496; }",
                [
                    "set routing-options autonomous-system 64496",
                    "protect routing-options autonomous-system",
                ],
            ),
            (
                "groups baz { snmp { inactive: location baz; } }",
                ["set groups baz snmp location baz", "deactivate groups baz snmp location"],
            ),
            (
                "snmp { inactive: apply-groups [ foo bar ]; }",
                [
                    "set snmp apply-groups foo",
                    "set snmp apply-groups bar",
                    "deactivate snmp apply-groups",
                ],
            ),
            (
                "system { protect: host-name router1; }",
                ["set system host-name router1", "protect system host-name"],
            ),
            (
                "system { delete: host-name router1; }",
                ["set system host-name router1", "delete system host-name"],
            ),
            (
                'interfaces { ge-0/0/0 { protect: description "a b"; } }',
                [
                    'set interfaces ge-0/0/0 description "a b"',
                    "protect interfaces ge-0/0/0 description",
                ],
            ),
            (
                "routing-options { static { inactive:\t route\t10.98.0.0/16\t reject; } }",
                [
                    "set routing-options static route 10.98.0.0/16 reject",
                    "deactivate routing-options static route 10.98.0.0/16",
                ],
            ),
        ],
        ids=[
            "inactive-route",
            "protected-as",
            "inactive-group-location",
            "inactive-leaf-list",
            "protected-host-name",
            "deleted-host-name",
            "quoted-value",
            "normalized-tabs",
        ],
    )
    def test_to_set_refuses_a_multiword_terminal_tag(
        self, source: str, expected: list[str]
    ) -> None:
        assert (
            convert_config(source, from_format=Format.STRUCTURED, to_format=Format.SET).splitlines()
            == expected
        )
        converter = SetConverter(source)
        statements = converter.statements()
        with pytest.deprecated_call(match="convert_config"), pytest.raises(ValueError) as error:
            converter.to_set()
        assert "convert_config" in str(error.value)
        for secret in (
            "10.98.0.0/16",
            "64496",
            "router1",
            "baz",
            "foo",
            "bar",
            "ge-0/0/0",
            '"a b"',
        ):
            assert secret not in str(error.value)
        assert converter.statements() == statements

    @pytest.mark.parametrize(
        ("source", "expected"),
        [
            ("system { host-name router1; }", ["set system host-name router1"]),
            ("system { replace: host-name router1; }", ["set system host-name router1"]),
            (
                "system { inactive: services { ssh; } }",
                ["set system services ssh", "deactivate system services"],
            ),
            (
                "system { protect: services { ssh; } }",
                ["set system services ssh", "protect system services"],
            ),
            (
                "system { delete: services { ssh; } }",
                ["set system services ssh", "delete system services"],
            ),
            (
                "system { services { inactive: ssh; } }",
                ["set system services ssh", "deactivate system services ssh"],
            ),
            (
                "system { services { protect: ssh; } }",
                ["set system services ssh", "protect system services ssh"],
            ),
            (
                "system { services { delete: ssh; } }",
                ["set system services ssh", "delete system services ssh"],
            ),
            (
                "system { services { replace: protect: inactive: delete: ssh; } }",
                [
                    "set system services ssh",
                    "protect system services ssh",
                    "deactivate system services ssh",
                    "delete system services ssh",
                ],
            ),
            (
                'system { services { protect: "ssh"; } }',
                ['set system services "ssh"', 'protect system services "ssh"'],
            ),
        ],
    )
    def test_unambiguous_legacy_statements_keep_their_output(
        self, source: str, expected: list[str]
    ) -> None:
        with pytest.deprecated_call(match="convert_config"):
            assert SetConverter(source).to_set().splitlines() == expected

    @pytest.mark.parametrize("tag", ["inactive", "protect", "delete"])
    def test_deprecated_validation_reports_the_refusal(self, tag: str, artifacts_dir: str) -> None:
        class SetValidationMustNotRun:
            def validate(self, source: str) -> ValidationResult:
                pytest.fail("Unsafe terminal metadata reached set validation")

        source = f"system {{ {tag}: host-name router1; }}"
        with pytest.deprecated_call():
            result = StructuredValidator(SetValidationMustNotRun()).validate(source)
        assert result.valid is False
        assert result.errors
        assert "convert_config" in result.errors[0].message
        assert "router1" not in result.errors[0].message
        with pytest.deprecated_call():
            facade = JunosValidator(artifacts_dir=artifacts_dir).validate_structured(source)
        assert facade.valid is False
        assert facade.errors
        assert "convert_config" in facade.errors[0].message
        assert "router1" not in facade.errors[0].message
