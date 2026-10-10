"""Reading any format and writing any other keeps the configuration's meaning.

Every conversion is format -> IR -> format (ARCHITECTURE.md, "One interchange
format"), so one law covers every pair: each source of a shape reads as the
shape's IR, and each writer's output reads back as that IR, or as the part of
it the writer can carry. The rows are `tests/support/shapes.py`; a fix adds a
row there, not a test here. This replaces the hand-written per-pair tests, one
class per (reader, writer), that used to cover a few pairs each.

Set output is also compared line for line where a row declares it: a set line
is one statement, so its text is meaning, not layout.
"""

from __future__ import annotations

import pytest

from junoscfg import Format, convert_config
from tests.support.shapes import SHAPES, WRITERS, Shape, read_ir


def _readers() -> list[object]:
    return [
        pytest.param(shape, reader, id=f"{shape.name}-{reader.value}")
        for shape in SHAPES
        for reader in shape.sources
    ]


def _pairs(shapes: list[Shape]) -> list[object]:
    return [
        pytest.param(shape, reader, writer, id=f"{shape.name}-{reader.value}-{writer.value}")
        for shape in shapes
        for reader in shape.sources
        for writer in WRITERS
    ]


class TestEveryReaderGivesTheShapeIr:
    """Every spelling of one configuration reads as one IR."""

    @pytest.mark.parametrize(("shape", "reader"), _readers())
    def test_the_source_reads_as_the_ir(self, shape: Shape, reader: Format) -> None:
        assert read_ir(shape.sources[reader], reader) == shape.expected_ir()


class TestEveryWriterKeepsTheIr:
    """What a writer writes reads back as what was read."""

    @pytest.mark.parametrize(("shape", "reader", "writer"), _pairs(SHAPES))
    def test_the_output_reads_back_as_the_ir(
        self, shape: Shape, reader: Format, writer: Format
    ) -> None:
        output = convert_config(shape.sources[reader], from_format=reader, to_format=writer)
        assert read_ir(output, writer) == shape.expected_after(writer)
        for text in shape.never_written.get(writer, ()):
            assert text not in output, f"{writer.value} output carries {text!r}"


class TestSetOutputIsTheDeviceLines:
    """Set output from every reader is the same lines, in the declared order."""

    @pytest.mark.parametrize(
        ("shape", "reader"),
        [
            pytest.param(shape, reader, id=f"{shape.name}-{reader.value}")
            for shape in SHAPES
            if shape.set_output is not None
            for reader in shape.sources
        ],
    )
    def test_the_set_lines(self, shape: Shape, reader: Format) -> None:
        output = convert_config(shape.sources[reader], from_format=reader, to_format=Format.SET)
        assert output == shape.set_output


class TestASecondWriterKeepsTheIr:
    """A writer's output is a source like any other: converting it again loses nothing.

    For the shapes every writer carries whole, the second hop of each chain
    (JSON -> set -> structured, set -> structured -> set, XML -> YAML -> set,
    ...) reads back as the IR, and set output after it is still the declared
    lines.
    """

    @pytest.mark.parametrize(
        ("shape", "reader", "writer"), _pairs([shape for shape in SHAPES if shape.lossless])
    )
    def test_every_second_writer(self, shape: Shape, reader: Format, writer: Format) -> None:
        first = convert_config(shape.sources[reader], from_format=reader, to_format=writer)
        for second in WRITERS:
            output = convert_config(first, from_format=writer, to_format=second)
            assert read_ir(output, second) == shape.expected_ir(), f"then {second.value}"
            if second is Format.SET and shape.set_output is not None:
                assert output == shape.set_output, f"then {second.value}"
