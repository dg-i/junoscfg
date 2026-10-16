"""junoscfg against the device: its set rendering of every capture is the device's.

A capture is a configuration a Junos device loaded and printed in four
formats (`tests/data/device/README.md`); the device is the oracle above the
schema model and everything junoscfg generates. For every capture and every
rendering, junoscfg's set output equals the device's own display set, less the
lines `known-differences.json` records with their class. A difference not
recorded fails, and so does a recorded one that is gone: a fix shrinks the
record (`tools/device_differences.py`), it never hides in it.

That the four renderings read to one configuration follows: each must give
the device's set.
"""

from __future__ import annotations

import json
from typing import Any

import pytest
import yaml

from junoscfg import Format, convert_config
from tests.support.devices import DEVICE_DATA, FORMATS, captures, known_differences, recorded
from tests.support.shapes import in_order, read_ir

CASES = [
    pytest.param(capture, suffix, id=f"{capture.key}.{suffix}")
    for capture in captures()
    for suffix in FORMATS
]
KINDS = {"defect", "equivalent", "open", "device-quirk"}


class TestJunoscfgWritesTheDevicesSet:
    @pytest.mark.parametrize(("capture", "suffix"), CASES)
    def test_only_the_recorded_lines_differ(self, capture, suffix: str) -> None:
        found, expected = capture.difference(suffix), recorded(capture, suffix)
        problems = [
            f"{side} {why}: {line}"
            for side in ("missing", "extra")
            for why, lines in (
                ("but not recorded", set(found[side]) - set(expected[side])),
                ("recorded but gone (shrink the record)", set(expected[side]) - set(found[side])),
            )
            for line in sorted(lines)
        ]
        assert not problems, "\n".join(problems)


#: The statements valid at every level (spec schema-pipeline/universal-statements).
UNIVERSAL = frozenset({"apply-groups", "apply-groups-except", "apply-flags", "apply-macro"})


def _universal_statements(node: Any, path: tuple[str, ...], found: dict) -> None:
    """Every universal statement in an IR, by its path, an entry named by its key."""
    if isinstance(node, dict):
        for key, value in node.items():
            if key in UNIVERSAL:
                found[(*path, key)] = json.dumps(value, sort_keys=True)
            elif key == "junoscfg:unplaced" and isinstance(value, dict):
                for text in value:
                    if text.split()[0] in UNIVERSAL:
                        found[(*path, "unplaced", text)] = "kept"
            else:
                _universal_statements(value, (*path, key), found)
    elif isinstance(node, list):
        for index, item in enumerate(node):
            entry = item.get("name", index) if isinstance(item, dict) else index
            _universal_statements(item, (*path, str(entry)), found)


def _read(capture: Any, suffix: str) -> dict:
    rendered = convert_config(
        capture.rendering(suffix),
        from_format=FORMATS[suffix],
        to_format=Format.JSON,
        validate=False,
    )
    found: dict = {}
    _universal_statements(json.loads(rendered), (), found)
    return found


class TestEveryDoorReadsTheDevicesUniversalStatements:
    """Each reader gives the universal statements the device's own JSON holds.

    The device law above compares set output only, and set output hid both
    defects: `apply-flags omit` kept whole was written back verbatim, and a
    nested `apply-groups` with one group read from XML as a scalar where the
    device's JSON writes a list. Change universal-statements-from-tree
    (Test/Challenge finding 1). The curly rendering of group GR-OMIT is the
    device's `{ /* OMITTED */ }` (class `omitted-curly`), so it is left out
    there.
    """

    @pytest.mark.parametrize(
        ("capture", "suffix"),
        [
            pytest.param(capture, suffix, id=f"{capture.key}.{suffix}")
            for capture in captures()
            for suffix in ("conf", "set", "xml")
        ],
    )
    def test_every_door_reads_the_devices_universal_statements(self, capture, suffix: str) -> None:
        device = _read(capture, "json")
        got = _read(capture, suffix)
        if suffix == "conf":
            device = {path: v for path, v in device.items() if "GR-OMIT" not in path}
            got = {path: v for path, v in got.items() if "GR-OMIT" not in path}
        assert got == device

    def test_the_captures_hold_universal_statements(self) -> None:
        """The comparison above means something only where there is something to compare."""
        held = {capture.key: _read(capture, "json") for capture in captures()}
        assert sum(len(found) for found in held.values()) >= 30, held
        assert sum(1 for found in held.values() if found) >= 3, held
        flags = [path for found in held.values() for path in found if path[-1] == "apply-flags"]
        assert len(flags) >= 2, flags


class TestJunosYamlIsTheDevicesJson:
    """yaml-new is the Junos JSON object in YAML, over every device capture.

    Spec conversion/junos-json-yaml. The QFX5120 capture on 25.2R2-S1.5 spells
    15 empty containers `{}` where the vMX capture of the same source on
    23.2R2-S7.5 spells `[null]`
    (tests/data/device/synthetic/qfx5120-25.2R2-S1.5/junoscfg-oracle.json.gz);
    yaml-new writes what JSON output writes, `[null]`, and whether the QFX
    loads that is an open device question (change yaml-new-format).
    """

    @pytest.mark.parametrize(("capture", "suffix"), CASES)
    def test_every_rendering_writes_the_json_object(self, capture, suffix: str) -> None:
        source = capture.rendering(suffix)

        def write(writer: Format) -> str:
            return convert_config(
                source, from_format=FORMATS[suffix], to_format=writer, validate=False
            )

        written = yaml.safe_load(write(Format.YAML_NEW))
        assert in_order(written) == in_order(json.loads(write(Format.JSON)))

    @pytest.mark.parametrize(
        "capture", [pytest.param(capture, id=capture.key) for capture in captures()]
    )
    def test_the_devices_json_in_yaml_reads_as_the_json(self, capture) -> None:
        source = capture.rendering("json")
        spelled = yaml.safe_dump(json.loads(source), sort_keys=False, allow_unicode=True)
        for writer in (Format.YAML, Format.SET):
            assert convert_config(
                spelled, from_format=Format.YAML_NEW, to_format=writer, validate=False
            ) == convert_config(source, from_format=Format.JSON, to_format=writer, validate=False)


class TestTheRecordExplainsItself:
    def test_every_class_has_a_kind_and_a_definition(self) -> None:
        classes = known_differences()["classes"]
        assert classes
        for name, about in classes.items():
            assert about["kind"] in KINDS, name
            assert about["definition"].strip(), name

    def test_every_recorded_line_has_a_defined_class(self) -> None:
        classes = set(known_differences()["classes"])
        labels = {
            label
            for entry in known_differences()["differences"].values()
            for lines in entry.values()
            for label in lines.values()
        }
        assert labels <= classes, sorted(labels - classes)

    def test_every_defined_class_has_a_recorded_line(self) -> None:
        """A class whose lines a fix removed leaves the record with them.

        Test/Challenge F9 (change structured-one-line-blocks): `labels <= classes`
        alone let `omitted-block-emitted` stay defined after its lines went.
        """
        classes = set(known_differences()["classes"])
        labels = {
            label
            for entry in known_differences()["differences"].values()
            for lines in entry.values()
            for label in lines.values()
        }
        assert classes <= labels, sorted(classes - labels)

    def test_every_recorded_rendering_is_a_capture(self) -> None:
        keys = {f"{c.key}.{suffix}" for c in captures() for suffix in FORMATS}
        assert set(known_differences()["differences"]) <= keys


class TestTheCapturesAreWhatTheManifestSays:
    def test_every_capture_has_its_four_renderings(self) -> None:
        for capture in captures():
            for suffix in FORMATS:
                assert (
                    DEVICE_DATA / capture.source / capture.device / f"{capture.name}.{suffix}.gz"
                ).is_file()

    def test_no_rendering_is_outside_the_manifest(self) -> None:
        listed = {
            DEVICE_DATA / c.source / c.device / f"{c.name}.{suffix}.gz"
            for c in captures()
            for suffix in FORMATS
        }
        on_disk = {p for p in DEVICE_DATA.glob("*/*/*.gz") if p.parent.name != "sources"}
        assert on_disk == listed

    def test_every_device_is_described(self) -> None:
        manifest = json.loads((DEVICE_DATA / "manifest.json").read_text(encoding="utf-8"))
        for capture in captures():
            device = manifest["devices"][capture.device]
            assert device["model"] and device["release"] and device["release_source"]


class TestJuniperCarriesItsLicence:
    """Apache-2.0, section 4: the licence, the notice, and a statement of what changed."""

    def test_the_licence_and_notice_sit_beside_the_files(self) -> None:
        licence = (DEVICE_DATA / "jvd" / "LICENSE").read_text(encoding="utf-8")
        notice = (DEVICE_DATA / "jvd" / "NOTICE").read_text(encoding="utf-8")
        assert "Apache License" in licence and "Version 2.0" in licence
        assert "Juniper Networks" in notice
        assert "Modifications" in notice

    def test_every_jvd_capture_has_its_unmodified_source_and_origin(self) -> None:
        manifest = json.loads((DEVICE_DATA / "manifest.json").read_text(encoding="utf-8"))
        for capture in captures():
            if capture.source == "jvd":
                assert (DEVICE_DATA / "jvd" / "sources" / f"{capture.name}.conf.gz").is_file()
                assert manifest["jvd"]["paths"][capture.name]
        assert len(manifest["jvd"]["commit"]) == 40


def _selectable_paths(node: Any, prefix: tuple[str, ...], depth: int) -> list[tuple[str, ...]]:
    """Every path of mapping keys to *depth*: mappings, lists, leaves, flags and
    annotation keys alike, as `--path` addresses them."""
    if not isinstance(node, dict) or depth == 0:
        return []
    found: list[tuple[str, ...]] = []
    for key, value in node.items():
        found.append((*prefix, key))
        found.extend(_selectable_paths(value, (*prefix, key), depth - 1))
    return found


def _value_at(document: Any, path: tuple[str, ...]) -> Any:
    """The value at *path* of an absolute document; `groups` holds its entries
    directly in the Junos JSON object, so a `group` step after it stays put."""
    node = document["configuration"]
    for step, key in enumerate(path):
        if key == "group" and step and path[step - 1] == "groups" and isinstance(node, list):
            continue
        node = node[key]
    return node


def _below_the_path(line: str, path: tuple[str, ...]) -> str | None:
    """An absolute set line without its path's words, or ``None`` when the line
    is not under the path. Each key is consumed when it is the line's next word;
    a key the line does not name (a list name the schema hides, an annotation
    key, the kept-statements key) is passed. The keys the set writer renames
    (`ieee-802.3ad`, `end-range`, the NAT `match` keys) sit inside lists, which
    no path of mapping keys reaches."""
    command, _, rest = line.partition(" ")
    words = rest.split(" ") if rest else []
    for key in path:
        if words and words[0] == key:
            words.pop(0)
    remainder = " ".join(words)
    return f"{command} {remainder}" if remainder else command


def _put_back(relative: str, words: list[str], entries: str | None) -> str:
    """Relative structured text put back under the path's *words*; *entries*
    is the list or leaf name each top-level statement is written after."""
    text = relative
    if entries is not None:
        lines = []
        for line in text.splitlines():
            if line and not line.startswith((" ", "}")):
                tags = ""
                while line.startswith(("inactive: ", "protect: ", "replace: ")):
                    tag, _, line = line.partition(" ")
                    tags += tag + " "
                line = f"{tags}{entries} {line}"
            lines.append(line + "\n")
        text = "".join(lines)
    for word in reversed(words):
        text = f"{word} {{\n" + "".join(f"    {line}\n" for line in text.splitlines()) + "}\n"
    return text


class TestRelativeSelections:
    """`--path --relative` writes what absolute output writes at the path, without
    the path (spec conversion/path-filtering), for every path of mapping keys
    to depth 4 of every device JSON capture: json, yaml-new and yaml give the
    absolute document's value there; every relative set line is its absolute
    line without the path's words; relative structured text, put back under
    those words, reads as the absolute text (a tag on the selected statement
    itself, which structured output notes and cannot write, aside)."""

    @pytest.mark.parametrize(
        "capture", [pytest.param(capture, id=capture.key) for capture in captures()]
    )
    def test_a_relative_selection_is_the_absolute_one_without_its_path(self, capture) -> None:
        source = capture.rendering("json")
        loaded = json.loads(source)
        configuration = loaded.get("configuration", loaded)
        paths = _selectable_paths(configuration, (), 4)
        assert paths

        def written(to_format: Format, path: tuple[str, ...], relative: bool) -> str:
            return convert_config(
                source,
                from_format=Format.JSON,
                to_format=to_format,
                path=".".join(path),
                relative=relative,
                validate=False,
            )

        problems = []
        for path in paths:
            for to_format, load in (
                (Format.JSON, json.loads),
                (Format.YAML_NEW, yaml.safe_load),
                (Format.YAML, yaml.safe_load),
            ):
                relative = load(written(to_format, path, True))
                if relative != _value_at(load(written(to_format, path, False)), path):
                    problems.append(f"{to_format.value} {'.'.join(path)}")
            absolute_set = written(Format.SET, path, False).splitlines()
            relative_set = written(Format.SET, path, True).splitlines()
            if relative_set != [_below_the_path(line, path) for line in absolute_set]:
                problems.append(f"set {'.'.join(path)}")
            parent = configuration
            for key in path[:-1]:
                parent = parent[key]
            value = parent[path[-1]]
            words = list(path)
            named = [
                word for word in words if any(f" {word} " in f" {line} " for line in absolute_set)
            ]
            if not isinstance(value, (dict, list)) or isinstance(parent.get(f"@{path[-1]}"), dict):
                continue
            if isinstance(value, dict) and "@" in value:
                continue
            entries = (
                named[-1] if isinstance(value, list) and named and named[-1] == words[-1] else None
            )
            relative_text = written(Format.STRUCTURED, path, True)
            if not relative_text:
                continue
            put = _put_back(relative_text, named[:-1] if entries else named, entries)
            if read_ir(put, Format.STRUCTURED) != read_ir(
                written(Format.STRUCTURED, path, False), Format.STRUCTURED
            ):
                problems.append(f"structured {'.'.join(path)}")
        assert not problems, "\n".join(problems[:40])


class TestAnAbsoluteSelectionKeepsItsTags:
    """A path ending at a statement whose tags the device writes beside it (a
    deactivated flag, a commented leaf or list: `"@<key>"`) keeps them when
    selected absolute, as the selection of its parent writes them, for every
    path of mapping keys to depth 5 of every device JSON capture (owner request
    2026-10-16, change own-crash-fixes; Test/Challenge TC5)."""

    def test_every_tagged_statement_keeps_its_tags(self) -> None:
        def written(source: str, path: tuple[str, ...]) -> Any:
            text = convert_config(
                source,
                from_format=Format.JSON,
                to_format=Format.JSON,
                path=".".join(path) or None,
                validate=False,
            )
            return json.loads(text)["configuration"]

        tagged, problems = [], []
        for capture in captures():
            source = capture.rendering("json")
            loaded = json.loads(source)
            configuration = loaded.get("configuration", loaded)
            for path in _selectable_paths(configuration, (), 5):
                parent = configuration
                for key in path[:-1]:
                    parent = parent[key]
                if path[-1].startswith("@") or f"@{path[-1]}" not in parent:
                    continue
                tagged.append(f"{capture.key} {'.'.join(path)}")
                wanted, got = written(source, path[:-1]), written(source, path)
                for key in path[:-1]:
                    wanted, got = wanted[key], got[key]
                if got != {k: wanted[k] for k in (path[-1], f"@{path[-1]}")}:
                    problems.append(tagged[-1])
        assert tagged
        assert not problems, "\n".join(problems)
