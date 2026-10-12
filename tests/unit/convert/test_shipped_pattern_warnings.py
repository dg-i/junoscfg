"""All shipped patterns reach field validation without Python regex warnings.

The posix-bracket-escape review F3 called for the complete shipped pattern table,
beyond the individual literal-bracket regression in test_field_validator.py.
Synthetic schema leaves select every entry through the public validation door;
the table itself comes unchanged from the bundled_tree session fixture.
"""

from __future__ import annotations

import re
import warnings
from typing import TYPE_CHECKING, Any

from junoscfg.convert import validate_ir
from tests.support.artifacts import using_tree

if TYPE_CHECKING:
    from pathlib import Path


def test_every_shipped_pattern_validates_without_python_warnings(
    bundled_tree: dict[str, Any], tmp_path: Path
) -> None:
    patterns = bundled_tree["_patterns"]
    assert patterns, "the shipped pattern table must be exercised"
    leaves = {f"pattern-{index}": {"l": True, "r": index} for index in range(len(patterns))}
    tree = {"_patterns": patterns, "c": {"configuration": {"c": leaves}}}
    config = {name: "router1" for name in leaves}

    with using_tree(tmp_path, tree), warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        re.purge()  # A cached regex must not hide a first-compilation warning.
        validate_ir(config)

    assert [(warning.category.__name__, str(warning.message)) for warning in caught] == []


def test_validation_warning_capture_detects_ambiguous_set_intersection(tmp_path: Path) -> None:
    """A real regex compilation warning verifies the sweep's capture boundary."""
    tree = {
        "_patterns": [r"^[a&&b]$"],
        "c": {"configuration": {"c": {"tag": {"l": True, "r": 0}}}},
    }
    with using_tree(tmp_path, tree), warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        re.purge()
        result = validate_ir({"tag": "a"})

    assert result.valid
    assert any(
        warning.category is FutureWarning and "set intersection" in str(warning.message)
        for warning in caught
    )
