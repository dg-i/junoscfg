"""Device captures: what a Junos device printed for a configuration, in four formats.

The device is the oracle, above the schema model and everything junoscfg
generates (ARCHITECTURE.md, evidence hierarchy). A capture is one
configuration loaded on a device and saved by it as curly, XML, JSON and
display set (`tests/data/device/README.md`); its display set is what junoscfg's
set rendering of any of the four must equal, less the differences
`known-differences.json` records with their class.
"""

from __future__ import annotations

import copy
import json
from dataclasses import dataclass
from functools import cache
from typing import Any

from junoscfg import Format, convert_config
from junoscfg.display import read_artifact_text
from tests.support.paths import TEST_DATA

DEVICE_DATA = TEST_DATA / "device"
KNOWN_DIFFERENCES = DEVICE_DATA / "known-differences.json"
#: Rendering suffix -> the format junoscfg reads it as.
FORMATS = {"conf": Format.STRUCTURED, "json": Format.JSON, "set": Format.SET, "xml": Format.XML}
_STATEMENT = ("set ", "deactivate ", "protect ", "activate ")
#: The capture whose four renderings `examples/` holds, byte for byte.
EXAMPLE = "synthetic/vmx-23.2R2-S7.5/junoscfg-oracle"


@dataclass(frozen=True)
class Capture:
    """One configuration as one device printed it."""

    name: str
    source: str
    device: str
    captured: str
    note: str = ""
    refused: tuple[str, ...] = ()

    @property
    def key(self) -> str:
        return f"{self.source}/{self.device}/{self.name}"

    def rendering(self, suffix: str) -> str:
        """The device's rendering in *suffix* (``conf``, ``json``, ``set``, ``xml``)."""
        return read_artifact_text(
            DEVICE_DATA / self.source / self.device / f"{self.name}.{suffix}.gz"
        )

    def device_set(self) -> list[str]:
        """The device's display set: its statements, without blank lines."""
        return _statements(self.rendering("set"))

    def junoscfg_set(self, suffix: str) -> list[str]:
        """junoscfg's set rendering of the device's *suffix* rendering."""
        source = self.rendering(suffix)
        rendered = convert_config(
            source, from_format=FORMATS[suffix], to_format=Format.SET, validate=False
        )
        return _statements(rendered)

    def difference(self, suffix: str) -> dict[str, list[str]]:
        """Lines of the device's set junoscfg lacks (missing), and the reverse (extra)."""
        device, ours = set(self.device_set()), set(self.junoscfg_set(suffix))
        return {"missing": sorted(device - ours), "extra": sorted(ours - device)}


def _statements(text: str) -> list[str]:
    return [line for line in text.splitlines() if line.startswith(_STATEMENT)]


@cache
def captures() -> tuple[Capture, ...]:
    """Every committed capture, as the manifest lists them."""
    manifest = json.loads((DEVICE_DATA / "manifest.json").read_text(encoding="utf-8"))
    return tuple(
        Capture(**{**entry, "refused": tuple(entry.get("refused", ()))})
        for entry in manifest["captures"]
    )


@cache
def known_differences() -> dict:
    """The recorded differences and their classes."""
    return json.loads(KNOWN_DIFFERENCES.read_text(encoding="utf-8"))


def recorded(capture: Capture, suffix: str) -> dict[str, list[str]]:
    """The recorded difference for one rendering, in the shape `Capture.difference` gives."""
    entry = known_differences()["differences"].get(f"{capture.key}.{suffix}", {})
    return {side: sorted(entry.get(side, {})) for side in ("missing", "extra")}


def recorded_lines(capture: Capture, suffix: str) -> set[str]:
    """Every line the record names for one rendering, on either side."""
    entry = recorded(capture, suffix)
    return set(entry["missing"]) | set(entry["extra"])


def example() -> Capture:
    """The capture `examples/` holds: the vMX's renderings of junoscfg-oracle."""
    return next(capture for capture in captures() if capture.key == EXAMPLE)


#: Statements of the example the vMX (23.2R2) and the QFX5120 (25.2R2) both
#: loaded that junoscfg cannot place in the shipped schema, by their path in
#: the IR, with the reason. PRODUCT DEFECT, and none of them a class of
#: `known-differences.json`: the set rendering keeps them as written, so the
#: device law sees nothing, but field validation reports each and the JSON
#: schemas reject them; an anonymized run names each by its schema path.
#: Found when the example became the device's (openspec/changes/device-oracle).
UNPLACED_IN_THE_EXAMPLE: tuple[tuple[tuple[str, ...], str], ...] = (
    (("system", "login", "user", "shell"), "the 25.2R0 schema model has no `shell`"),
    (
        ("system", "services", "extension-service", "request-response", "grpc", "clear-text"),
        "the 25.2R0 schema model has no grpc `clear-text`",
    ),
    (
        (
            "system",
            "services",
            "extension-service",
            "request-response",
            "grpc",
            "skip-authentication",
        ),
        "the 25.2R0 schema model has no grpc `skip-authentication`",
    ),
    (
        ("system", "ddos-protection", "protocols", "autoconf"),
        "the 25.2R0 schema model has no ddos-protection `autoconf`",
    ),
    (
        ("protocols", "bgp", "group", "family", "inet6", "labeled-unicast", "per-prefix-label"),
        "the 25.2R0 schema model has no inet6 labeled-unicast `per-prefix-label`",
    ),
    (
        ("interfaces", "interface-range", "member-range"),
        "the JSON reader keeps the element name `end-range`, so `member-range` lacks its "
        "mandatory `to`; the set reader and the schema say `to` (ARCH-C09, change 13). Unseen "
        "until change anonymize-every-placed-value walked the children of `interfaces` "
        "beside `interface`",
    ),
    (
        ("interfaces", "interface", "ether-options", "ieee-802.3ad"),
        "the JSON reader keeps the element name `ieee-802.3ad`; the XML reader and the "
        "schema say `802.3ad`",
    ),
)


def placed_only(ir: dict[str, Any]) -> dict[str, Any]:
    """*ir* without the statements of `UNPLACED_IN_THE_EXAMPLE`, as a copy.

    A path descends through every entry of a list it meets; the statement's
    own tags (``@<name>``) go with it.
    """
    trimmed = copy.deepcopy(ir)
    root = trimmed.get("configuration", trimmed)
    for path, _ in UNPLACED_IN_THE_EXAMPLE:
        _drop(root, path)
    return trimmed


def _drop(node: Any, path: tuple[str, ...]) -> None:
    if isinstance(node, list):
        for item in node:
            _drop(item, path)
    elif isinstance(node, dict):
        head, rest = path[0], path[1:]
        if rest:
            if head in node:
                _drop(node[head], rest)
        else:
            node.pop(head, None)
            node.pop(f"@{head}", None)
