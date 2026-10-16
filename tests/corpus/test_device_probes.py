"""junoscfg against a device probe: what the device took, refused and printed.

A probe is the owner's run of the probe's own synthetic statements on one
device, in `configure private` and never committed; its sanitized record is
`tests/data/device/probes/<device>/<date>.json` (`tests/data/device/README.md`).
The device is the oracle above the schema model: set validation takes what it
took and refuses what it refused, every rendering it printed reads as its own
display set and validates, and a `--path` selection loads as the device prints
the same statements. The 2026-10-16 QFX5120 probe settled HOLD-TIME-001,
ANCESTOR-TAGS-001, RELATIVE-TAGS-001, LEAF-LIST-VALUE-TAGS-001,
RENAME-EVIDENCE-001, JSON-KEYWORD-ALIAS-001, UNDOCUMENTED-001 and
VERB-PREFIX-001 (change device-probe-fixes).
"""

from __future__ import annotations

import json
import re
from typing import Any

import pytest

from junoscfg import Format, convert_config, convert_config_result, validate_config
from tests.support.paths import TEST_DATA
from tests.support.shapes import read_ir

PROBE = TEST_DATA / "device" / "probes" / "qfx5120-25.2R2-S1.5" / "2026-10-16.json"
RECORD: dict[str, Any] = json.loads(PROBE.read_text(encoding="utf-8"))

_LINES = [entry for entry in RECORD["lines"] if "out_of_scope" not in entry]
_OUT_OF_SCOPE = [entry for entry in RECORD["lines"] if "out_of_scope" in entry]
_READERS = {"json": Format.JSON, "xml": Format.XML}
#: Lines the device took that junoscfg's grammar still refuses, each with the
#: backlog entry that owns it (found by this probe; docs/BACKLOG.md).
_FOLLOW_UPS = {
    "set interfaces ge-0/0/1 hold-time up 0 down 0": (
        "SET-COMPACT-LEAVES-001: the grammar takes one hold-time leaf a line"
    ),
    **{
        f"set policy-options policy-statement JUNOSCFG-PROBE term {term} then community {op}"
        " JUNOSCFG-C1": (
            "SET-LITERAL-KEYWORDS-001: the grammar spells the key keyword `=` as `eq_literal`"
        )
        for term, op in (("t1", "="), ("t2", "+"), ("t3", "-"))
    },
}


def _line_case(index: int, entry: dict[str, Any]) -> Any:
    reason = _FOLLOW_UPS.get(entry["line"])
    marks = [pytest.mark.xfail(strict=True, reason=reason)] if reason else []
    return pytest.param(entry, id=f"{entry['id']}-{index}", marks=marks)


def _text(rendering: dict[str, Any]) -> str:
    text = rendering["text"]
    return json.dumps(text) if rendering["format"] == "json" else text


def _set_lines(state: Any, show: str) -> list[str] | None:
    """The lines of a probe *state* the device's `show <show>` printed: those
    whose statement path starts with the shown path."""
    if not isinstance(state, list):
        return None
    shown = f" {show} "
    return [line for line in state if f" {line.partition(' ')[2]} ".startswith(shown)]


def _printed_set(rendering: dict[str, Any]) -> list[str] | None:
    """The device's display set for the same state and `show` as *rendering*,
    or the state's own lines under that path where the device printed none."""
    for other in RECORD["renderings"]:
        if (
            other["format"] == "set"
            and other["state"] == rendering["state"]
            and other["show"] == rendering["show"]
        ):
            return list(other["text"])
    return _set_lines(rendering["state"], rendering["show"])


_RENDERINGS = [
    pytest.param(rendering, id=f"{rendering['id']}-{rendering['format']}-{index}")
    for index, rendering in enumerate(RECORD["renderings"])
    if rendering["format"] in _READERS and _printed_set(rendering) is not None
]


class TestEveryProbedLineValidatesAsTheDeviceTookIt:
    """`-v` takes a line the device took and refuses one it refused: `protect
    policy-options policy-statement` (D5) and `deactivate ... community 64496:2`
    (A2) validated, and `set chassis dump-on-panic` and four undocumented
    siblings (D4, P4) did not. `hold-time down 0` alone loads and fails only at
    `commit check` (D1), so it validates."""

    @pytest.mark.parametrize("entry", [_line_case(i, e) for i, e in enumerate(_LINES)])
    def test_the_line(self, entry: dict[str, Any]) -> None:
        result = validate_config(entry["line"], format=Format.SET)
        assert result.valid is entry["accepted"], [e.message for e in result.errors]
        if not entry["accepted"]:
            assert [e.message for e in result.errors] == [f"Invalid syntax: {entry['line']}"]

    def test_the_lines_out_of_scope_still_disagree(self) -> None:
        """Bracket lists and a platform-unsupported speed are out of scope; were
        junoscfg to agree with the device there, the record would be stale."""
        assert _OUT_OF_SCOPE
        for entry in _OUT_OF_SCOPE:
            assert validate_config(entry["line"], format=Format.SET).valid is not entry["accepted"]

    def test_the_record_holds_lines_of_both_verdicts(self) -> None:
        assert {entry["accepted"] for entry in _LINES} == {True, False}
        assert set(_FOLLOW_UPS) <= {entry["line"] for entry in _LINES}


class TestEveryProbedRenderingReadsAsItsSet:
    """Each JSON and XML rendering the device printed reads, with field
    validation, to the statements of its display set, and validates: the
    undocumented `clear-text address`, `dump-on-panic` and `debugger-on-*`
    inside `<undocumented>` (D4, P4), the element names `system-name`,
    `ethernet-1g` and `*-literal` (D2), and a leaf's own tags as
    `"@description": {"inactive": true, "protect": true}` (C3)."""

    @pytest.mark.parametrize("rendering", _RENDERINGS)
    def test_the_rendering(self, rendering: dict[str, Any]) -> None:
        reader = _READERS[rendering["format"]]
        result = convert_config_result(_text(rendering), from_format=reader, to_format=Format.SET)
        assert [d.message for d in result.diagnostics if d.source == "field-validate"] == []
        printed = "\n".join(_printed_set(rendering) or []) + "\n"
        assert read_ir(result.output, Format.SET) == read_ir(printed, Format.SET)
        if reader is Format.JSON:
            assert validate_config(_text(rendering), format=Format.JSON).valid

    def test_the_renderings_cover_every_question_with_one(self) -> None:
        assert {r.values[0]["id"] for r in _RENDERINGS} >= {"C3", "A2", "D2", "D4", "P4"}


class TestJunoscfgWritesTheDevicesJsonNames:
    """The device loaded junoscfg's JSON for the renamed statements and printed
    the same names (D2): junoscfg's JSON of the statements it loaded is the
    device's JSON object, and the keyword JSON (`"802.3ad"`, `"to"`) the device
    loads reads as the element JSON, whose set output is the device's (D3)."""

    _PATHS = {
        "snmp name": "snmp.name",
        "interfaces interface-range JUNOSCFG-D2": "interfaces.interface-range",
        "policy-options policy-statement JUNOSCFG-PROBE": "policy-options.policy-statement",
    }

    def test_the_json_object(self) -> None:
        loaded = next(
            load for load in RECORD["loads"] if load["command"].endswith("d2-junoscfg.json")
        )
        source = json.dumps(loaded["source"])
        compared = 0
        for rendering in RECORD["renderings"]:
            if rendering["format"] != "json" or rendering["state"] != loaded["command"]:
                continue
            written = convert_config(
                source,
                from_format=Format.JSON,
                to_format=Format.JSON,
                path=self._PATHS[rendering["show"]],
            )
            assert json.loads(written) == rendering["text"], rendering["show"]
            compared += 1
        assert compared == len(self._PATHS)

    def test_the_keyword_json_reads_as_the_element_json(self) -> None:
        keyword, element = (
            json.dumps(load["source"]) for load in RECORD["loads"] if load["id"] == "D3"
        )
        printed = next(
            r["text"] for r in RECORD["renderings"] if r["id"] == "D3" and r["format"] == "set"
        )
        assert read_ir(keyword, Format.JSON) == read_ir(element, Format.JSON)
        written = convert_config(keyword, from_format=Format.JSON, to_format=Format.SET)
        assert written.splitlines() == printed
        assert validate_config(keyword, format=Format.JSON).valid


class TestASelectionLoadsAsTheDevicePrintsIt:
    """With `routing-options static` deactivated, the device prints the route
    with `deactivate routing-options static` (C3): junoscfg's absolute
    selection of the routes keeps the ancestor's tag and reads as the same
    configuration as the device's display set (equivalent, not identical: it
    writes no bare `set routing-options static`)."""

    def test_the_selection(self) -> None:
        shown = [
            r
            for r in RECORD["renderings"]
            if r["format"] == "set"
            and r["show"] == "routing-options static route 198.51.100.0/24"
            and "deactivate routing-options static" in r["state"]
        ]
        assert len(shown) == 1
        state = "\n".join(shown[0]["state"]) + "\n"
        written = convert_config(
            state, from_format=Format.SET, to_format=Format.SET, path="routing-options.static.route"
        )
        printed = "\n".join(shown[0]["text"]) + "\n"
        assert read_ir(written, Format.SET) == read_ir(printed, Format.SET)


class TestTheProbeRecordIsSanitized:
    """The record holds the probe's own statements, the device's responses and
    renderings, and nothing that names the device, its user or the time: no
    CLI prompt, banner or `junos:changed-*` attribute."""

    _PROMPT = re.compile(r"[\w.-]+@[\w.-]+[>#%]")

    def test_no_prompt_or_timestamp(self) -> None:
        text = PROBE.read_text(encoding="utf-8")
        assert RECORD["lines"] and RECORD["renderings"]
        assert "junos:changed" not in text
        assert "{master" not in text and "rpc-reply" not in text
        assert not self._PROMPT.search(text)
        assert set(RECORD["device"]) == {"family", "release", "date", "mode"}
