"""Reading any format and writing any other keeps the configuration's meaning.

Every conversion is format -> IR -> format (ARCHITECTURE.md, "One interchange
format"), so one law covers every pair: each source of a shape reads as the
shape's IR, and each writer's output reads back as that IR, or as the part of
it the writer can carry. The rows are `tests/support/shapes.py`; a fix adds a
row there, not a test here. This replaces the hand-written per-pair tests, one
class per (reader, writer), that used to cover a few pairs each.

Set output is also compared line for line where a row declares it: a set line
is one statement, so its text is meaning, not layout.

`yaml-new` is the Junos JSON object in YAML (spec conversion/junos-json-yaml):
its output loads as the JSON output parses, key order included, the YAML
spelling of any JSON source reads as that source, and a `yaml` file converted
to `yaml-new` reads as the `yaml` file did.
"""

from __future__ import annotations

import json

import pytest
import yaml

from junoscfg import Format, convert_config
from tests.support.shapes import SHAPES, WRITERS, Shape, in_order, read_ir


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

    @pytest.mark.parametrize(
        ("shape", "reader"),
        [
            pytest.param(shape, reader, id=f"{shape.name}-{reader.value}")
            for shape in SHAPES
            if shape.ordered
            for reader in shape.sources
        ],
    )
    def test_an_entry_keeps_its_declared_key_order(self, shape: Shape, reader: Format) -> None:
        """An entry's key fields come first, in the order the XSD declares them.

        Dictionaries compare equal in any order, so the order is compared on its own,
        for the rows that declare it (spec conversion/entry-keys).
        """
        assert in_order(read_ir(shape.sources[reader], reader)) == in_order(shape.expected_ir())


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
        for text in shape.written.get(writer, ()):
            assert text in output, f"{text!r} missing from {writer.value} output:\n{output}"


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


#: The words that tag a structured statement; each leads the line it tags.
_TAG_WORDS = frozenset({"inactive:", "protect:"})


class TestAStructuredTagLeadsItsLine:
    """Structured output writes a tag before the statement it tags, never inside a line.

    A tag merged into its parent's line, `protocols inactive: lldp disable;`, is
    a line the device rejects (rows `an-inactive-flag-under-a-container` and
    `...-beside-a-sibling`, spec conversion/meta-tags). A quoted value that
    reads like a tag is one word with its quote, and is not a tag.
    """

    @pytest.mark.parametrize(("shape", "reader"), _readers())
    def test_no_tag_follows_a_word(self, shape: Shape, reader: Format) -> None:
        output = convert_config(
            shape.sources[reader], from_format=reader, to_format=Format.STRUCTURED
        )
        for line in output.splitlines():
            words = line.split()
            while words and words[0] in _TAG_WORDS:
                words.pop(0)
            assert not _TAG_WORDS & set(words), f"a tag inside {line.strip()!r}"


def _with(fmt: Format) -> list[object]:
    return [pytest.param(shape, id=shape.name) for shape in SHAPES if fmt in shape.sources]


class TestJunosYamlIsTheJsonObject:
    """yaml-new is the object the JSON writer builds and the JSON reader takes.

    The owner's default for yaml-new (2026-10-15, change yaml-new-format):
    the identical object to Junos JSON, so a file means the same in either.
    """

    @pytest.mark.parametrize(("shape", "reader"), _readers())
    def test_the_output_is_the_json_object(self, shape: Shape, reader: Format) -> None:
        source = shape.sources[reader]
        written = convert_config(source, from_format=reader, to_format=Format.YAML_NEW)
        expected = json.loads(convert_config(source, from_format=reader, to_format=Format.JSON))
        assert in_order(yaml.safe_load(written)) == in_order(expected)

    @pytest.mark.parametrize("shape", _with(Format.JSON))
    def test_the_yaml_spelling_of_json_reads_as_json(self, shape: Shape) -> None:
        """Every writer gives the same text for the JSON source and its YAML spelling.

        The YAML writer dumps the IR as read, so its equal text is an equal IR.
        """
        source = shape.sources[Format.JSON]
        spelled = yaml.safe_dump(json.loads(source), sort_keys=False, allow_unicode=True)
        for writer in WRITERS:
            assert convert_config(
                spelled, from_format=Format.YAML_NEW, to_format=writer
            ) == convert_config(source, from_format=Format.JSON, to_format=writer), writer.value


class TestIrYamlMigratesToJunosYaml:
    """`yaml` -> `yaml-new` is the migration path the planned rename relies on
    (docs/decisions/2026-10-15-yaml-new-before-renaming-yaml.md)."""

    @pytest.mark.parametrize("shape", _with(Format.YAML))
    def test_the_converted_file_reads_as_the_yaml_did(self, shape: Shape) -> None:
        source = shape.sources[Format.YAML]
        migrated = convert_config(source, from_format=Format.YAML, to_format=Format.YAML_NEW)
        assert read_ir(migrated, Format.YAML_NEW) == read_ir(source, Format.YAML)
        for writer in WRITERS:
            assert convert_config(
                migrated, from_format=Format.YAML_NEW, to_format=writer
            ) == convert_config(
                convert_config(source, from_format=Format.YAML, to_format=Format.JSON),
                from_format=Format.JSON,
                to_format=writer,
            ), writer.value
