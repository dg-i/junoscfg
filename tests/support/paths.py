"""Where things are, for every test, whatever directory pytest was started in.

A path relative to the working directory passes from the repository root and
fails from anywhere else; one counted from a test file's own ``__file__``
breaks when the file moves. Both used to exist side by side.
"""

from __future__ import annotations

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
#: The committed synthetic configurations: router1 in every format.
EXAMPLES = PROJECT_ROOT / "examples"
#: Committed test data: device captures, the set corpus, the keyed-entries XSD, goldens.
TEST_DATA = PROJECT_ROOT / "tests" / "data"
#: The package source, for tests that scan it.
PACKAGE_SRC = PROJECT_ROOT / "src" / "junoscfg"
#: The bundled validation artifacts.
ARTIFACT_DIR = PACKAGE_SRC / "validate" / "data"
#: Gitignored home of operator data: XSD dumps, cloned corpora.
PRIVATE_DATA = PROJECT_ROOT / "private_test_data"
