"""Copy device captures from private_test_data/ into tests/data/device/.

A capture is one configuration loaded on a real device (``configure private``,
``load override``, never committed) and saved by the device in its four
renderings: curly (``.conf``), XML, JSON and display set. The device is the
oracle: what it printed is what Junos means, whatever junoscfg makes of it.

Only the renderings and the sources are copied. The capture logs name the lab
devices and are never committed. Files are gzipped with mtime 0, so a re-import
of the same captures is byte-identical. The manifest records each device, each
capture and, for Juniper's JVD configurations, the repository, commit and path
they came from; their licence and notice sit beside them in jvd/.

Run after a recapture: ``uv run python tools/import_device_captures.py [SKIP...]``,
where SKIP is a capture name, or ``<device>/<name>`` for one device's capture,
to leave out a capture that is not final.
"""

from __future__ import annotations

import gzip
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PRIVATE = ROOT / "private_test_data"
TARGET = ROOT / "tests" / "data" / "device"
FORMATS = ("conf", "json", "set", "xml")

#: Device directory -> where its captures are, and what `show version` or, failing
#: that, the XML namespace says it runs.
DEVICES = {
    "vmx-23.2R2-S7.5": {
        "folder": "jvd_derived_data",
        "model": "vmx",
        "release": "23.2R2-S7.5",
        "release_source": "show version",
    },
    "qfx5120-25.2R2-S1.5": {
        "folder": "jvd_derived_data_qfx",
        "model": "qfx5120-32c",
        "release": "25.2R2-S1.5",
        "release_source": "xml-namespace",
    },
}

#: What is imported, from which folder (None: the device's), and why: few
#: captures, each for something no other shows.
#: The ex4600, ex4100 and qfx renderings of the same configurations gave no
#: junoscfg difference the vmx's did not (they drop what their platform lacks),
#: an4_acx710 shows only classes mdr1_acx7509 shows, and ap1_mx304 matches in
#: every format; they stay in private_test_data/, and the grammar corpus still
#: draws on every device line there.
SELECTION = {
    "vmx-23.2R2-S7.5": {
        "junoscfg-oracle": (
            "oracle_vmx",
            "every construct the converters must carry, routing and system material for the "
            "anonymizer; the routing superset, and examples/",
        ),
        "bng1_mx304": (None, "the only capture of radius-timeout-dropped; `$junos-` variables"),
        "mdr1_acx7509": (None, "transport-class and isis overload; the bare-deactivate quirk"),
        "services-leaf1_qfx5130-48c": (
            None,
            "policy-expression quoting; most XML/JSON element leaks",
        ),
        "synthetic-probes": (None, "junoscfg's renderings, loaded to ask the device their meaning"),
    },
    "qfx5120-25.2R2-S1.5": {
        "junoscfg-oracle": (
            "oracle_qfx",
            "the switching (ELS) section, on the release the shipped artifacts come from",
        ),
    },
}

JVD_REPOSITORY = "https://github.com/Juniper/jvd"
JVD_COMMIT = "ef889c28e687155388823ac09be5452701f97ef9"
JVD_PATHS = {
    "bng1_mx304": "service_provider/broadband_edge/configuration/conf/bng1_mx304.conf",
    "mdr1_acx7509": (
        "service_provider/metro_ethernet_business_services/configuration/conf/mdr1_acx7509.conf"
    ),
    "services-leaf1_qfx5130-48c": (
        "data_center/adc/5stage_evpn_vxlan/configuration/conf/services-leaf1_qfx5130-48c.conf"
    ),
}
SYNTHETIC = ("junoscfg-oracle", "synthetic-probes")
#: Captures a device folder holds that are not that device's: synthetic-ex in the vmx
#: folder was captured on the ex4600 and is identical to the ex4600 folder's copy.
NOT_THIS_DEVICE = {("vmx-23.2R2-S7.5", "synthetic-ex")}


def _write_gz(source: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    with (
        open(source, "rb") as raw,
        open(target, "wb") as out,
        gzip.GzipFile(fileobj=out, mode="wb", compresslevel=9, mtime=0, filename="") as gz,
    ):
        shutil.copyfileobj(raw, gz)


def _kind(name: str) -> str:
    return "jvd" if name in JVD_PATHS else "synthetic"


def main(skip: set[str]) -> int:
    """Import every capture not in *skip*; write the manifest."""
    # A re-import replaces what an earlier one wrote; licence files, the README
    # and the records beside the renderings stay.
    for kind in ("synthetic", "jvd"):
        for folder in (TARGET / kind).glob("*/"):
            shutil.rmtree(folder)
    captures = []
    for device, chosen in SELECTION.items():
        for name, (where, why) in chosen.items():
            folder = PRIVATE / (where or DEVICES[device]["folder"])
            if name in skip or f"{device}/{name}" in skip:
                continue
            present = [ext for ext in FORMATS if (folder / f"{name}.{ext}").is_file()]
            if present != list(FORMATS):
                print(
                    f"{device}/{name}: missing {sorted(set(FORMATS) - set(present))}",
                    file=sys.stderr,
                )
                return 1
            kind = _kind(name)
            for ext in FORMATS:
                _write_gz(folder / f"{name}.{ext}", TARGET / kind / device / f"{name}.{ext}.gz")
            captures.append(
                {
                    "name": name,
                    "source": kind,
                    "device": device,
                    "captured": "2026-10-10",
                    "note": why,
                }
            )
    imported = {c["name"] for c in captures}
    for name in SYNTHETIC:
        if name in imported:
            _write_gz(
                PRIVATE / f"{name}.conf", TARGET / "synthetic" / "sources" / f"{name}.conf.gz"
            )
    for name, path in JVD_PATHS.items():
        if name in imported:
            _write_gz(PRIVATE / "jvd" / path, TARGET / "jvd" / "sources" / f"{name}.conf.gz")
    manifest = {
        "devices": {d: {k: v for k, v in m.items() if k != "folder"} for d, m in DEVICES.items()},
        "jvd": {
            "repository": JVD_REPOSITORY,
            "commit": JVD_COMMIT,
            "paths": JVD_PATHS,
            "note": (
                "loaded unmodified; the captures were run from a clone whose commit was not "
                "recorded, and the load-error line numbers match this commit"
            ),
        },
        "secrets": (
            "invented for the synthetic configurations, Juniper's published lab values in the "
            "JVD ones; public, and not masked. Each device re-encrypts them"
        ),
        "captures": captures,
    }
    (TARGET / "manifest.json").write_text(json.dumps(manifest, indent=1) + "\n", encoding="utf-8")
    print(f"{len(captures)} captures from {len(DEVICES)} devices")
    return 0


if __name__ == "__main__":
    sys.exit(main(set(sys.argv[1:])))
