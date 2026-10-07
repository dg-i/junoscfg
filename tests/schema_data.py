"""Discovery of developer-supplied device schema dumps.

A user needs none of this: the package ships generated artifacts and works
without a device. A developer *should* sync one or more NETCONF XSD dumps into
``private_test_data/schemas/``, which is gitignored, and the tests marked
``schema`` then run against each of them.

Drop a fresh dump in as ``new.xsd`` and it is promoted on first use to a name
carrying its Junos release, so several devices and releases can sit side by
side without manual bookkeeping.
"""

from __future__ import annotations

import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SCHEMA_DIR = PROJECT_ROOT / "private_test_data" / "schemas"
STAGING_NAME = "new.xsd"
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


def promote_staged(directory: Path | None = None) -> Path | None:
    """Rename ``new.xsd`` to a name carrying its release.

    Returns the new path, or None when there is nothing staged. Two devices on
    one release are fine: the second becomes ``<version>-2.xsd``. The staged
    file is never overwritten and never silently replaces an existing dump.
    """
    directory = directory or SCHEMA_DIR
    staged = directory / STAGING_NAME
    if not staged.is_file():
        return None

    version = read_version(staged)
    target = directory / f"{version}.xsd"
    counter = 2
    while target.exists():
        target = directory / f"{version}-{counter}.xsd"
        counter += 1
    staged.rename(target)
    return target


def available(directory: Path | None = None) -> list[Path]:
    """Every dump a developer has synced, promoting anything staged first."""
    directory = directory or SCHEMA_DIR
    if not directory.is_dir():
        return []
    promote_staged(directory)
    return sorted(p for p in directory.glob("*.xsd") if p.name != STAGING_NAME)
