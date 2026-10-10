"""Discovery of the Juniper Validated Designs corpus.

A user needs none of this. `github.com/Juniper/jvd` is Juniper's own published
reference configuration set — about 1,500 files and five million lines across
QFX, ACX, MX, PTX and SRX — and it is the only broad, independent Junos corpus
this project has access to. Three defects that every committed fixture missed
were found against it in one afternoon.

It is cloned at test time rather than vendored: it is someone else's
repository, it is large, and a stale copy would be worse than none. Point
``JUNOSCFG_JVD_PATH`` at a clone you already have, or let ``--jvd`` make a
shallow one under ``private_test_data/``, which is gitignored.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

from tests.support.paths import PRIVATE_DATA

CACHE_DIR = PRIVATE_DATA / "jvd"
PATH_ENV = "JUNOSCFG_JVD_PATH"
CLONE_URL = "https://github.com/Juniper/jvd.git"

# Files that are documentation carrying configuration rather than
# configuration: prose, section labels such as `AN3:`, and the CLI prompt
# captured above a dump. They are not junoscfg's to parse.
NOT_CONFIGURATION = (
    "show configuration",
    "Unknown statement: AN",
    "Unknown statement: MA",
    "Unknown statement: MSE",
    "Unknown statement: MEG",
    "lets ISIS hellos use the full",
    "## SECRET-DATA",
)


def corpus_root() -> Path | None:
    """An existing clone, or None. Never clones."""
    override = os.environ.get(PATH_ENV)
    if override:
        path = Path(override).expanduser()
        return path if (path / ".git").is_dir() or any(path.rglob("*.conf")) else None
    return CACHE_DIR if CACHE_DIR.is_dir() else None


def ensure_corpus() -> Path | None:
    """The corpus, cloning it shallowly if there is none. Needs the network."""
    existing = corpus_root()
    if existing is not None:
        return existing
    CACHE_DIR.parent.mkdir(parents=True, exist_ok=True)
    try:
        subprocess.run(
            ["git", "clone", "--depth", "1", "--quiet", CLONE_URL, str(CACHE_DIR)],
            check=True,
            capture_output=True,
            timeout=600,
        )
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, OSError):
        return None
    return CACHE_DIR if CACHE_DIR.is_dir() else None


def configs(root: Path | None = None) -> list[Path]:
    """Every ``.conf`` in the corpus, in a stable order."""
    root = root or corpus_root()
    if root is None:
        return []
    return sorted(root.rglob("*.conf"))


def is_configuration(error_text: str) -> bool:
    """False when a conversion failure is the file's fault, not junoscfg's."""
    return not any(marker in error_text for marker in NOT_CONFIGURATION)
