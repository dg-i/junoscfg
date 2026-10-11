"""Field validation: leaf values in the IR against the schema's constraints.

Through `junoscfg.convert.validate_ir`, the door `convert_config(validate=True)`
and the pipeline use. A case that needs its own schema writes the structure
tree artifact, `junos-structure-tree.json` in the format
`docs/architecture/schema-internals.md` documents (`_enums` and `_patterns`
are its dedup tables), into an artifacts directory and selects it with
`junoscfg.display.artifacts_dir`, as `--artifacts` does. One case builds that
tree from a small XSD instead, to show the generator and the validator agree.
The keyed-entry cases validate against the shipped tree.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

import pytest
import yaml

from junoscfg import Format, convert_config, convert_config_result
from junoscfg.anonymize import AnonymizeConfig
from junoscfg.convert import (
    UNPLACED,
    FieldError,
    FieldValidationError,
    FieldValidationResult,
    pipeline,
    pipeline_result,
    to_dict,
    validate_ir,
)
from junoscfg.display import artifacts_dir
from tests.support.artifacts import using_tree
from tests.support.devices import placed_only
from tests.support.keyed_entries import TERM, set_ir, structure_tree

if TYPE_CHECKING:
    from collections.abc import Callable
    from contextlib import AbstractContextManager
    from pathlib import Path

    #: Validate an IR against a structure tree: ``validate(tree, config)``.
    Validate = Callable[[dict[str, Any], dict[str, Any]], FieldValidationResult]


@pytest.fixture
def use_tree(tmp_path: Path) -> Callable[[dict[str, Any]], AbstractContextManager[Path]]:
    """Convert and validate against *tree*, written as the structure tree artifact."""
    return lambda tree: using_tree(tmp_path, tree)


@pytest.fixture
def validate(use_tree: Callable[[dict[str, Any]], AbstractContextManager[Path]]) -> Validate:
    """`validate_ir` against a structure tree written for the call."""

    def run(tree: dict[str, Any], config: dict[str, Any]) -> FieldValidationResult:
        with use_tree(tree):
            return validate_ir(config)

    return run


def _make_schema(
    *,
    enums: list[list[str]] | None = None,
    patterns: list[str] | None = None,
    tree: dict | None = None,
) -> dict:
    """A minimal structure tree with its `_enums` and `_patterns` tables."""
    schema: dict = {}
    if tree:
        schema.update(tree)
    if enums:
        schema["_enums"] = enums
    if patterns:
        schema["_patterns"] = patterns
    return schema


def _leaf(**kwargs: object) -> dict:
    """A leaf node."""
    d: dict = {"l": True}
    d.update(kwargs)
    return d


def _container(**children: dict) -> dict:
    """A container node."""
    return {"c": children}


# ── The result types ─────────────────────────────────────────────────


class TestFieldError:
    """What `validate_ir` reports per finding: where, what, the value, and
    what was expected (`UNPLACED` for a statement the schema cannot place)."""

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
    """Errors make a result invalid; warnings alone do not."""

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
    """The strict-mode exception counts the errors and names the first five."""

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
    def test_value_in_allowed_set_passes(self, validate: Validate) -> None:
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
        result = validate(schema, {"system": {"option": "enable"}})
        assert result.valid is True
        assert result.errors == []

    def test_value_not_in_set_fails(self, validate: Validate) -> None:
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
        result = validate(schema, {"system": {"option": "maybe"}})
        assert result.valid is False
        assert len(result.errors) == 1
        assert "maybe" in result.errors[0].message
        assert "enable" in result.errors[0].message

    def test_large_enum_shows_truncated_list(self, validate: Validate) -> None:
        values = [f"val{i}" for i in range(20)]
        schema = _make_schema(
            enums=[values],
            tree=_container(configuration=_container(level=_container(choice=_leaf(e=0)))),
        )
        result = validate(schema, {"level": {"choice": "nonexistent"}})
        assert result.valid is False
        assert "20 total" in result.errors[0].message

    def test_list_value_validates_each_element(self, validate: Validate) -> None:
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
        result = validate(schema, {"system": {"ciphers": ["aes128-ctr", "aes256-ctr"]}})
        assert result.valid is True
        assert result.errors == []

    def test_list_value_reports_invalid_element(self, validate: Validate) -> None:
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
        result = validate(schema, {"system": {"ciphers": ["aes128-ctr", "bad-cipher"]}})
        assert result.valid is False
        assert len(result.errors) == 1
        assert "bad-cipher" in result.errors[0].message

    def test_enum_with_type_fallthrough(self, validate: Validate) -> None:
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
        # Numeric port 179 is not in the enum, but is a valid uint16
        result = validate(schema, {"system": {"port": "179"}})
        assert result.valid is True

    def test_enum_with_pattern_fallthrough(self, validate: Validate) -> None:
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
        # Port range "33434-33464" is not in enum, but matches the pattern
        result = validate(schema, {"system": {"port": "33434-33464"}})
        assert result.valid is True

    def test_enum_only_accepts_numeric_value(self, validate: Validate) -> None:
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
        result = validate(schema, {"system": {"port": "179"}})
        assert result.valid is True

    def test_enum_only_accepts_numeric_range(self, validate: Validate) -> None:
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
        result = validate(schema, {"system": {"port": "33434-33464"}})
        assert result.valid is True

    def test_enum_with_name_placeholder_accepts_string(self, validate: Validate) -> None:
        """Enum containing 'name' accepts arbitrary string values (XSD union)."""
        schema = _make_schema(
            enums=[["all", "name"]],
            tree=_container(
                configuration=_container(
                    vlan=_container(members=_leaf(e=0)),
                )
            ),
        )
        result = validate(schema, {"vlan": {"members": "VX3001020"}})
        assert result.valid is True

    def test_enum_with_name_placeholder_still_accepts_literal(self, validate: Validate) -> None:
        """Enum containing 'name' still accepts the literal keyword 'all'."""
        schema = _make_schema(
            enums=[["all", "name"]],
            tree=_container(
                configuration=_container(
                    vlan=_container(members=_leaf(e=0)),
                )
            ),
        )
        result = validate(schema, {"vlan": {"members": "all"}})
        assert result.valid is True

    def test_enum_with_value_placeholder_accepts_string(self, validate: Validate) -> None:
        """Enum containing 'value' accepts arbitrary values (XSD union)."""
        schema = _make_schema(
            enums=[["auto", "value"]],
            tree=_container(
                configuration=_container(
                    shdsl=_container(line_rate=_leaf(e=0)),
                )
            ),
        )
        result = validate(schema, {"shdsl": {"line_rate": "192"}})
        assert result.valid is True

    def test_enum_with_suffix_name_placeholder_accepts_string(self, validate: Validate) -> None:
        """Enum containing '*-name' suffix accepts arbitrary instance names."""
        schema = _make_schema(
            enums=[["default", "routing-instance-name"]],
            tree=_container(
                configuration=_container(
                    routing=_container(instance=_leaf(e=0)),
                )
            ),
        )
        result = validate(schema, {"routing": {"instance": "vpn-1"}})
        assert result.valid is True

    def test_enum_with_suffix_id_placeholder_accepts_string(self, validate: Validate) -> None:
        """Enum containing '*-id' suffix accepts arbitrary identifiers."""
        schema = _make_schema(
            enums=[["none", "vlan-id"]],
            tree=_container(
                configuration=_container(
                    bridge=_container(domain=_leaf(e=0)),
                )
            ),
        )
        result = validate(schema, {"bridge": {"domain": "100"}})
        assert result.valid is True

    def test_enum_without_placeholder_still_rejects(self, validate: Validate) -> None:
        """Enum without any placeholder values still rejects unknown strings."""
        schema = _make_schema(
            enums=[["enable", "disable"]],
            tree=_container(
                configuration=_container(
                    system=_container(option=_leaf(e=0)),
                )
            ),
        )
        result = validate(schema, {"system": {"option": "VX3001020"}})
        assert result.valid is False

    def test_enum_only_still_rejects_bad_values(self, validate: Validate) -> None:
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
        result = validate(schema, {"system": {"option": "maybe"}})
        assert result.valid is False


# ── Pattern validation ───────────────────────────────────────────────


class TestPatternValidation:
    def test_matching_pattern_passes(self, validate: Validate) -> None:
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
        result = validate(schema, {"system": {"name": "router-1"}})
        assert result.valid is True

    def test_non_matching_pattern_fails(self, validate: Validate) -> None:
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
        result = validate(schema, {"system": {"name": "123-invalid"}})
        assert result.valid is False
        assert "pattern" in result.errors[0].message

    def test_negated_pattern_matching_value_fails(self, validate: Validate) -> None:
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
        result = validate(schema, {"system": {"tag": "badprefix-stuff"}})
        assert result.valid is False
        assert "must not match" in result.errors[0].message

    def test_negated_pattern_non_matching_value_passes(self, validate: Validate) -> None:
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
        result = validate(schema, {"system": {"tag": "goodprefix-stuff"}})
        assert result.valid is True


# ── IP address validation ────────────────────────────────────────────


class TestIPAddressValidation:
    def test_anonymization_type_does_not_validate_a_template_value(
        self, validate: Validate
    ) -> None:
        schema = _make_schema(
            tree=_container(
                configuration=_container(iface=_container(prefix=_leaf(atr="ipprefix")))
            )
        )
        result = validate(schema, {"iface": {"prefix": "$ROUTE_PREFIX"}})
        assert result.errors == []
        assert result.warnings == []

    def test_valid_ipv4_passes(self, validate: Validate) -> None:
        schema = _make_schema(
            tree=_container(configuration=_container(iface=_container(addr=_leaf(tr="ipaddr")))),
        )
        result = validate(schema, {"iface": {"addr": "10.0.0.1"}})
        assert result.valid is True

    def test_invalid_ipv4_fails(self, validate: Validate) -> None:
        schema = _make_schema(
            tree=_container(configuration=_container(iface=_container(addr=_leaf(tr="ipaddr")))),
        )
        result = validate(schema, {"iface": {"addr": "300.1.2.3"}})
        assert result.valid is False
        assert "300.1.2.3" in result.errors[0].message

    def test_valid_cidr_passes(self, validate: Validate) -> None:
        schema = _make_schema(
            tree=_container(
                configuration=_container(iface=_container(prefix=_leaf(tr="ipprefix")))
            ),
        )
        result = validate(schema, {"iface": {"prefix": "10.0.0.0/24"}})
        assert result.valid is True

    def test_invalid_cidr_fails(self, validate: Validate) -> None:
        schema = _make_schema(
            tree=_container(
                configuration=_container(iface=_container(prefix=_leaf(tr="ipprefix")))
            ),
        )
        result = validate(schema, {"iface": {"prefix": "300.0.0.0/24"}})
        assert result.valid is False

    def test_valid_ipv6_passes(self, validate: Validate) -> None:
        schema = _make_schema(
            tree=_container(configuration=_container(iface=_container(addr6=_leaf(tr="ipv6addr")))),
        )
        result = validate(schema, {"iface": {"addr6": "2001:db8::1"}})
        assert result.valid is True

    def test_invalid_ipv6_fails(self, validate: Validate) -> None:
        schema = _make_schema(
            tree=_container(configuration=_container(iface=_container(addr6=_leaf(tr="ipv6addr")))),
        )
        result = validate(schema, {"iface": {"addr6": "gggg::1"}})
        assert result.valid is False

    def test_ipaddr_accepts_ipv6(self, validate: Validate) -> None:
        """Generic ipaddr type accepts both IPv4 and IPv6."""
        schema = _make_schema(
            tree=_container(configuration=_container(iface=_container(addr=_leaf(tr="ipaddr")))),
        )
        result = validate(schema, {"iface": {"addr": "3ffe:0b00:0001:f003::1"}})
        assert result.valid is True

    def test_ipprefix_accepts_ipv6(self, validate: Validate) -> None:
        """Generic ipprefix type accepts both IPv4 and IPv6 prefixes."""
        schema = _make_schema(
            tree=_container(
                configuration=_container(iface=_container(prefix=_leaf(tr="ipprefix")))
            ),
        )
        result = validate(schema, {"iface": {"prefix": "2001:db8::/32"}})
        assert result.valid is True

    def test_ipv6_where_ipv4_expected_fails(self, validate: Validate) -> None:
        schema = _make_schema(
            tree=_container(configuration=_container(iface=_container(addr=_leaf(tr="ipv4addr")))),
        )
        result = validate(schema, {"iface": {"addr": "2001:db8::1"}})
        assert result.valid is False
        assert "IPv4" in result.errors[0].message

    def test_ipv4_where_ipv6_expected_fails(self, validate: Validate) -> None:
        schema = _make_schema(
            tree=_container(configuration=_container(iface=_container(addr6=_leaf(tr="ipv6addr")))),
        )
        result = validate(schema, {"iface": {"addr6": "10.0.0.1"}})
        assert result.valid is False
        assert "IPv6" in result.errors[0].message


# ── Type validation ──────────────────────────────────────────────────


class TestTypeValidation:
    def test_valid_integer_passes(self, validate: Validate) -> None:
        schema = _make_schema(
            tree=_container(configuration=_container(system=_container(mtu=_leaf(tr="uint16")))),
        )
        result = validate(schema, {"system": {"mtu": "1500"}})
        assert result.valid is True

    def test_non_integer_fails(self, validate: Validate) -> None:
        schema = _make_schema(
            tree=_container(configuration=_container(system=_container(mtu=_leaf(tr="uint16")))),
        )
        result = validate(schema, {"system": {"mtu": "abc"}})
        assert result.valid is False
        assert "integer" in result.errors[0].message

    def test_unsigned_integer_negative_fails(self, validate: Validate) -> None:
        schema = _make_schema(
            tree=_container(configuration=_container(system=_container(mtu=_leaf(tr="uint16")))),
        )
        result = validate(schema, {"system": {"mtu": "-1"}})
        assert result.valid is False
        assert "out of range" in result.errors[0].message

    def test_unsigned_integer_overflow_fails(self, validate: Validate) -> None:
        schema = _make_schema(
            tree=_container(configuration=_container(system=_container(mtu=_leaf(tr="uint16")))),
        )
        result = validate(schema, {"system": {"mtu": "99999"}})
        assert result.valid is False
        assert "out of range" in result.errors[0].message

    def test_boolean_true_passes(self, validate: Validate) -> None:
        schema = _make_schema(
            tree=_container(configuration=_container(system=_container(flag=_leaf(tr="boolean")))),
        )
        result = validate(schema, {"system": {"flag": "true"}})
        assert result.valid is True

    def test_boolean_invalid_fails(self, validate: Validate) -> None:
        schema = _make_schema(
            tree=_container(configuration=_container(system=_container(flag=_leaf(tr="boolean")))),
        )
        result = validate(schema, {"system": {"flag": "maybe"}})
        assert result.valid is False
        assert "boolean" in result.errors[0].message


# ── Mandatory field validation ───────────────────────────────────────


class TestMandatoryValidation:
    def test_missing_mandatory_generates_warning(self, validate: Validate) -> None:
        schema = _make_schema(
            tree=_container(
                configuration=_container(
                    system=_container(
                        **{"host-name": {**_leaf(), "m": True}},
                    )
                )
            ),
        )
        result = validate(schema, {"system": {}})
        assert result.valid is True  # warnings, not errors
        assert len(result.warnings) == 1
        assert "host-name" in result.warnings[0].message

    def test_present_mandatory_no_warning(self, validate: Validate) -> None:
        schema = _make_schema(
            tree=_container(
                configuration=_container(
                    system=_container(
                        **{"host-name": {**_leaf(), "m": True}},
                    )
                )
            ),
        )
        result = validate(schema, {"system": {"host-name": "r1"}})
        assert result.valid is True
        assert result.warnings == []

    def test_flat_dict_mandatory_skipped(self, validate: Validate) -> None:
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
        # Trigger with "after" but no "count" — should NOT warn
        result = validate(schema, {"trigger": {"after": [None]}})
        assert result.valid is True
        assert result.warnings == []


# ── Structural / recursive validation ────────────────────────────────


class TestStructuralValidation:
    def test_nested_configs_validated_recursively(self, validate: Validate) -> None:
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
        result = validate(schema, {"system": {"services": {"ssh": {"status": "broken"}}}})
        assert result.valid is False
        assert result.errors[0].path == "system.services.ssh.status"

    def test_named_list_entries_validated(self, validate: Validate) -> None:
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
        # Named list as a list
        result = validate(schema, {"interfaces": {"interface": [{"status": "broken"}]}})
        assert result.valid is False

    def test_presence_flag_skipped(self, validate: Validate) -> None:
        schema = _make_schema(
            tree=_container(
                configuration=_container(
                    system=_container(
                        flag=_leaf(tr="uint16"),
                    )
                )
            ),
        )
        # Presence flags (True or None) should be skipped
        result = validate(schema, {"system": {"flag": True}})
        assert result.valid is True

    def test_empty_value_skipped(self, validate: Validate) -> None:
        schema = _make_schema(
            tree=_container(
                configuration=_container(
                    system=_container(
                        name=_leaf(tr="uint16"),
                    )
                )
            ),
        )
        result = validate(schema, {"system": {"name": ""}})
        assert result.valid is True

    def test_attribute_keys_skipped(self, validate: Validate) -> None:
        schema = _make_schema(
            tree=_container(
                configuration=_container(
                    system=_container(
                        name=_leaf(),
                    )
                )
            ),
        )
        result = validate(schema, {"system": {"name": "r1", "@system": {"inactive": True}}})
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

    def test_an_unknown_key_is_an_error(self, validate: Validate) -> None:
        result = validate(
            self._system(name=_leaf()), {"system": {"name": "r1", "nonsense alpha beta": True}}
        )
        assert result.valid is False
        assert [e.path for e in result.errors] == ["system"]
        assert "nonsense alpha beta" in result.errors[0].message

    def test_a_key_that_merely_starts_with_an_underscore_is(self, validate: Validate) -> None:
        """Only `_v0`, `_v1`... is a reader's; `_bogus alpha` is a statement."""
        result = validate(self._system(name=_leaf()), {"system": {"_bogus alpha beta": True}})
        assert [e.value for e in result.errors] == ["_bogus alpha beta"]

    def test_the_configuration_wrapper_is_stripped_not_reported(self, validate: Validate) -> None:
        """Passed whole, the IR used to validate nothing and say so with silence."""
        schema = {**self._system(name=_leaf(e=0)), "_enums": [["r1"]]}
        wrapped = validate(schema, {"configuration": {"system": {"name": "wrong"}}})
        bare = validate(schema, {"system": {"name": "wrong"}})
        assert [e.path for e in wrapped.errors] == [e.path for e in bare.errors] == ["system.name"]

    def test_the_message_names_the_list_entry(self, validate: Validate) -> None:
        schema = _make_schema(
            tree=_container(
                configuration=_container(
                    interfaces=_container(interface={"L": True, "c": {"mtu": _leaf()}})
                )
            )
        )
        result = validate(
            schema, {"interfaces": {"interface": [{"name": "ge-0/0/0", "nonsense alpha": True}]}}
        )
        assert result.errors[0].message.startswith(
            "'nonsense alpha' under interface ge-0/0/0 could not be placed in the schema"
        )

    def test_a_list_entrys_key_is_not(self, validate: Validate) -> None:
        schema = _make_schema(
            tree=_container(
                configuration=_container(
                    interfaces=_container(interface={"L": True, "c": {"mtu": _leaf()}})
                )
            )
        )
        result = validate(
            schema, {"interfaces": {"interface": [{"name": "ge-0/0/0", "mtu": "9000"}]}}
        )
        assert result.valid is True, result.errors

    def test_a_flat_entrys_key_and_values_are_not(self, validate: Validate) -> None:
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
        result = validate(
            schema,
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
            },
        )
        assert result.valid is True, result.errors

    def test_an_overridden_entry_key_is_not(self, validate: Validate) -> None:
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
        result = validate(
            schema, {"system": {"community": [{"community-name": "C", "add": [None]}]}}
        )
        assert result.valid is True, result.errors

    def test_an_incomplete_statement_is_unplaced(self) -> None:
        """A partial key reaches validation whole and is reported `UNPLACED`.

        Spec: identifier-key-fields, conversion/entry-keys, "A statement the
        reader cannot complete is kept whole". The reader used to make
        `{"name": "as-list"}` of it, which validated."""

        ir = set_ir(f"{TERM} from as-path-neighbors as-list")
        result = validate_ir({"configuration": ir})
        assert [e.value for e in result.errors] == ["as-path-neighbors as-list"]
        assert result.errors[0].path.endswith("term.from")
        assert result.errors[0].message.startswith("'as-path-neighbors as-list'")
        assert result.errors[0].expected == UNPLACED

    def test_a_universal_statement_is_not(self, validate: Validate) -> None:
        result = validate(
            self._system(name=_leaf()),
            {
                "system": {
                    "name": "r1",
                    "apply-groups": ["g1"],
                    "apply-macro": [{"name": "m", "data": []}],
                }
            },
        )
        assert result.valid is True, result.errors

    def test_a_switch_spelling_is_not(self, validate: Validate) -> None:
        """`disable` is written for the node `enable-disable`."""
        schema = _make_schema(
            enums=[["disable"]],
            tree=_container(
                configuration=_container(
                    system=_container(**{"enable-disable": _leaf(nk=True, e=0)})
                )
            ),
        )
        result = validate(schema, {"system": {"disable": [None]}})
        assert result.valid is True, result.errors

    def test_a_switch_spelling_satisfies_its_mandatory_node(self, validate: Validate) -> None:
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
        result = validate(schema, {"watchdog": {"enable": [None]}})
        assert result.warnings == [], result.warnings


# ── The schema in use ────────────────────────────────────────────────


class TestNoSchema:
    """An empty tree constrains nothing; without a chosen directory the
    shipped tree is the schema."""

    def test_no_schema_returns_valid(self, validate: Validate) -> None:
        assert validate({}, {"system": {"host-name": "r1"}}).valid is True

    @pytest.mark.parametrize("host_name", ["r1", "router1"])
    def test_the_shipped_tree_is_the_default(self, host_name: str) -> None:
        result = validate_ir({"system": {"host-name": host_name}})
        assert result.errors == []
        assert result.warnings == []


class TestTheExampleConfigurationValidates:
    """`examples/junoscfg-oracle.json`, what a vMX printed with `| display json`.

    A device loaded every statement of it, so every finding is junoscfg's or
    the example's own. The one the example earns: `access profile PROF-1
    radius-server` carries no `secret`, which the schema marks mandatory (the
    device loaded it uncommitted, and mandatory is checked at commit).
    """

    RADIUS_SECRET = ("access.profile.radius-server.secret", "Missing mandatory field 'secret'")

    def test_every_statement_the_schema_places_validates(self, json_config: str) -> None:
        """Clean, but for the statements `UNPLACED_IN_THE_EXAMPLE` records as a defect."""
        result = validate_ir(to_dict(json.dumps(placed_only(json.loads(json_config))), "json"))
        assert result.errors == []
        assert [(w.path, w.message) for w in result.warnings] == [self.RADIUS_SECRET]

    @pytest.mark.xfail(
        strict=True,
        reason="PRODUCT DEFECT: no known-differences class (set renderings keep them): the "
        "shipped 25.2R0 schema cannot place five statements both devices loaded, and the "
        "JSON reader keeps `ieee-802.3ad`; tests/support/devices.py UNPLACED_IN_THE_EXAMPLE",
    )
    def test_the_example_validates_clean(self, json_config: str) -> None:
        result = validate_ir(to_dict(json_config, "json"))
        assert result.errors == []
        assert [(w.path, w.message) for w in result.warnings] == [self.RADIUS_SECRET]


class TestATreeBuiltFromAnXsdIsEnforced:
    """The generator and the validator agree on the tree format: an enum, a
    pattern, an integer type and a mandatory flag declared in an XSD reach
    `validate_ir` through `junos-structure-tree.json`."""

    XSD = """\
<xsd:schema xmlns:xsd="http://www.w3.org/2001/XMLSchema"
            xmlns:junos="http://xml.juniper.net/junos/25.2R0/junos"
            elementFormDefault="qualified">
  <xsd:element name="configuration">
    <xsd:complexType>
      <xsd:sequence>
        <xsd:choice minOccurs="0" maxOccurs="unbounded">
          <xsd:element name="system" minOccurs="0">
            <xsd:complexType>
              <xsd:sequence>
                <xsd:choice minOccurs="0" maxOccurs="unbounded">
                  <xsd:element name="host-name" minOccurs="0">
                    <xsd:annotation><xsd:appinfo><flag>mandatory</flag></xsd:appinfo></xsd:annotation>
                    <xsd:simpleType>
                      <xsd:restriction base="xsd:string">
                        <xsd:pattern value="^[a-z][a-z0-9-]*$"/>
                      </xsd:restriction>
                    </xsd:simpleType>
                  </xsd:element>
                  <xsd:element name="option" minOccurs="0">
                    <xsd:simpleType>
                      <xsd:restriction base="xsd:string">
                        <xsd:enumeration value="enable"/>
                        <xsd:enumeration value="disable"/>
                      </xsd:restriction>
                    </xsd:simpleType>
                  </xsd:element>
                  <xsd:element name="mtu" minOccurs="0" type="xsd:unsignedShort"/>
                </xsd:choice>
              </xsd:sequence>
            </xsd:complexType>
          </xsd:element>
        </xsd:choice>
      </xsd:sequence>
    </xsd:complexType>
  </xsd:element>
</xsd:schema>
"""

    @pytest.mark.parametrize(
        ("system", "errors", "warnings"),
        [
            ({"host-name": "router-1", "option": "enable", "mtu": "1500"}, [], []),
            ({"host-name": "1-router"}, ["system.host-name"], []),
            ({"host-name": "r1", "option": "maybe"}, ["system.option"], []),
            ({"host-name": "r1", "mtu": "99999"}, ["system.mtu"], []),
            ({"option": "enable"}, [], ["system.host-name"]),
        ],
        ids=["clean", "pattern", "enum", "range", "mandatory"],
    )
    def test_each_constraint_is_enforced(
        self, tmp_path: Path, system: dict, errors: list[str], warnings: list[str]
    ) -> None:
        structure_tree(self.XSD, tmp_path)
        with artifacts_dir(tmp_path):
            result = validate_ir({"system": system})
        assert [e.path for e in result.errors] == errors
        assert [w.path for w in result.warnings] == warnings


# ── The pipeline ─────────────────────────────────────────────────────


class TestThePipelineAppliesFieldValidation:
    """`validate` reports, `strict` refuses, and anonymization refuses what the
    schema cannot place whatever either says."""

    _BAD = '{"configuration": {"system": {"host-name": "bad-host"}}}'
    _TREE = _make_schema(
        enums=[["valid-host"]],
        tree=_container(configuration=_container(system=_container(**{"host-name": _leaf(e=0)}))),
    )

    def test_pipeline_with_validate_false_skips_validation(
        self, use_tree: Callable[[dict[str, Any]], AbstractContextManager[None]]
    ) -> None:
        with use_tree(self._TREE):
            result = pipeline_result(
                self._BAD, from_format="json", to_format="json", validate=False
            )
        assert "bad-host" in result.output
        assert result.diagnostics == ()

    def test_pipeline_with_validate_true_warns(
        self,
        use_tree: Callable[[dict[str, Any]], AbstractContextManager[None]],
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """The finding is a returned diagnostic, the output still converts, and
        nothing is printed: rendering is the caller's."""
        with use_tree(self._TREE):
            result = pipeline_result(self._BAD, from_format="json", to_format="json", validate=True)
        assert "bad-host" in result.output
        assert [(d.source, d.path) for d in result.diagnostics] == [
            ("field-validate", "system.host-name")
        ]
        assert capsys.readouterr().err == ""

    def test_pipeline_strict_raises_on_bad_value(
        self, use_tree: Callable[[dict[str, Any]], AbstractContextManager[None]]
    ) -> None:
        with use_tree(self._TREE), pytest.raises(FieldValidationError, match="bad-host"):
            pipeline(self._BAD, from_format="json", to_format="json", strict=True)

    def test_an_unmodelled_statement_warns_and_fails_strict(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """What was silently discarded is kept, diagnosed, and fatal under strict."""
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
        cfg = AnonymizeConfig(ips=True, salt="s")
        source = "set protocols bgp neighbor 203.0.114.9 description peer"
        with pytest.raises(FieldValidationError, match="cannot anonymize"):
            pipeline(source, from_format="set", to_format="set", anon_config=cfg, validate=False)
        modelled = "set protocols bgp group G neighbor 203.0.114.9 description peer"
        out = pipeline(modelled, from_format="set", to_format="set", anon_config=cfg)
        assert "203.0.114.9" not in out


# ── Keyed entries against the shipped tree ───────────────────────────


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
    """Each key field is checked as a leaf; a `name` where the list keys
    otherwise is unplaced. Spec: validation/keyed-entries, "Field validation
    checks each key field as a leaf" (change identifier-key-fields)."""

    @staticmethod
    def _errors(ir: dict) -> list:
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
    """Kept whole by the reader, reported by validation, refused under strict.
    Spec: conversion/entry-keys."""

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
        result = validate_ir({"configuration": set_ir(line)})
        assert not result.valid
        assert any(e.expected == UNPLACED for e in result.errors), result.errors
        with pytest.raises(FieldValidationError):
            convert_config(line, from_format=Format.SET, to_format=Format.JSON, strict=True)


class TestALeafWithoutItsValueIsUnplaced:
    """A leaf written without its value is a statement the device rejects
    (corpus CORRECTLY_REJECTED, `set system host-name`). Every door wrote it
    back as a bare line with no diagnostic, and the set reader let it replace
    a value read before it (NEW-C1). The set and structured readers keep it in
    the level's record; JSON, YAML and XML hold it where it stands, and field
    validation reports it either way. Spec: conversion/entry-keys, change
    kept-whole-statements."""

    _SOURCES = {
        "set": "set system host-name\n",
        "structured": "system {\n    host-name;\n}\n",
        "json": '{"configuration": {"system": {"host-name": null}}}',
        "yaml": "configuration:\n  system:\n    host-name:\n",
        "xml": "<configuration><system><host-name/></system></configuration>",
    }

    @pytest.mark.parametrize("fmt", list(_SOURCES))
    def test_each_door_reports_it(self, fmt: str) -> None:
        result = convert_config_result(
            self._SOURCES[fmt], from_format=Format(fmt), to_format=Format.SET
        )
        assert result.output == "set system host-name\n"
        messages = [d.message for d in result.diagnostics if d.source == "field-validate"]
        assert len(messages) == 1, messages
        assert messages[0].startswith("'host-name'")
        assert messages[0].endswith(
            "could not be placed in the schema: kept as written, not validated"
        )

    @pytest.mark.parametrize("fmt", list(_SOURCES))
    def test_strict_and_anonymization_refuse_it(self, fmt: str) -> None:
        source = self._SOURCES[fmt]
        with pytest.raises(FieldValidationError):
            convert_config(source, from_format=Format(fmt), to_format=Format.SET, strict=True)
        with pytest.raises(FieldValidationError, match="cannot anonymize"):
            pipeline(
                source,
                from_format=fmt,
                to_format="set",
                anon_config=AnonymizeConfig(ips=True, salt="s"),
                validate=False,
            )

    @pytest.mark.parametrize(
        ("fmt", "source"),
        [
            ("set", "set system host-name router1\n"),
            ("json", '{"configuration": {"system": {"host-name": "router1"}}}'),
            (
                "json",
                '{"configuration": {"interfaces": {"interface": [{"name": "ge-0/0/0", '
                '"description": ""}]}}}',
            ),
            ("set", 'set interfaces ge-0/0/0 description ""\n'),
            (
                "json",
                '{"configuration": {"policy-options": {"community": [{"name": "SAMPLE-COMM", '
                '"members": ["64496:1"]}]}}}',
            ),
            ("json", '{"configuration": {"system": {"services": {"ssh": [null]}}}}'),
        ],
        ids=["set-value", "json-value", "json-empty-value", "set-empty-value", "leaf-list", "flag"],
    )
    def test_a_leaf_with_a_value_is_clean(self, fmt: str, source: str) -> None:
        """The negative side: a value, an empty value, a leaf-list and a
        presence flag report nothing."""
        result = convert_config_result(source, from_format=Format(fmt), to_format=Format.SET)
        assert [d for d in result.diagnostics if "could not be placed" in d.message] == []


class TestANameKeyIsOpen:
    """Closed-enum enforcement applies to the key fields the tree names in `k`
    only. A `name` key's enum is a fragment, open as it was before `name`
    became a tree child; holding it closed reported 11,310 valid jvd lines.
    Owner decision on challenge C, phase-6 review of identifier-key-fields;
    the closed side is `TestKeyedEntries::test_a_key_value_is_checked_against_its_leaf`."""

    def test_a_classifier_name_is_clean(self) -> None:
        line = "set class-of-service interfaces ge-0/0/0 unit 0 classifiers dscp SAMPLE-DSCP"
        assert validate_ir({"configuration": set_ir(line)}).errors == []


class TestAnEntryWithoutItsKeyIsUnplaced:
    """An entry from JSON, YAML or XML that lacks a key field was written as a
    line the device rejects, with no diagnostic. It is the statement the set
    reader cannot complete, reported the same way (finding 5, phase-6 review
    of identifier-key-fields)."""

    _CASES = [
        (_policy("from", {"as-path-neighbors": [{"list-name": "SAMPLE-AS-LIST"}]}), "list-type"),
        (_policy("from", {"route-filter": [{"exact": [None], "accept": [None]}]}), "address"),
        (_policy("from", {"route-filter": [{"address": "198.51.100.0/24"}]}), "exact"),
        (_event({k: v for k, v in _MATCH.items() if k != "condition"}), "condition"),
        ({"policy-options": {"policy-statement": [{"then": {"accept": [None]}}]}}, "name"),
    ]

    @pytest.mark.parametrize(("ir", "field"), _CASES)
    def test_validation_reports_it(self, ir: dict, field: str) -> None:
        errors = validate_ir({"configuration": ir}).errors
        unplaced = [e for e in errors if e.expected == UNPLACED]
        assert len(unplaced) == 1, errors
        assert f"without its key field '{field}" in unplaced[0].message
        assert unplaced[0].message.endswith(
            "could not be placed in the schema: kept as written, not validated"
        )

    @pytest.mark.parametrize("fmt", ["json", "yaml", "xml"])
    def test_each_structured_door_reports_it(self, fmt: str) -> None:
        ir = _policy("from", {"as-path-neighbors": [{"list-name": "SAMPLE-AS-LIST"}]})
        if fmt == "json":
            source = json.dumps({"configuration": ir})
        elif fmt == "yaml":
            source = yaml.safe_dump({"configuration": ir})
        else:
            source = (
                "<configuration><policy-options><policy-statement><name>SAMPLE-POLICY</name>"
                "<term><name>T1</name><from><as-path-neighbors>"
                "<list-name>SAMPLE-AS-LIST</list-name>"
                "</as-path-neighbors></from></term></policy-statement></policy-options>"
                "</configuration>"
            )
        result = convert_config_result(source, from_format=Format(fmt), to_format=Format.SET)
        messages = [d.message for d in result.diagnostics if d.source == "field-validate"]
        assert messages == [
            "'as-path-neighbors' entry without its key field 'list-type' could not be placed "
            "in the schema: kept as written, not validated"
        ]
        with pytest.raises(FieldValidationError):
            convert_config_result(
                source, from_format=Format(fmt), to_format=Format.SET, strict=True
            )

    def test_a_complete_entry_is_clean(self) -> None:
        entry = {"list-type": "as-list", "list-name": "SAMPLE-AS-LIST"}
        ir = _policy("from", {"as-path-neighbors": [entry]})
        assert validate_ir({"configuration": ir}).errors == []
