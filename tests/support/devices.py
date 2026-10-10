"""Device captures: what a Junos device printed for a configuration, in four formats.

The device is the oracle, above the schema model and everything junoscfg
generates (ARCHITECTURE.md, evidence hierarchy). A capture is one
configuration loaded on a device and saved by it as curly, XML, JSON and
display set (`tests/data/device/README.md`); its display set is what junoscfg's
set rendering of any of the four must equal, less the differences
`known-differences.json` records with their class.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import cache

from junoscfg import Format, convert_config
from junoscfg.display import read_artifact_text
from tests.support.paths import TEST_DATA

DEVICE_DATA = TEST_DATA / "device"
KNOWN_DIFFERENCES = DEVICE_DATA / "known-differences.json"
#: Rendering suffix -> the format junoscfg reads it as.
FORMATS = {"conf": Format.STRUCTURED, "json": Format.JSON, "set": Format.SET, "xml": Format.XML}
_STATEMENT = ("set ", "deactivate ", "protect ", "activate ")


@dataclass(frozen=True)
class Capture:
    """One configuration as one device printed it."""

    name: str
    source: str
    device: str
    captured: str
    note: str = ""

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
    return tuple(Capture(**entry) for entry in manifest["captures"])


@cache
def known_differences() -> dict:
    """The recorded differences and their classes."""
    return json.loads(KNOWN_DIFFERENCES.read_text(encoding="utf-8"))


def recorded(capture: Capture, suffix: str) -> dict[str, list[str]]:
    """The recorded difference for one rendering, in the shape `Capture.difference` gives."""
    entry = known_differences()["differences"].get(f"{capture.key}.{suffix}", {})
    return {side: sorted(entry.get(side, {})) for side in ("missing", "extra")}
