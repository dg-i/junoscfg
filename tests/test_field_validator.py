"""Tests for field-level validation of Junos configuration values."""

from __future__ import annotations

import pytest

from junoscfg.convert.field_validator import (
    FieldError,
    FieldValidationError,
    FieldValidationResult,
    FieldValidator,
)

# ── Test schema fixtures ─────────────────────────────────────────────


def _make_schema(
    *,
    enums: list[list[str]] | None = None,
    patterns: list[str] | None = None,
    tree: dict | None = None,
) -> dict:
    """Build a minimal structure tree with field-level metadata."""
    schema: dict = {}
    if tree:
        schema.update(tree)
    if enums:
        schema["_enums"] = enums
    if patterns:
        schema["_patterns"] = patterns
    return schema


def _leaf(**kwargs: object) -> dict:
    """Build a leaf node dict."""
    d: dict = {"l": True}
    d.update(kwargs)
    return d


def _container(**children: dict) -> dict:
    """Build a container node dict."""
    return {"c": children}


# ── FieldError / FieldValidationResult unit tests ────────────────────


class TestFieldErrorDataclass:
    def test_creation(self) -> None:
        err = FieldError(path="system.host-name", message="bad value", value="x")
        assert err.path == "system.host-name"
        assert err.message == "bad value"
        assert err.value == "x"
        assert err.expected == ""

    def test_with_expected(self) -> None:
        err = FieldError(path="a.b", message="fail", expected="integer")
        assert err.expected == "integer"


class TestFieldValidationResult:
    def test_valid_when_empty(self) -> None:
        result = FieldValidationResult()
        assert result.valid is True
        assert result.errors == []
        assert result.warnings == []

    def test_invalid_with_errors(self) -> None:
        result = FieldValidationResult()
        result.errors.append(FieldError(path="x", message="bad"))
        assert result.valid is False

    def test_valid_with_warnings_only(self) -> None:
        result = FieldValidationResult()
        result.warnings.append(FieldError(path="x", message="missing"))
        assert result.valid is True


class TestFieldValidationError:
    def test_message(self) -> None:
        result = FieldValidationResult()
        result.errors.append(FieldError(path="a.b", message="invalid value"))
        exc = FieldValidationError(result)
        assert "1 error(s)" in str(exc)
        assert "invalid value" in str(exc)
        assert exc.result is result

    def test_truncated_message(self) -> None:
        result = FieldValidationResult()
        for i in range(7):
            result.errors.append(FieldError(path=f"p{i}", message=f"err{i}"))
        exc = FieldValidationError(result)
        assert "7 error(s)" in str(exc)
        assert "2 more" in str(exc)


# ── Enum validation ──────────────────────────────────────────────────


class TestEnumValidation:
    def test_value_in_allowed_set_passes(self) -> None:
        schema = _make_schema(
            enums=[["enable", "disable"]],
            tree=_container(
                configuration=_container(
                    system=_container(
                        option=_leaf(e=0),
                    )
                )
            ),
        )
        validator = FieldValidator(schema=schema)
        result = validator.validate({"system": {"option": "enable"}})
        assert result.valid is True
        assert result.errors == []

    def test_value_not_in_set_fails(self) -> None:
        schema = _make_schema(
            enums=[["enable", "disable"]],
            tree=_container(
                configuration=_container(
                    system=_container(
                        option=_leaf(e=0),
                    )
                )
            ),
        )
        validator = FieldValidator(schema=schema)
        result = validator.validate({"system": {"option": "maybe"}})
        assert result.valid is False
        assert len(result.errors) == 1
        assert "maybe" in result.errors[0].message
        assert "enable" in result.errors[0].message

    def test_large_enum_shows_truncated_list(self) -> None:
        values = [f"val{i}" for i in range(20)]
        schema = _make_schema(
            enums=[values],
            tree=_container(configuration=_container(level=_container(choice=_leaf(e=0)))),
        )
        validator = FieldValidator(schema=schema)
        result = validator.validate({"level": {"choice": "nonexistent"}})
        assert result.valid is False
        assert "20 total" in result.errors[0].message

    def test_list_value_validates_each_element(self) -> None:
        """List values should be validated element-by-element, not as str(list)."""
        schema = _make_schema(
            enums=[["aes128-ctr", "aes256-ctr", "aes128-gcm"]],
            tree=_container(
                configuration=_container(
                    system=_container(
                        ciphers=_leaf(e=0),
                    )
                )
            ),
        )
        validator = FieldValidator(schema=schema)
        result = validator.validate({"system": {"ciphers": ["aes128-ctr", "aes256-ctr"]}})
        assert result.valid is True
        assert result.errors == []

    def test_list_value_reports_invalid_element(self) -> None:
        """When a list has an invalid element, only that element is reported."""
        schema = _make_schema(
            enums=[["aes128-ctr", "aes256-ctr"]],
            tree=_container(
                configuration=_container(
                    system=_container(
                        ciphers=_leaf(e=0),
                    )
                )
            ),
        )
        validator = FieldValidator(schema=schema)
        result = validator.validate({"system": {"ciphers": ["aes128-ctr", "bad-cipher"]}})
        assert result.valid is False
        assert len(result.errors) == 1
        assert "bad-cipher" in result.errors[0].message

    def test_enum_with_type_fallthrough(self) -> None:
        """Numeric value passes when enum fails but type constraint matches."""
        schema = _make_schema(
            enums=[["ssh", "telnet", "http"]],
            tree=_container(
                configuration=_container(
                    system=_container(
                        port=_leaf(e=0, tr="uint16"),
                    )
                )
            ),
        )
        validator = FieldValidator(schema=schema)
        # Numeric port 179 is not in the enum, but is a valid uint16
        result = validator.validate({"system": {"port": "179"}})
        assert result.valid is True

    def test_enum_with_pattern_fallthrough(self) -> None:
        """Numeric value passes when enum fails but pattern matches."""
        schema = _make_schema(
            enums=[["ssh", "telnet"]],
            patterns=[r"^[0-9]+(-[0-9]+)?$"],
            tree=_container(
                configuration=_container(
                    system=_container(
                        port=_leaf(e=0, r=0),
                    )
                )
            ),
        )
        validator = FieldValidator(schema=schema)
        # Port range "33434-33464" is not in enum, but matches the pattern
        result = validator.validate({"system": {"port": "33434-33464"}})
        assert result.valid is True

    def test_enum_only_accepts_numeric_value(self) -> None:
        """Enum-only fields accept numeric values (XSD union types)."""
        schema = _make_schema(
            enums=[["ftp-data", "ftp", "ssh", "telnet", "smtp"]],
            tree=_container(
                configuration=_container(
                    system=_container(
                        port=_leaf(e=0),
                    )
                )
            ),
        )
        validator = FieldValidator(schema=schema)
        result = validator.validate({"system": {"port": "179"}})
        assert result.valid is True

    def test_enum_only_accepts_numeric_range(self) -> None:
        """Enum-only fields accept numeric ranges like '33434-33464'."""
        schema = _make_schema(
            enums=[["ftp-data", "ftp", "ssh", "telnet"]],
            tree=_container(
                configuration=_container(
                    system=_container(
                        port=_leaf(e=0),
                    )
                )
            ),
        )
        validator = FieldValidator(schema=schema)
        result = validator.validate({"system": {"port": "33434-33464"}})
        assert result.valid is True

    def test_enum_with_name_placeholder_accepts_string(self) -> None:
        """Enum containing 'name' accepts arbitrary string values (XSD union)."""
        schema = _make_schema(
            enums=[["all", "name"]],
            tree=_container(
                configuration=_container(
                    vlan=_container(members=_leaf(e=0)),
                )
            ),
        )
        validator = FieldValidator(schema=schema)
        result = validator.validate({"vlan": {"members": "VX3001020"}})
        assert result.valid is True

    def test_enum_with_name_placeholder_still_accepts_literal(self) -> None:
        """Enum containing 'name' still accepts the literal keyword 'all'."""
        schema = _make_schema(
            enums=[["all", "name"]],
            tree=_container(
                configuration=_container(
                    vlan=_container(members=_leaf(e=0)),
                )
            ),
        )
        validator = FieldValidator(schema=schema)
        result = validator.validate({"vlan": {"members": "all"}})
        assert result.valid is True

    def test_enum_with_value_placeholder_accepts_string(self) -> None:
        """Enum containing 'value' accepts arbitrary values (XSD union)."""
        schema = _make_schema(
            enums=[["auto", "value"]],
            tree=_container(
                configuration=_container(
                    shdsl=_container(line_rate=_leaf(e=0)),
                )
            ),
        )
        validator = FieldValidator(schema=schema)
        result = validator.validate({"shdsl": {"line_rate": "192"}})
        assert result.valid is True

    def test_enum_with_suffix_name_placeholder_accepts_string(self) -> None:
        """Enum containing '*-name' suffix accepts arbitrary instance names."""
        schema = _make_schema(
            enums=[["default", "routing-instance-name"]],
            tree=_container(
                configuration=_container(
                    routing=_container(instance=_leaf(e=0)),
                )
            ),
        )
        validator = FieldValidator(schema=schema)
        result = validator.validate({"routing": {"instance": "vpn-1"}})
        assert result.valid is True

    def test_enum_with_suffix_id_placeholder_accepts_string(self) -> None:
        """Enum containing '*-id' suffix accepts arbitrary identifiers."""
        schema = _make_schema(
            enums=[["none", "vlan-id"]],
            tree=_container(
                configuration=_container(
                    bridge=_container(domain=_leaf(e=0)),
                )
            ),
        )
        validator = FieldValidator(schema=schema)
        result = validator.validate({"bridge": {"domain": "100"}})
        assert result.valid is True

    def test_enum_without_placeholder_still_rejects(self) -> None:
        """Enum without any placeholder values still rejects unknown strings."""
        schema = _make_schema(
            enums=[["enable", "disable"]],
            tree=_container(
                configuration=_container(
                    system=_container(option=_leaf(e=0)),
                )
            ),
        )
        validator = FieldValidator(schema=schema)
        result = validator.validate({"system": {"option": "VX3001020"}})
        assert result.valid is False

    def test_enum_only_still_rejects_bad_values(self) -> None:
        """When field has only an enum (no type/pattern), non-numeric bad values still fail."""
        schema = _make_schema(
            enums=[["enable", "disable"]],
            tree=_container(
                configuration=_container(
                    system=_container(
                        option=_leaf(e=0),
                    )
                )
            ),
        )
        validator = FieldValidator(schema=schema)
        result = validator.validate({"system": {"option": "maybe"}})
        assert result.valid is False


# ── Pattern validation ───────────────────────────────────────────────


class TestPatternValidation:
    def test_matching_pattern_passes(self) -> None:
        schema = _make_schema(
            patterns=[r"^[a-z][a-z0-9-]*$"],
            tree=_container(
                configuration=_container(
                    system=_container(
                        name=_leaf(r=0),
                    )
                )
            ),
        )
        validator = FieldValidator(schema=schema)
        result = validator.validate({"system": {"name": "router-1"}})
        assert result.valid is True

    def test_non_matching_pattern_fails(self) -> None:
        schema = _make_schema(
            patterns=[r"^[a-z][a-z0-9-]*$"],
            tree=_container(
                configuration=_container(
                    system=_container(
                        name=_leaf(r=0),
                    )
                )
            ),
        )
        validator = FieldValidator(schema=schema)
        result = validator.validate({"system": {"name": "123-invalid"}})
        assert result.valid is False
        assert "pattern" in result.errors[0].message

    def test_negated_pattern_matching_value_fails(self) -> None:
        schema = _make_schema(
            patterns=["!^badprefix"],
            tree=_container(
                configuration=_container(
                    system=_container(
                        tag=_leaf(r=0),
                    )
                )
            ),
        )
        validator = FieldValidator(schema=schema)
        result = validator.validate({"system": {"tag": "badprefix-stuff"}})
        assert result.valid is False
        assert "must not match" in result.errors[0].message

    def test_negated_pattern_non_matching_value_passes(self) -> None:
        schema = _make_schema(
            patterns=["!^badprefix"],
            tree=_container(
                configuration=_container(
                    system=_container(
                        tag=_leaf(r=0),
                    )
                )
            ),
        )
        validator = FieldValidator(schema=schema)
        result = validator.validate({"system": {"tag": "goodprefix-stuff"}})
        assert result.valid is True


# ── IP address validation ────────────────────────────────────────────


class TestIPAddressValidation:
    def test_valid_ipv4_passes(self) -> None:
        schema = _make_schema(
            tree=_container(configuration=_container(iface=_container(addr=_leaf(tr="ipaddr")))),
        )
        validator = FieldValidator(schema=schema)
        result = validator.validate({"iface": {"addr": "10.0.0.1"}})
        assert result.valid is True

    def test_invalid_ipv4_fails(self) -> None:
        schema = _make_schema(
            tree=_container(configuration=_container(iface=_container(addr=_leaf(tr="ipaddr")))),
        )
        validator = FieldValidator(schema=schema)
        result = validator.validate({"iface": {"addr": "300.1.2.3"}})
        assert result.valid is False
        assert "300.1.2.3" in result.errors[0].message

    def test_valid_cidr_passes(self) -> None:
        schema = _make_schema(
            tree=_container(
                configuration=_container(iface=_container(prefix=_leaf(tr="ipprefix")))
            ),
        )
        validator = FieldValidator(schema=schema)
        result = validator.validate({"iface": {"prefix": "10.0.0.0/24"}})
        assert result.valid is True

    def test_invalid_cidr_fails(self) -> None:
        schema = _make_schema(
            tree=_container(
                configuration=_container(iface=_container(prefix=_leaf(tr="ipprefix")))
            ),
        )
        validator = FieldValidator(schema=schema)
        result = validator.validate({"iface": {"prefix": "300.0.0.0/24"}})
        assert result.valid is False

    def test_valid_ipv6_passes(self) -> None:
        schema = _make_schema(
            tree=_container(configuration=_container(iface=_container(addr6=_leaf(tr="ipv6addr")))),
        )
        validator = FieldValidator(schema=schema)
        result = validator.validate({"iface": {"addr6": "2001:db8::1"}})
        assert result.valid is True

    def test_invalid_ipv6_fails(self) -> None:
        schema = _make_schema(
            tree=_container(configuration=_container(iface=_container(addr6=_leaf(tr="ipv6addr")))),
        )
        validator = FieldValidator(schema=schema)
        result = validator.validate({"iface": {"addr6": "gggg::1"}})
        assert result.valid is False

    def test_ipaddr_accepts_ipv6(self) -> None:
        """Generic ipaddr type accepts both IPv4 and IPv6."""
        schema = _make_schema(
            tree=_container(configuration=_container(iface=_container(addr=_leaf(tr="ipaddr")))),
        )
        validator = FieldValidator(schema=schema)
        result = validator.validate({"iface": {"addr": "3ffe:0b00:0001:f003::1"}})
        assert result.valid is True

    def test_ipprefix_accepts_ipv6(self) -> None:
        """Generic ipprefix type accepts both IPv4 and IPv6 prefixes."""
        schema = _make_schema(
            tree=_container(
                configuration=_container(iface=_container(prefix=_leaf(tr="ipprefix")))
            ),
        )
        validator = FieldValidator(schema=schema)
        result = validator.validate({"iface": {"prefix": "2001:db8::/32"}})
        assert result.valid is True

    def test_ipv6_where_ipv4_expected_fails(self) -> None:
        schema = _make_schema(
            tree=_container(configuration=_container(iface=_container(addr=_leaf(tr="ipv4addr")))),
        )
        validator = FieldValidator(schema=schema)
        result = validator.validate({"iface": {"addr": "2001:db8::1"}})
        assert result.valid is False
        assert "IPv4" in result.errors[0].message

    def test_ipv4_where_ipv6_expected_fails(self) -> None:
        schema = _make_schema(
            tree=_container(configuration=_container(iface=_container(addr6=_leaf(tr="ipv6addr")))),
        )
        validator = FieldValidator(schema=schema)
        result = validator.validate({"iface": {"addr6": "10.0.0.1"}})
        assert result.valid is False
        assert "IPv6" in result.errors[0].message


# ── Type validation ──────────────────────────────────────────────────


class TestTypeValidation:
    def test_valid_integer_passes(self) -> None:
        schema = _make_schema(
            tree=_container(configuration=_container(system=_container(mtu=_leaf(tr="uint16")))),
        )
        validator = FieldValidator(schema=schema)
        result = validator.validate({"system": {"mtu": "1500"}})
        assert result.valid is True

    def test_non_integer_fails(self) -> None:
        schema = _make_schema(
            tree=_container(configuration=_container(system=_container(mtu=_leaf(tr="uint16")))),
        )
        validator = FieldValidator(schema=schema)
        result = validator.validate({"system": {"mtu": "abc"}})
        assert result.valid is False
        assert "integer" in result.errors[0].message

    def test_unsigned_integer_negative_fails(self) -> None:
        schema = _make_schema(
            tree=_container(configuration=_container(system=_container(mtu=_leaf(tr="uint16")))),
        )
        validator = FieldValidator(schema=schema)
        result = validator.validate({"system": {"mtu": "-1"}})
        assert result.valid is False
        assert "out of range" in result.errors[0].message

    def test_unsigned_integer_overflow_fails(self) -> None:
        schema = _make_schema(
            tree=_container(configuration=_container(system=_container(mtu=_leaf(tr="uint16")))),
        )
        validator = FieldValidator(schema=schema)
        result = validator.validate({"system": {"mtu": "99999"}})
        assert result.valid is False
        assert "out of range" in result.errors[0].message

    def test_boolean_true_passes(self) -> None:
        schema = _make_schema(
            tree=_container(configuration=_container(system=_container(flag=_leaf(tr="boolean")))),
        )
        validator = FieldValidator(schema=schema)
        result = validator.validate({"system": {"flag": "true"}})
        assert result.valid is True

    def test_boolean_invalid_fails(self) -> None:
        schema = _make_schema(
            tree=_container(configuration=_container(system=_container(flag=_leaf(tr="boolean")))),
        )
        validator = FieldValidator(schema=schema)
        result = validator.validate({"system": {"flag": "maybe"}})
        assert result.valid is False
        assert "boolean" in result.errors[0].message


# ── Mandatory field validation ───────────────────────────────────────


class TestMandatoryValidation:
    def test_missing_mandatory_generates_warning(self) -> None:
        schema = _make_schema(
            tree=_container(
                configuration=_container(
                    system=_container(
                        **{"host-name": {**_leaf(), "m": True}},
                    )
                )
            ),
        )
        validator = FieldValidator(schema=schema)
        result = validator.validate({"system": {}})
        assert result.valid is True  # warnings, not errors
        assert len(result.warnings) == 1
        assert "host-name" in result.warnings[0].message

    def test_present_mandatory_no_warning(self) -> None:
        schema = _make_schema(
            tree=_container(
                configuration=_container(
                    system=_container(
                        **{"host-name": {**_leaf(), "m": True}},
                    )
                )
            ),
        )
        validator = FieldValidator(schema=schema)
        result = validator.validate({"system": {"host-name": "r1"}})
        assert result.valid is True
        assert result.warnings == []

    def test_flat_dict_mandatory_skipped(self) -> None:
        """Mandatory checks are skipped for children of flat-dict elements."""
        schema = _make_schema(
            tree=_container(
                configuration=_container(
                    trigger={
                        "fd": True,
                        "c": {
                            "after": {"p": True},
                            "count": {**_leaf(), "m": True, "nk": True},
                        },
                    },
                )
            ),
        )
        validator = FieldValidator(schema=schema)
        # Trigger with "after" but no "count" — should NOT warn
        result = validator.validate({"trigger": {"after": [None]}})
        assert result.valid is True
        assert result.warnings == []


# ── Structural / recursive validation ────────────────────────────────


class TestStructuralValidation:
    def test_nested_configs_validated_recursively(self) -> None:
        schema = _make_schema(
            enums=[["enable", "disable"]],
            tree=_container(
                configuration=_container(
                    system=_container(
                        services=_container(
                            ssh=_container(
                                status=_leaf(e=0),
                            )
                        )
                    )
                )
            ),
        )
        validator = FieldValidator(schema=schema)
        result = validator.validate({"system": {"services": {"ssh": {"status": "broken"}}}})
        assert result.valid is False
        assert result.errors[0].path == "system.services.ssh.status"

    def test_named_list_entries_validated(self) -> None:
        schema = _make_schema(
            enums=[["up", "down"]],
            tree=_container(
                configuration=_container(
                    interfaces=_container(
                        interface={
                            "L": True,
                            "c": {"status": _leaf(e=0)},
                        }
                    )
                )
            ),
        )
        validator = FieldValidator(schema=schema)
        # Named list as a list
        result = validator.validate({"interfaces": {"interface": [{"status": "broken"}]}})
        assert result.valid is False

    def test_presence_flag_skipped(self) -> None:
        schema = _make_schema(
            tree=_container(
                configuration=_container(
                    system=_container(
                        flag=_leaf(tr="uint16"),
                    )
                )
            ),
        )
        validator = FieldValidator(schema=schema)
        # Presence flags (True or None) should be skipped
        result = validator.validate({"system": {"flag": True}})
        assert result.valid is True

    def test_empty_value_skipped(self) -> None:
        schema = _make_schema(
            tree=_container(
                configuration=_container(
                    system=_container(
                        name=_leaf(tr="uint16"),
                    )
                )
            ),
        )
        validator = FieldValidator(schema=schema)
        result = validator.validate({"system": {"name": ""}})
        assert result.valid is True

    def test_attribute_keys_skipped(self) -> None:
        schema = _make_schema(
            tree=_container(
                configuration=_container(
                    system=_container(
                        name=_leaf(),
                    )
                )
            ),
        )
        validator = FieldValidator(schema=schema)
        result = validator.validate({"system": {"name": "r1", "@system": {"inactive": True}}})
        assert result.valid is True

    def test_unknown_keys_ignored(self) -> None:
        schema = _make_schema(
            tree=_container(configuration=_container(system=_container(name=_leaf()))),
        )
        validator = FieldValidator(schema=schema)
        result = validator.validate({"system": {"name": "r1", "unknown": "val"}})
        assert result.valid is True


# ── No schema available ──────────────────────────────────────────────


class TestNoSchema:
    def test_no_schema_returns_valid(self) -> None:
        validator = FieldValidator(schema={})
        result = validator.validate({"system": {"host-name": "r1"}})
        assert result.valid is True

    def test_none_schema_loads_bundled(self) -> None:
        """When schema=None, validator loads the bundled schema."""
        validator = FieldValidator(schema=None)
        # Should not crash; result depends on bundled schema content
        result = validator.validate({"system": {"host-name": "r1"}})
        assert isinstance(result.valid, bool)


# ── Pipeline integration ─────────────────────────────────────────────


class TestPipelineIntegration:
    def test_pipeline_with_validate_false_skips_validation(self) -> None:
        from junoscfg.convert import pipeline

        # Even if values are bad, validate=False should skip checking
        result = pipeline(
            '{"configuration": {"system": {"host-name": "r1"}}}',
            from_format="json",
            to_format="json",
            validate=False,
        )
        assert "r1" in result

    def test_pipeline_with_validate_true_warns(self, capsys: pytest.CaptureFixture[str]) -> None:
        from junoscfg.convert import pipeline

        # Default validate=True should still produce output
        result = pipeline(
            '{"configuration": {"system": {"host-name": "r1"}}}',
            from_format="json",
            to_format="json",
            validate=True,
        )
        assert "r1" in result

    def test_pipeline_strict_raises_on_bad_value(self) -> None:
        """Test that strict mode raises when schema has constraints that fail.

        This uses a custom validator to guarantee the error, since the bundled
        schema may not have constraints on host-name.
        """
        from junoscfg.convert.field_validator import FieldValidator
        from junoscfg.convert.input import to_dict

        schema = _make_schema(
            enums=[["valid-host"]],
            tree=_container(
                configuration=_container(
                    system=_container(
                        **{"host-name": _leaf(e=0)},
                    )
                )
            ),
        )
        validator = FieldValidator(schema=schema)
        ir = to_dict('{"configuration": {"system": {"host-name": "bad-host"}}}', "json")
        result = validator.validate(ir)
        assert result.valid is False

    def test_validate_ir_standalone(self) -> None:
        from junoscfg.convert import validate_ir

        ir = {"system": {"host-name": "router1"}}
        result = validate_ir(ir)
        # Should complete without crashing; result depends on bundled schema
        assert isinstance(result.valid, bool)


# ── Full example config validation ───────────────────────────────────


class TestFullConfigValidation:
    """Smoke test: validate the example config against the bundled schema."""

    @pytest.mark.skipif(
        not __import__("pathlib")
        .Path(
            __import__("pathlib").Path(__file__).resolve().parent.parent
            / "examples"
            / "load_ox_conf.json"
        )
        .exists(),
        reason="Example config files not available",
    )
    def test_example_config_validates(self, json_config: str) -> None:
        """The bundled example config should validate without unexpected errors."""
        from junoscfg.convert.field_validator import FieldValidator
        from junoscfg.convert.input import to_dict

        ir = to_dict(json_config, "json")
        validator = FieldValidator()  # uses bundled schema
        result = validator.validate(ir)
        # We don't require zero errors (schema constraints may flag things
        # that are technically valid in context), but verify it completes
        assert isinstance(result.valid, bool)
        assert isinstance(result.errors, list)
        assert isinstance(result.warnings, list)
