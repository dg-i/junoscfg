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


def _words(text: str) -> set[str]:
    words: set[str] = set()
    for line in text.splitlines():
        try:
            words.update(shlex.split(line))
        except ValueError:
            words.update(word.strip('"') for word in line.split())
    return words


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
        addresses = {word for word in _words("\n".join(capture.device_set())) if _is_address(word)}
        assert addresses, "the capture holds no address: the law would pass on nothing"
        run = _run(key, suffix)
        kept_by_design = {a for a, b in run.mapping.get("ip", {}).items() if a == b}
        assert sorted((addresses & _words(run.written)) - kept_by_design) == []

    @pytest.mark.parametrize(("key", "suffix"), CASES)
    def test_the_mapping_restores_the_canonical_ir(self, key: str, suffix: str) -> None:
        run = _run(key, suffix)
        assert run.mapping, "nothing was anonymized"
        assert run.anonymized != run.source
        assert run.reverted == run.source

    @pytest.mark.parametrize(("key", "suffix"), CASES)
    def test_every_group_reference_resolves(self, key: str, suffix: str) -> None:
        run = _run(key, suffix)
        before, after = _references(run.source), _references(run.anonymized)
        assert len(before) == len(after)
        defined_before, defined_after = _groups(run.source), _groups(run.anonymized)
        dangling = [
            (old, new)
            for old, new in zip(before, after, strict=True)
            if old in defined_before and new not in defined_after
        ]
        assert dangling == []
