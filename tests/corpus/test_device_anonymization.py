"""Every device capture, anonymized with every rule on, keeps the anonymizer's promise.

A capture is a configuration a Junos device loaded and printed in four
formats (`tests/data/device/README.md`). Read from each rendering and
anonymized with every rule, it must lose every address the device wrote
(but one the address anonymizer keeps by design, such as `0.0.0.0/0`), keep
every group reference pointing at its renamed group, and come back to the IR
it was read as when the mapping is reverted.

Until change anonymize-every-placed-value the walker missed universal
statements below the root, a transparent container's other children and a
list held by a container that is no list; the IP rule ignored `hostname`
and other types; a second pass renamed `apply-groups` again; and content the
schema cannot place passed `anonymize()` unseen or was refused by the
conversion (ARCH-C05, NEW-R5, ANON-P1, ANON-P2, NEW-A-N1/N2/N3/N6). Spec
anonymization/placed-values.
"""

from __future__ import annotations

import ipaddress
import json
import re
import shlex
import tempfile
from dataclasses import dataclass
from functools import cache
from pathlib import Path
from typing import Any

import pytest

from junoscfg import Format, convert_config
from junoscfg.anonymize import AnonymizeConfig
from tests.support.devices import FORMATS, captures

CASES = [
    pytest.param(capture.key, suffix, id=f"{capture.key}.{suffix}")
    for capture in captures()
    for suffix in FORMATS
]
_GROUP_REFERENCES = frozenset({"apply-groups", "apply-groups-except"})


def _every_rule(**options: Any) -> AnonymizeConfig:
    return AnonymizeConfig(
        ips=True,
        passwords=True,
        communities=True,
        ssh_keys=True,
        identities=True,
        groups=True,
        descriptions=True,
        as_numbers=[64496, 64497, 64498, 64499, 64511],
        sensitive_words=["customer"],
        salt="corpus-salt",
        **options,
    )


@dataclass(frozen=True)
class Run:
    """One rendering, read plainly and anonymized with every rule on."""

    source: dict[str, Any]
    anonymized: dict[str, Any]
    written: str
    mapping: dict[str, dict[str, str]]
    reverted: dict[str, Any]


@cache
def _run(key: str, suffix: str) -> Run:
    capture = next(capture for capture in captures() if capture.key == key)
    text, fmt = capture.rendering(suffix), FORMATS[suffix]
    plain = convert_config(text, from_format=fmt, to_format=Format.JSON, validate=False)
    with tempfile.TemporaryDirectory() as scratch:
        dumped = Path(scratch) / "map.json"
        anonymized = convert_config(
            text,
            from_format=fmt,
            to_format=Format.JSON,
            validate=False,
            anon_config=_every_rule(dump_map=str(dumped)),
        )
        mapping = json.loads(dumped.read_text(encoding="utf-8"))
        reverted = convert_config(
            anonymized,
            from_format=Format.JSON,
            to_format=Format.JSON,
            validate=False,
            anon_config=AnonymizeConfig(revert_map=str(dumped)),
        )
    written = convert_config(
        text, from_format=fmt, to_format=Format.SET, validate=False, anon_config=_every_rule()
    )
    return Run(json.loads(plain), json.loads(anonymized), written, mapping, json.loads(reverted))


def _is_address(word: str) -> bool:
    address, _, length = word.partition("/")
    try:
        ipaddress.ip_address(address)
    except ValueError:
        return False
    return not length or length.isdigit()


#: Blocks the address anonymizer keeps by design, decided here and not by the
#: run (Test/Challenge finding 1): documentation and private blocks keep what
#: their own prefix length covers, so `10.0.0.0/8` stays and `10.1.0.0/16` does not.
_KEPT_BLOCKS = tuple(
    ipaddress.ip_network(block)
    for block in (
        "0.0.0.0/8",
        "192.0.2.0/24",
        "198.51.100.0/24",
        "203.0.113.0/24",
        "10.0.0.0/8",
        "172.16.0.0/12",
        "192.168.0.0/16",
    )
)
_FULLY_KEPT = _KEPT_BLOCKS[:4]


def _kept_by_design(word: str) -> bool:
    """Whether the address anonymizer keeps *word* whatever the salt."""
    address = ipaddress.ip_address(word.partition("/")[0])
    network = ipaddress.ip_network(word, strict=False)
    if (
        address.is_unspecified
        or address.is_loopback
        or address.is_multicast
        or address.is_reserved
        or network.prefixlen == 0
        or (isinstance(address, ipaddress.IPv6Address) and address.ipv4_mapped is not None)
    ):
        return True
    if any(address in block for block in _FULLY_KEPT if block.version == address.version):
        return True
    # An aggregate: the anonymizer keeps the first octet of IPv4 and passes an
    # IPv6 prefix shorter than /32 as written.
    if "/" in word and (
        (network.version == 4 and network.prefixlen <= 8 and network.network_address == address)
        or (network.version == 6 and network.prefixlen < 32)
    ):
        return True
    return any(
        block.version == network.version
        and network.prefixlen <= block.prefixlen
        and block.subnet_of(network)  # type: ignore[arg-type]
        for block in _KEPT_BLOCKS
    )


#: Keywords whose value is syntax shaped like an address: an area identifier
#: (`areaid`) and an SNMP OID (ruling on Test/Challenge finding 6). A BGP
#: `cluster` holds an address (specification challenge S4).
_SYNTAX_BEFORE = frozenset({"area", "oid"})
#: A run of characters an address is spelled with; an address inside a word
#: (`http://203.0.114.9:8080/x`, `lo_203.0.114.9`) is one too (S5).
_RUN = re.compile(r"[0-9A-Fa-f:.]+")


def _addresses_in(lines: list[str]) -> set[str]:
    """Every address in *lines*, whole words and inside words, but an area or an OID.

    A whole word keeps its prefix length; inside a word the scan is plain
    `ipaddress` over each run of address characters, independent of the
    product's tokenizer (specification challenge S5).
    """
    found: set[str] = set()
    for line in lines:
        words = _split(line)
        for before, word in zip(["", *words], words, strict=False):
            if before in _SYNTAX_BEFORE:
                continue
            if _is_address(word):
                found.add(word)
                continue
            for run in _RUN.findall(word):
                for candidate in (run.strip(".:"), *run.split(":")):
                    if _is_address(candidate.strip(".")):
                        found.add(candidate.strip("."))
    return found


def _split(line: str) -> list[str]:
    try:
        return shlex.split(line)
    except ValueError:
        return [word.strip('"') for word in line.split()]


def _references(node: Any) -> list[str]:
    """Every group an `apply-groups` or `apply-groups-except` names, in tree order."""
    found: list[str] = []
    if isinstance(node, dict):
        for key, value in node.items():
            if key in _GROUP_REFERENCES:
                found.extend(str(v) for v in (value if isinstance(value, list) else [value]))
            else:
                found.extend(_references(value))
    elif isinstance(node, list):
        for item in node:
            found.extend(_references(item))
    return found


def _groups(ir: dict[str, Any]) -> set[str]:
    groups = ir["configuration"].get("groups", [])
    if isinstance(groups, dict):
        groups = groups.get("group", [])
    return {str(group.get("name")) for group in groups if isinstance(group, dict)}


class TestEveryCaptureAnonymizes:
    @pytest.mark.parametrize(("key", "suffix"), CASES)
    def test_no_address_of_the_capture_survives(self, key: str, suffix: str) -> None:
        capture = next(capture for capture in captures() if capture.key == key)
        addresses = {a for a in _addresses_in(capture.device_set()) if not _kept_by_design(a)}
        assert addresses, "the capture holds no address to replace: the law would pass on nothing"
        run = _run(key, suffix)
        assert sorted(addresses & _addresses_in(run.written.splitlines())) == []
        assert addresses <= set(run.mapping.get("ip", {})), "an address was never replaced"

    @pytest.mark.parametrize(("key", "suffix"), CASES)
    def test_the_mapping_restores_the_canonical_ir(self, key: str, suffix: str) -> None:
        run = _run(key, suffix)
        assert run.mapping, "nothing was anonymized"
        assert run.anonymized != run.source
        assert run.reverted == run.source

    @pytest.mark.parametrize(("key", "suffix"), CASES)
    def test_every_group_reference_resolves(self, key: str, suffix: str) -> None:
        """Every reference names a group the output defines, or is unchanged: a
        name Junos reserves (`re0`, `node0`, `${node}`) passes the group rule
        (ruling on Test/Challenge finding 7)."""
        run = _run(key, suffix)
        before, after = _references(run.source), _references(run.anonymized)
        assert len(before) == len(after)
        defined = _groups(run.anonymized)
        dangling = [
            (old, new)
            for old, new in zip(before, after, strict=True)
            if new not in defined and new != old
        ]
        assert dangling == []
