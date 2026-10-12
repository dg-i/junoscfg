"""Every rule covers its held device values, individually.

T3 supplements the combined device address/reference law and the independent
handwritten all-rule/pair contract. Invented oracle configurations were loaded
and printed by vMX 23.2R2 and QFX5120 25.2R2; XML is deliberately deferred.
The expected inventory comes from device display set, not product rule matches.
"""

from __future__ import annotations

import ipaddress
import json
import re
import shlex
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pathlib import Path

import pytest

from junoscfg import Format, convert_config
from junoscfg.anonymize import AnonymizeConfig
from tests.support.devices import FORMATS, Capture, captures


@dataclass(frozen=True)
class RuleCase:
    id: str
    mapping: str
    options: dict[str, Any]


RULES = (
    RuleCase("ip", "ip", {"ips": True}),
    RuleCase("password", "password", {"passwords": True}),
    RuleCase("ssh-key", "ssh_key", {"ssh_keys": True}),
    RuleCase("community", "community", {"communities": True}),
    RuleCase("identity", "identity", {"identities": True}),
    RuleCase("group", "group", {"groups": True}),
    RuleCase("description", "description", {"descriptions": True}),
    RuleCase("as-number", "as_number", {"as_numbers": [64496, 64497, 64498, 64499, 64511]}),
    RuleCase("sensitive-word", "sensitive_word", {"sensitive_words": ["customer"]}),
    RuleCase("sensitive-pattern", "sensitive_word", {"sensitive_patterns": [r"GR-[A-Z-]+"]}),
)
CAPTURES = tuple(c for c in captures() if c.source == "synthetic" and c.name == "junoscfg-oracle")
CASES = [
    pytest.param(capture, suffix, row, id=f"{capture.device}.{suffix}.{row.id}")
    for capture in CAPTURES
    for suffix in ("json", "set", "conf")
    for row in RULES
]


def _inventory(capture: Capture, row: RuleCase) -> set[str]:
    """Device-token semantics for the ten rule scopes present in this capture."""
    values: set[str] = set()
    for line in capture.device_set():
        words = shlex.split(line)
        for index, word in enumerate(words[:-1]):
            value = words[index + 1]
            if row.id == "ip" and word != "oid":
                try:
                    ipaddress.ip_interface(value)
                except ValueError:
                    pass
                else:
                    values.add(value)
            if not value or value == "<*>":
                continue
            eligible = {
                "password": value.startswith(("$6$", "$9$"))
                or word in {"encrypted-password", "authentication-key"},
                "ssh-key": word in {"ssh-rsa", "ssh-ed25519"},
                "community": word == "community" and "snmp" in words[:index],
                "identity": word == "user" and "login" in words[:index],
                "group": word in {"groups", "apply-groups", "apply-groups-except"}
                or (word == "group" and "bgp" in words[:index]),
                # system location is a container; SNMP location is a leaf.
                "description": word in {"description", "contact"}
                or (word == "location" and "snmp" in words[:index]),
                "as-number": word in {"peer-as", "autonomous-system"},
            }
            if eligible.get(row.id, False):
                values.add(value)
        if row.id.startswith("sensitive"):
            pattern = r"customer" if row.id == "sensitive-word" else r"GR-[A-Z-]+"
            for value in words[1:]:
                if re.search(pattern, value, flags=re.IGNORECASE):
                    values.add(value)
    return values


def _ip_is_preserved(value: str) -> bool:
    """Documented reserved ranges and whole private-block aggregates pass."""
    address = ipaddress.ip_address(value.partition("/")[0])
    network = ipaddress.ip_network(value, strict=False)
    if address.is_unspecified or address.is_loopback or address.is_multicast or address.is_reserved:
        return True
    if network.prefixlen == 0:
        return True
    if address.version == 4 and any(
        address in ipaddress.ip_network(block)
        for block in ("0.0.0.0/8", "192.0.2.0/24", "198.51.100.0/24", "203.0.113.0/24")
    ):
        return True
    return value in {"10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16"}


def _strings(value: Any) -> list[str]:
    if isinstance(value, dict):
        return [str(k) for k in value] + [s for child in value.values() for s in _strings(child)]
    if isinstance(value, list):
        return [s for child in value for s in _strings(child)]
    return [value] if isinstance(value, str) else []


def _mapped(value: Any, table: dict[str, str]) -> Any:
    if isinstance(value, dict):
        return {_mapped(k, table): _mapped(v, table) for k, v in value.items()}
    if isinstance(value, list):
        return [_mapped(v, table) for v in value]
    if isinstance(value, str):
        if value in table:
            return table[value]
        pattern = "|".join(re.escape(original) for original in sorted(table, key=len, reverse=True))
        return re.sub(pattern, lambda match: table[match.group()], value)
    return value


def _leaves(value: Any, path: tuple[Any, ...] = ()) -> dict[tuple[Any, ...], Any]:
    if isinstance(value, dict):
        return {
            p: v for key, child in value.items() for p, v in _leaves(child, (*path, key)).items()
        }
    if isinstance(value, list):
        return {
            p: v
            for index, child in enumerate(value)
            for p, v in _leaves(child, (*path, index)).items()
        }
    return {path: value}


@pytest.mark.parametrize(("capture", "suffix", "row"), CASES)
def test_each_device_rule_replaces_its_inventory_and_reverses(
    capture: Capture, suffix: str, row: RuleCase, tmp_path: Path
) -> None:
    expected = _inventory(capture, row)
    if row.id == "ip" and suffix == "json":
        # Native JSON includes an annotation with an embedded IPv6 prefix.
        # Inventory that held text as well as the device's statement values.
        expected = set()
        for value in _strings(json.loads(capture.rendering("json"))):
            if not isinstance(value, str):
                continue
            for candidate in (value, *value.split()):
                candidate = candidate.strip("(),;\"'")
                try:
                    ipaddress.ip_interface(candidate)
                except ValueError:
                    pass
                else:
                    expected.add(candidate)
    if suffix == "conf" and row.id in {"group", "sensitive-pattern"}:
        # The device emits /* OMITTED */ instead of the GR-OMIT group.
        assert "/* OMITTED */" in capture.rendering("conf")
        expected.remove("GR-OMIT")
    assert expected, "a rule without eligible held values must not claim coverage"
    source = capture.rendering(suffix)
    arguments = {"from_format": FORMATS[suffix], "to_format": Format.JSON, "validate": False}
    baseline = json.loads(convert_config(source, **arguments))
    dumped = tmp_path / "mapping.json"
    anonymized = convert_config(
        source,
        **arguments,
        anon_config=AnonymizeConfig(salt="device-rule-salt", dump_map=str(dumped), **row.options),
    )
    mapping = json.loads(dumped.read_text(encoding="utf-8"))
    assert set(mapping) == {row.mapping}
    assert set(mapping[row.mapping]) == expected
    for original, replacement in mapping[row.mapping].items():
        if row.id == "ip" and _ip_is_preserved(original):
            assert replacement == original
        else:
            assert replacement != original
    before, after = _leaves(baseline), _leaves(json.loads(anonymized))
    if row.id == "ip":
        # Native readers may hold address names as dictionary keys: rename keys
        # as well as leaves, without dropping or reordering any entries.
        assert json.loads(anonymized) == _mapped(baseline, mapping[row.mapping])
    else:
        assert before.keys() == after.keys(), "anonymization changed capture shape"
    for path, original in before.items():
        if row.id != "ip" and isinstance(original, str) and original in mapping[row.mapping]:
            assert after[path] == mapping[row.mapping][original], "a mapped occurrence survived"
    assert json.loads(anonymized) != baseline
    reverted = convert_config(
        anonymized,
        from_format=Format.JSON,
        to_format=Format.JSON,
        validate=False,
        anon_config=AnonymizeConfig(revert_map=str(dumped)),
    )
    assert json.loads(reverted) == baseline
