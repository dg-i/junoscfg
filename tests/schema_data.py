"""Discovery of developer-supplied device schema dumps.

A user needs none of this: the package ships generated artifacts and works
without a device. A developer *should* sync one or more NETCONF XSD dumps into
``private_test_data/schemas/``, which is gitignored, and the tests marked
``schema`` then run against each of them.

Drop a fresh dump in as ``new.xsd`` and it is promoted on first use to a name
carrying its Junos release, so several devices and releases can sit side by
side without manual bookkeeping.

The platform cannot be read out of the dump. A NETCONF XSD is release-wide: it
describes everything a Junos release supports across the whole product line, so
every dump names every platform — ACX, EX, MX, PTX, QFX, SRX and vMX all appear
in all of ours, as enum values for hardware-specific configuration rather than
as a statement of what the box is. Feature depth says the same: ``unified-edge``
is 1,771 nodes in both a vMX's 23.2R2 dump and the bundled 24.4R0, and
``virtual-chassis`` is 63 in every one. What varies is the release.

So the platform is recorded at capture time, from ``show version``, or not at
all. Pass it to :func:`promote_staged`, or write it into ``new.platform``
beside the staged dump.
"""

from __future__ import annotations

import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SCHEMA_DIR = PROJECT_ROOT / "private_test_data" / "schemas"
STAGING_NAME = "new.xsd"
# `show version` reports `Model: vmx`; put that word here beside the staged
# dump and the promoted name carries it.
STAGING_PLATFORM = "new.platform"
SOURCE_ENV = "JUNOSCFG_XSD_SOURCE"

# The release appears in the junos namespace declaration near the top of the
# dump, so a few kilobytes are enough; these files run to hundreds of megabytes.
_VERSION_RE = re.compile(r'xmlns:junos="http://xml\.juniper\.net/junos/([^/"]+)/junos"')
_VERSION_HEAD_BYTES = 65536


def read_version(path: Path) -> str:
    """The Junos release a dump declares, or ``unknown``."""
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        head = handle.read(_VERSION_HEAD_BYTES)
    match = _VERSION_RE.search(head)
    return match.group(1) if match else "unknown"


def read_platform(directory: Path | None = None) -> str | None:
    """The platform recorded beside a staged dump, or None.

    The dump itself cannot say — see the module docstring — so this reads what
    `show version` reported, if anybody wrote it down.
    """
    directory = directory or SCHEMA_DIR
    marker = directory / STAGING_PLATFORM
    if not marker.is_file():
        return None
    word = marker.read_text(encoding="utf-8").strip().split()
    if not word:
        return None
    return re.sub(r"[^A-Za-z0-9]+", "-", word[-1]).strip("-").lower() or None


def promote_staged(directory: Path | None = None, platform: str | None = None) -> Path | None:
    """Rename ``new.xsd`` to a name carrying its release, and its platform.

    Returns the new path, or None when there is nothing staged. The platform is
    whatever ``show version`` called the model; it comes from the *platform*
    argument, else from a ``new.platform`` file beside the dump, else the name
    carries the release alone. Two dumps of one release and platform are fine:
    the second becomes ``<version>-<platform>-2.xsd``. The staged file is never
    overwritten and never silently replaces an existing dump.
    """
    directory = directory or SCHEMA_DIR
    staged = directory / STAGING_NAME
    if not staged.is_file():
        return None

    platform = platform or read_platform(directory)
    stem = f"{read_version(staged)}-{platform}" if platform else read_version(staged)
    target = directory / f"{stem}.xsd"
    counter = 2
    while target.exists():
        target = directory / f"{stem}-{counter}.xsd"
        counter += 1
    staged.rename(target)
    (directory / STAGING_PLATFORM).unlink(missing_ok=True)
    return target


def available(directory: Path | None = None) -> list[Path]:
    """Every dump a developer has synced, promoting anything staged first."""
    directory = directory or SCHEMA_DIR
    if not directory.is_dir():
        return []
    promote_staged(directory)
    return sorted(p for p in directory.glob("*.xsd") if p.name != STAGING_NAME)
