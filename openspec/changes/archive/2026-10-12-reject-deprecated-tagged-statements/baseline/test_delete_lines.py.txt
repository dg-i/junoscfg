"""Delete lines in the display layer: the set lexer, the path filters, detection.

A ``delete`` line, or a ``delete:`` prefix in curly input, is a statement like
``set`` and ``deactivate``: `SetConverter` writes it, the path filters keep it,
and format detection counts it as display set. What conversion makes of a
delete is `tests/unit/convert/test_delete_operation.py` and the delete rows of
`tests/support/shapes.py`.
"""

from __future__ import annotations

import pytest

from junoscfg.display import (
    SetConverter,
    filter_set_by_path,
    filter_structured_by_path,
    is_display_set,
)


class TestSetConverterWritesADeletePrefix:
    """Structured with a ``delete:`` prefix becomes set and delete lines."""

    def test_delete_prefix_to_set(self) -> None:
        """'delete: services { ssh; }' → 'delete services' (marks the container)."""
        input_text = "delete: services {\n    ssh;\n}"
        with pytest.deprecated_call():  # to_set() is deprecated (structured-one-line-blocks)
            result = SetConverter(input_text).to_set()
        assert "delete services" in result
        assert "set services ssh" in result

    def test_delete_prefix_leaf(self) -> None:
        """'system { delete: host-name router1; }' → 'delete system host-name router1'."""
        input_text = "system {\n    delete: host-name router1;\n}"
        with pytest.deprecated_call():  # to_set() is deprecated (structured-one-line-blocks)
            result = SetConverter(input_text).to_set()
        assert "delete system host-name router1" in result


class TestFilterSetDelete:
    """filter_set_by_path handles delete lines."""

    def test_filters_delete_lines(self) -> None:
        text = (
            "set system services ssh\ndelete system services ssh\nset interfaces ge-0/0/0 unit 0\n"
        )
        result = filter_set_by_path(text, ["system", "services"])
        assert "set system services ssh\n" in result
        assert "delete system services ssh\n" in result
        assert "interfaces" not in result

    def test_relative_with_delete(self) -> None:
        text = "set system services ssh\ndelete system services ssh\n"
        result = filter_set_by_path(text, ["system", "services"], relative=True)
        assert "set ssh\n" in result
        assert "delete ssh\n" in result


class TestFilterStructuredDelete:
    """filter_structured_by_path handles delete: prefix."""

    def test_preserves_delete_prefix(self) -> None:
        text = "system {\n    delete: services {\n        ssh;\n    }\n}\n"
        result = filter_structured_by_path(text, ["system"], relative=True)
        assert "delete: services {" in result


class TestIsDisplaySetDelete:
    """is_display_set accepts delete lines."""

    def test_delete_only(self) -> None:
        assert is_display_set("delete system services ssh\n")

    def test_mixed_set_delete(self) -> None:
        assert is_display_set("set system host-name r1\ndelete system services ssh\n")

    def test_mixed_set_deactivate_delete(self) -> None:
        assert is_display_set(
            "set system host-name r1\ndeactivate system syslog\ndelete system services ssh\n"
        )
