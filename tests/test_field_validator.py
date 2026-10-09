"""Tests for field-level validation of Junos configuration values."""

from __future__ import annotations

import pytest

from junoscfg.convert.field_validator import (
    UNPLACED,
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


class TestAnUnmodelledStatementIsReported:
    """A key the schema does not know is an error, never silence.

    The walk used to `continue` past it, which is how a statement the set
    reader could not place -- kept verbatim as one key -- reached JSON and
    YAML output with no word said, and how `{"interfaces": {"interface":
    [{"name": "x", "no-such-child": "y"}]}}` validated. The IR carries keys
    the schema does not name by design, and each of those is exempt by its
    rule, not by a list: a list entry's key, a flat entry's `_v` values, an
    `@` attribute, a universal statement, and the spelling of a folded
    on/off switch.
    """

    @staticmethod
    def _system(**children: dict) -> dict:
        return _make_schema(
            tree=_container(configuration=_container(system=_container(**children)))
        )

    def test_an_unknown_key_is_an_error(self) -> None:
        result = FieldValidator(schema=self._system(name=_leaf())).validate(
            {"system": {"name": "r1", "nonsense alpha beta": True}}
        )
        assert result.valid is False
        assert [e.path for e in result.errors] == ["system"]
        assert "nonsense alpha beta" in result.errors[0].message

    def test_a_key_that_merely_starts_with_an_underscore_is(self) -> None:
        """Only `_v0`, `_v1`... is a reader's; `_bogus alpha` is a statement."""
        result = FieldValidator(schema=self._system(name=_leaf())).validate(
            {"system": {"_bogus alpha beta": True}}
        )
        assert [e.value for e in result.errors] == ["_bogus alpha beta"]

    def test_the_configuration_wrapper_is_stripped_not_reported(self) -> None:
        """Passed whole, the IR used to validate nothing and say so with silence."""
        validator = FieldValidator(schema=self._system(name=_leaf(e=0)))
        validator._enums = [["r1"]]  # noqa: SLF001
        wrapped = validator.validate({"configuration": {"system": {"name": "wrong"}}})
        bare = validator.validate({"system": {"name": "wrong"}})
        assert [e.path for e in wrapped.errors] == [e.path for e in bare.errors] == ["system.name"]

    def test_the_message_names_the_list_entry(self) -> None:
        schema = _make_schema(
            tree=_container(
                configuration=_container(
                    interfaces=_container(interface={"L": True, "c": {"mtu": _leaf()}})
                )
            )
        )
        result = FieldValidator(schema=schema).validate(
            {"interfaces": {"interface": [{"name": "ge-0/0/0", "nonsense alpha": True}]}}
        )
        assert result.errors[0].message.startswith(
            "'nonsense alpha' under interface ge-0/0/0 could not be placed in the schema"
        )

    def test_a_list_entrys_key_is_not(self) -> None:
        schema = _make_schema(
            tree=_container(
                configuration=_container(
                    interfaces=_container(interface={"L": True, "c": {"mtu": _leaf()}})
                )
            )
        )
        result = FieldValidator(schema=schema).validate(
            {"interfaces": {"interface": [{"name": "ge-0/0/0", "mtu": "9000"}]}}
        )
        assert result.valid is True, result.errors

    def test_a_flat_entrys_key_and_values_are_not(self) -> None:
        """`route-filter` keys on `address` and its match type; `attributes-match`
        on its three fields. Rewritten to the keyed form (identifier-key-fields,
        owner answer 1): the key fields are the tree's `k` and its children."""
        match_fields = ["from-event-attribute", "condition", "to-event-attribute-value"]
        schema = self._system(
            **{
                "route-filter": {
                    "L": True,
                    "o": True,
                    "k": ["address", ["exact"]],
                    "c": {"address": {"l": True, "nk": True}, "exact": {"p": True}},
                },
                "attributes-match": {
                    "L": True,
                    "k": match_fields,
                    "c": {name: {"l": True, "nk": True} for name in match_fields},
                },
            }
        )
        result = FieldValidator(schema=schema).validate(
            {
                "system": {
                    "route-filter": [{"address": "10.0.0.0/8", "exact": [None]}],
                    "attributes-match": [
                        {
                            "from-event-attribute": "a",
                            "condition": "equals",
                            "to-event-attribute-value": "b",
                        }
                    ],
                }
            }
        )
        assert result.valid is True, result.errors

    def test_an_overridden_entry_key_is_not(self) -> None:
        """`then community` keys on its action and `community-name`, from the
        tree's `k` where `ENTRY_KEY_OVERRIDES` used to name it."""
        schema = self._system(
            community={
                "L": True,
                "o": True,
                "k": [["add"], "community-name"],
                "c": {"add": {"p": True}, "community-name": {"l": True, "nk": True}},
            }
        )
        result = FieldValidator(schema=schema).validate(
            {"system": {"community": [{"community-name": "C", "add": [None]}]}}
        )
        assert result.valid is True, result.errors

    def test_an_incomplete_statement_is_unplaced(self) -> None:
        """A partial key reaches validation whole and is reported `UNPLACED`.

        Spec: identifier-key-fields, conversion/entry-keys, "A statement the
        reader cannot complete is kept whole". The reader used to make
        `{"name": "as-list"}` of it, which validated."""
        from junoscfg.convert import validate_ir
        from tests.keyed_entries import TERM, set_ir

        ir = set_ir(f"{TERM} from as-path-neighbors as-list")
        result = validate_ir({"configuration": ir})
        assert [e.value for e in result.errors] == ["as-path-neighbors as-list"]
        assert result.errors[0].path.endswith("term.from")
        assert result.errors[0].message.startswith("'as-path-neighbors as-list'")
        assert result.errors[0].expected == UNPLACED

    def test_a_universal_statement_is_not(self) -> None:
        result = FieldValidator(schema=self._system(name=_leaf())).validate(
            {
                "system": {
                    "name": "r1",
                    "apply-groups": ["g1"],
                    "apply-macro": [{"name": "m", "data": []}],
                }
            }
        )
        assert result.valid is True, result.errors

    def test_a_switch_spelling_is_not(self) -> None:
        """`disable` is written for the node `enable-disable`."""
        schema = _make_schema(
            enums=[["disable"]],
            tree=_container(
                configuration=_container(
                    system=_container(**{"enable-disable": _leaf(nk=True, e=0)})
                )
            ),
        )
        result = FieldValidator(schema=schema).validate({"system": {"disable": [None]}})
        assert result.valid is True, result.errors

    def test_a_switch_spelling_satisfies_its_mandatory_node(self) -> None:
        """`watchdog enable` carries the mandatory `enable-disable`, by spelling.

        The warning this raised was false and went unseen: the pipeline prints
        warnings only beside an error, and reporting unmodelled statements
        made it visible 21 times on Juniper's published designs."""
        schema = _make_schema(
            enums=[["disable"]],
            tree=_container(
                configuration=_container(
                    watchdog=_container(**{"enable-disable": _leaf(nk=True, e=0, m=True)})
                )
            ),
        )
        result = FieldValidator(schema=schema).validate({"watchdog": {"enable": [None]}})
        assert result.warnings == [], result.warnings


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

    def test_an_unmodelled_statement_warns_and_fails_strict(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """What was silently discarded is kept, diagnosed, and fatal under strict."""
        from junoscfg.convert import pipeline, pipeline_result

        source = "set interfaces ge-0/0/0 nonsense alpha beta gamma"
        result = pipeline_result(source, from_format="set", to_format="set")
        assert result.output.strip() == source
        assert capsys.readouterr().err == ""
        err = "\n".join(item.render() for item in result.diagnostics)
        assert "field-validate: interfaces: " in err
        # `interfaces` is transparent, so the path names it as Junos does
        assert "'nonsense alpha beta gamma' under interfaces ge-0/0/0 could not be placed" in err
        with pytest.raises(FieldValidationError):
            pipeline(source, from_format="set", to_format="json", strict=True)

    def test_anonymization_refuses_what_it_cannot_see(self) -> None:
        """A kept statement would leave verbatim, address and all, where the
        reader used to drop it: the anonymizer never rewrites a key the
        schema does not name. So it fails, whatever validate and strict say."""
        from junoscfg.anonymize.config import AnonymizeConfig
        from junoscfg.convert import pipeline

        cfg = AnonymizeConfig(ips=True, salt="s")
        source = "set protocols bgp neighbor 203.0.114.9 description peer"
        with pytest.raises(FieldValidationError, match="cannot anonymize"):
            pipeline(source, from_format="set", to_format="set", anon_config=cfg, validate=False)
        modelled = "set protocols bgp group G neighbor 203.0.114.9 description peer"
        out = pipeline(modelled, from_format="set", to_format="set", anon_config=cfg)
        assert "203.0.114.9" not in out

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


# ── identifier-key-fields: keyed entries against the bundled tree ────
#
# Spec: openspec/changes/identifier-key-fields/specs/validation/keyed-entries,
# "Field validation checks each key field as a leaf". Through `validate_ir`,
# the door `convert_config(validate=True)` uses.


def _policy(where: str, entries: dict, *, term: bool = True) -> dict:
    body = {where: entries}
    statement: dict = {"name": "SAMPLE-POLICY"}
    if term:
        statement["term"] = [{"name": "T1", **body}]
    else:
        statement.update(body)
    return {"policy-options": {"policy-statement": [statement]}}


def _event(*matches: dict) -> dict:
    return {
        "event-options": {
            "policy": [{"name": "SAMPLE-EVENT-POLICY", "attributes-match": list(matches)}]
        }
    }


_MATCH = {
    "from-event-attribute": "ping.test-owner",
    "condition": "matches",
    "to-event-attribute-value": "^uptime$",
}


class TestKeyedEntries:
    @staticmethod
    def _errors(ir: dict) -> list:
        from junoscfg.convert import validate_ir

        return validate_ir({"configuration": ir}).errors

    @pytest.mark.parametrize("term", [True, False])
    @pytest.mark.parametrize("slot", ["as-path-neighbors", "as-path-origins", "as-path-transits"])
    def test_a_device_keyed_as_list_reference_is_clean(self, slot: str, term: bool) -> None:
        for list_type in ("as-list", "as-list-group"):
            entry = {"list-type": list_type, "list-name": "SAMPLE-AS-LIST"}
            assert self._errors(_policy("from", {slot: [entry]}, term=term)) == []
        grouped = {"groups": [{"name": "SAMPLE-GROUP", **_policy("from", {slot: [entry]})}]}
        assert self._errors(grouped) == []

    def test_a_key_value_is_checked_against_its_leaf(self) -> None:
        """`1` is outside `list-type`'s enum; the device rejects it at `set`."""
        bad = {"list-type": "1", "list-name": "SAMPLE-AS-LIST"}
        errors = self._errors(_policy("from", {"as-path-neighbors": [bad]}))
        assert len(errors) == 1
        assert errors[0].path.endswith("as-path-neighbors.list-type")
        assert errors[0].value == "1"
        assert errors[0].expected != UNPLACED

        errors = self._errors(_event(dict(_MATCH, condition="resembles")))
        assert [e.path.rsplit(".", 1)[-1] for e in errors] == ["condition"]

    @pytest.mark.parametrize(
        ("ir", "key"),
        [
            (_policy("from", {"as-path-neighbors": [{"name": "as-list"}]}), "name"),
            (
                _policy(
                    "from",
                    {
                        "as-path-neighbors": [
                            {"list-type": "as-list", "list-name": "SAMPLE-AS-LIST", "name": "x"}
                        ]
                    },
                ),
                "name",
            ),
            (_event({"name": "ping.test-owner", "_v0": "matches", "_v1": "^uptime$"}), "_v0"),
            (_event({"name": "ping.test-owner", "_v0": "matches", "_v1": "^uptime$"}), "_v1"),
            (
                _policy("from", {"source-address-filter": [{"name": "198.51.100.0/24"}]}),
                "name",
            ),
        ],
    )
    def test_name_under_a_list_keyed_otherwise_is_unplaced(self, ir: dict, key: str) -> None:
        errors = self._errors(ir)
        assert key in [e.value for e in errors]
        placed = next(e for e in errors if e.value == key)
        assert placed.expected == UNPLACED

    def test_attributes_match_takes_its_three_fields(self) -> None:
        spaced = dict(_MATCH, **{"to-event-attribute-value": "^up time$"})
        for condition in ("equals", "starts-with", "matches"):
            assert self._errors(_event(dict(_MATCH, condition=condition), spaced)) == []

    def test_a_route_filter_action_is_clean(self) -> None:
        for slot in ("route-filter", "source-address-filter"):
            for match in ("exact", "orlonger", "longer"):
                entry = {"address": "198.51.100.0/24", match: [None], "accept": [None]}
                assert self._errors(_policy("from", {slot: [entry]})) == [], (slot, match)
        plf = {"list_name": "SAMPLE-PL", "orlonger": [None], "accept": [None]}
        assert self._errors(_policy("from", {"prefix-list-filter": [plf]})) == []
        for action in ("add", "delete", "set"):
            community = {action: [None], "community-name": "SAMPLE-COMM"}
            assert self._errors(_policy("then", {"community": [community]})) == [], action


class TestAnIncompleteStatementIsUnplaced:
    """Kept whole by the reader, reported by validation; spec: entry-keys."""

    @pytest.mark.parametrize(
        "line",
        [
            "set policy-options policy-statement SAMPLE-POLICY term T1 from as-path-neighbors "
            "as-list",
            "set policy-options policy-statement SAMPLE-POLICY term T1 from as-path-neighbors "
            "as-list SAMPLE-AS-LIST SAMPLE-EXTRA",
            "set policy-options policy-statement SAMPLE-POLICY term T1 from route-filter "
            "198.51.100.0/24 next-policy",
            "set apply-groups SAMPLE-GROUP SAMPLE-GROUP-2",
            "set event-options policy SAMPLE-EVENT-POLICY attributes-match ping.test-owner matches",
        ],
    )
    def test_each_door_reports_it(self, line: str) -> None:
        from junoscfg import Format, convert_config
        from junoscfg.convert import validate_ir
        from tests.keyed_entries import set_ir

        result = validate_ir({"configuration": set_ir(line)})
        assert not result.valid
        assert any(e.expected == UNPLACED for e in result.errors), result.errors
        with pytest.raises(FieldValidationError):
            convert_config(line, from_format=Format.SET, to_format=Format.JSON, strict=True)
