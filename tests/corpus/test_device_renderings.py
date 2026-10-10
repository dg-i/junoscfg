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

import pytest

from tests.support.devices import DEVICE_DATA, FORMATS, captures, known_differences, recorded

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
