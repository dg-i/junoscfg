"""What conversion says about a delete it cannot write.

Set output writes ``delete <path>`` after the content it deletes; structured
output has no delete, so it drops the annotation and keeps the content. Both
are rows of the shape catalogue (`tests/support/shapes.py`, the delete rows),
checked through every reader and writer by `tests/contract/test_format_matrix.py`.
This file keeps what the rows cannot see: the note that reports the drop, which
travels with the result and never reaches stderr. The display filters' handling
of delete lines is `tests/unit/display/test_delete_lines.py`.
"""

from __future__ import annotations

import json
from typing import Any

import pytest

from junoscfg import Format, convert_config_result


def _json(config: dict[str, Any]) -> str:
    return json.dumps({"configuration": config})


class TestStructuredOutputDropsADeleteWithANote:
    """A delete is dropped from structured output with a note, never on stderr."""

    @pytest.mark.parametrize(
        ("source", "from_format", "kept"),
        [
            pytest.param(
                _json({"system": {"services": {"@": {"operation": "delete"}, "ssh": [None]}}}),
                Format.JSON,
                "ssh",
                id="a-deleted-container",
            ),
            pytest.param(
                _json({"system": {"host-name": "router1", "@host-name": {"operation": "delete"}}}),
                Format.JSON,
                "host-name",
                id="a-deleted-leaf",
            ),
            pytest.param(
                "set system services ssh\ndelete system services ssh",
                Format.SET,
                None,
                id="a-statement-set-then-deleted",
            ),
        ],
    )
    def test_the_delete_is_dropped_with_a_note(
        self,
        source: str,
        from_format: Format,
        kept: str | None,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        converted = convert_config_result(
            source, from_format=from_format, to_format=Format.STRUCTURED
        )
        assert "delete:" not in converted.output
        if kept is None:
            assert converted.output.strip() == ""
        else:
            assert kept in converted.output
        assert capsys.readouterr().err == ""
        assert "delete annotation(s) dropped" in converted.diagnostics[0].render()


class TestAnAnnotationOnlyLeafIsNoFieldError:
    """`"host-name": {"@": {"operation": "delete"}}` has no value to validate."""

    def test_no_field_validate_warning_for_annotation_only_leaf(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        source = _json({"system": {"host-name": {"@": {"operation": "delete"}}}})
        converted = convert_config_result(source, from_format=Format.JSON, to_format=Format.SET)
        assert converted.output == "delete system host-name\n"
        assert not [d for d in converted.diagnostics if d.source == "field-validate"]
        assert "field-validate" not in capsys.readouterr().err
