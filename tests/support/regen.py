"""Which device dump ``--regen-schema`` rebuilds the bundled artifacts from.

Kept out of ``conftest.py`` so it can be imported and tested like any other
helper: a conftest is pytest's to load, and importing it as a module loads it
twice.
"""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

from junoscfg.display import find_artifact, forget_loaded_artifacts, read_artifact_text
from tests.support import schema_data
from tests.support.paths import ARTIFACT_DIR, PRIVATE_DATA, PROJECT_ROOT

# Where --regen-schema looks for the device XSD. It cannot be committed: it is
# a NETCONF dump from a real device at a specific Junos release, which is both
# large and operator data. private_test_data/ is the documented, gitignored
# home for exactly that.
XSD_SOURCE_ENV = "JUNOSCFG_XSD_SOURCE"
XSD_SOURCE_DIR = PRIVATE_DATA
#: pytest keeps 0 to 5 for itself; this one means "no dump to regenerate from".
REGEN_SOURCE_EXIT = 7
_TRAIN_RE = re.compile(r"^(\d+\.\d+)")


class XsdSourceError(Exception):
    """No single dump answers ``--regen-schema``; the message says what would."""


def shipped_release_train(artifact_dir: Path = ARTIFACT_DIR) -> str:
    """The release train of the bundled artifacts: ``25.2`` for ``25.2R0``.

    The metadata records the namespace release the dump declared, which is
    the train's base; a dump's own header names the full release, such as
    ``25.2R2-S1.5``. The train is what the two share.
    """
    meta = find_artifact(artifact_dir, "junos-schema-meta.json")
    if meta is None:
        raise XsdSourceError(f"no junos-schema-meta.json under {artifact_dir}")
    version = str(json.loads(read_artifact_text(meta)).get("junos_version", ""))
    match = _TRAIN_RE.match(version)
    if match is None:
        raise XsdSourceError(
            f"the bundled metadata names no release train ({version!r}), so no dump can "
            f"be matched to it; name the dump to rebuild from with {XSD_SOURCE_ENV}"
        )
    return match.group(1)


def _dumps(directory: Path) -> list[Path]:
    """Every ``.xsd`` file in *directory*, left as they are: a lookup renames nothing."""
    if not directory.is_dir():
        return []
    return sorted(p for p in directory.glob("*.xsd") if p.is_file())


def find_xsd_source(
    *,
    train: str | None = None,
    schemas_dir: Path | None = None,
    legacy_dir: Path | None = None,
    override: str | None = None,
) -> Path:
    """The dump to regenerate from: *override*, or the one dump of the shipped train.

    This used to be whichever dump sorted newest under
    ``private_test_data/schemas/``, so the documented pre-commit step would
    have replaced the shipped artifacts with whatever a developer had synced
    last, as a side effect of a file name. The release is an explicit choice:
    the dump whose release matches the bundled metadata's train, read from the
    dump's own header, or the one ``JUNOSCFG_XSD_SOURCE`` names, which is how
    the release moves on purpose. Anything else raises, with the reason,
    rather than picking. ``None`` for *override* means the variable is unset;
    set and empty is an error, not a fallback.
    """
    if override is not None:
        path = Path(override).expanduser()
        if not override.strip() or not path.is_file():
            raise XsdSourceError(f"{XSD_SOURCE_ENV}={override!r} is not a file")
        if schema_data.read_version(path) == "unknown":
            raise XsdSourceError(
                f"{XSD_SOURCE_ENV}={override} declares no Junos release in its header; "
                "artifacts built from it could not be matched to a dump again"
            )
        return path
    train = train or shipped_release_train()
    schemas_dir = schemas_dir or schema_data.SCHEMA_DIR
    legacy_dir = XSD_SOURCE_DIR if legacy_dir is None else legacy_dir
    candidates = _dumps(schemas_dir) + _dumps(legacy_dir)
    releases = {p: schema_data.read_version(p) for p in candidates}
    # The train followed by anything but another digit: 25.2R2-S1.5, 25.2X75-D10,
    # 25.2R2-S1.5-EVO, and not 25.20R1.
    wanted = re.compile(rf"{re.escape(train)}(?![0-9])")
    matching = [p for p in candidates if wanted.match(releases[p])]
    if len(matching) == 1:
        return matching[0]

    def _show(p: Path) -> str:
        where = p.relative_to(PROJECT_ROOT) if p.is_relative_to(PROJECT_ROOT) else p
        return f"{where} ({releases[p]})"

    if not matching:
        found = ", ".join(_show(p) for p in candidates) or "none"
        raise XsdSourceError(
            f"--regen-schema: no dump of the shipped release {train} under {schemas_dir} "
            f"or beside it; found: {found}. Sync the shipped release's dump, or name "
            f"another with {XSD_SOURCE_ENV} to move the release on purpose."
        )
    raise XsdSourceError(
        f"--regen-schema: {len(matching)} dumps of release {train}: "
        + ", ".join(_show(p) for p in matching)
        + f". Name one with {XSD_SOURCE_ENV}."
    )


def regenerate_from(xsd_source: Path) -> None:
    """Rebuild the bundled artifacts from *xsd_source* and drop the cached tree."""
    subprocess.run(
        ["uv", "run", "junoscfg", "schema", "generate", str(xsd_source), "-o", str(ARTIFACT_DIR)],
        check=True,
        capture_output=True,
    )
    forget_loaded_artifacts()
