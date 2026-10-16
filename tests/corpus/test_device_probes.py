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

import gzip
import json
import re
from typing import TYPE_CHECKING, Any

import pytest

from junoscfg import Format, convert_config, convert_config_result, validate_config
from tests.support.paths import PRIVATE_DATA, TEST_DATA
from tests.support.shapes import read_ir

if TYPE_CHECKING:
    from pathlib import Path

PROBES = TEST_DATA / "device" / "probes"
PROBE = PROBES / "qfx5120-25.2R2-S1.5" / "2026-10-16.json"
RECORD: dict[str, Any] = json.loads(PROBE.read_text(encoding="utf-8"))
_RECORDS = sorted(PROBES.glob("**/*.json"))
#: The owner's raw session of this probe, never committed (private_test_data/).
_RAW_SESSION = PRIVATE_DATA / "device-probe-2026-10-16" / "paste.out"

_LINES = [entry for entry in RECORD["lines"] if "out_of_scope" not in entry]
_OUT_OF_SCOPE = [entry for entry in RECORD["lines"] if "out_of_scope" in entry]
_READERS = {"json": Format.JSON, "xml": Format.XML}


def _values(record: dict[str, Any]) -> list[str]:
    """Every value a probe record holds: of each set line, as the set reader
    reads it (a bracket list one value a line), of each JSON rendering and
    loaded file, and the text of each XML element."""
    lines = [entry["line"] for entry in (*record["lines"], *record.get("edit_level", ()))]
    objects: list[Any] = [load["source"] for load in record.get("loads", ()) if "source" in load]
    for rendering in record["renderings"]:
        if isinstance(rendering["state"], list):
            lines.extend(rendering["state"])
        if rendering["format"] == "set":
            lines.extend(rendering["text"])
        elif rendering["format"] == "json":
            objects.append(rendering["text"])
    values: list[str] = []
    for line in lines:
        if not line.startswith("set "):
            continue  # a verb line names statements a set line holds
        head, _, listed = line.partition(" [ ")
        for one in [f"{head} {v}" for v in listed.rstrip(" ]").split()] if listed else [line]:
            set_json = convert_config(
                one, from_format=Format.SET, to_format=Format.JSON, validate=False
            )
            objects.append(json.loads(set_json))

    def walk(node: Any) -> None:
        if isinstance(node, dict):
            for key, value in node.items():
                if not key.startswith("@"):  # an annotation holds tags, not values
                    walk(value)
        elif isinstance(node, list):
            for value in node:
                walk(value)
        elif isinstance(node, str) or (isinstance(node, int) and not isinstance(node, bool)):
            values.append(str(node))

    walk(objects)
    for rendering in record["renderings"]:
        if rendering["format"] == "xml":
            values.extend(re.findall(r">([^<>\s][^<>]*)<", rendering["text"]))
    return values


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
    (A2) validated, and `set chassis dump-on-panic`, four undocumented
    siblings (D4, P4), `then community = | + | - JUNOSCFG-C1` (D2;
    SET-LITERAL-KEYWORDS-001) and `hold-time up 0 down 0` on one line (D1;
    SET-COMPACT-LEAVES-001) did not. `hold-time down 0` alone loads and fails
    only at `commit check` (D1), so it validates."""

    @pytest.mark.parametrize(
        "entry", [pytest.param(e, id=f"{e['id']}-{i}") for i, e in enumerate(_LINES)]
    )
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

    @pytest.mark.parametrize(
        "entry",
        [pytest.param(e, id=f"{e['id']}-{i}") for i, e in enumerate(_LINES) if "commit_check" in e],
    )
    def test_a_statement_commit_check_misses_is_a_field_warning(
        self, entry: dict[str, Any]
    ) -> None:
        """Where `commit check` names a missing mandatory statement, field
        validation warns about that statement, and only then (D1)."""
        missing = re.findall(r"Missing mandatory statement: '([^']+)'", entry["commit_check"])
        result = convert_config_result(entry["line"], from_format=Format.SET, to_format=Format.SET)
        warned = re.findall(
            r"Missing mandatory field '([^']+)'",
            " ".join(d.message for d in result.diagnostics if d.source == "field-validate"),
        )
        assert warned == missing

    def test_the_record_holds_lines_of_both_verdicts(self) -> None:
        assert {entry["accepted"] for entry in _LINES} == {True, False}


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
        written = convert_config_result(keyword, from_format=Format.JSON, to_format=Format.SET)
        assert written.output.splitlines() == printed
        # A permanent alias, not a deprecated one: no note, no warning (ruling 1).
        assert written.diagnostics == ()
        result = validate_config(keyword, format=Format.JSON)
        assert result.valid and not result.warnings


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
    """Every probe record holds the probe's own statements, the device's
    responses and renderings, and nothing that names the device, its user or
    the time (DG-i; docs/how-to/settle-a-schema-question.md, rule 5): no CLI
    prompt, banner, commit or change attribute, time of day or home path, and
    every value is one of the synthetic values of AGENTS.md, so a host name the
    test cannot know is caught too. Test/Challenge M1."""

    _LEAKS = {
        "a CLI prompt": re.compile(r"[\w.-]+@[\w.-]+(:[\w.-]+)?[>#%]"),
        "a change or commit attribute": re.compile(r"junos:(changed|commit)"),
        "a commit banner": re.compile(r"## Last (commit|changed)"),
        "a CLI banner": re.compile(r"\{(master|primary|backup|linecard)[:}]"),
        "an XML reply": re.compile(r"rpc-reply|<cli>"),
        "a time of day": re.compile(r"\b\d{2}:\d{2}:\d{2}\b"),
        "a home path": re.compile(r"/var/home/|/home/"),
        "a host-name statement": re.compile(r"\bhost-name\b"),
    }
    _VALUE = re.compile(
        r"JUNOSCFG-[A-Z0-9-]+|198\.51\.100\.\d+(/\d+)?|203\.0\.114\.\d+|127\.0\.0\.1"
        r"|(6449[6-9]|6450\d|6451[01])(:\d+)?|(ge|xe|et)-\d+/\d+/\d+|ae\d+|lo0|t\d+|\d+g?"
        r"|admin|operator|router1|sw1"
    )

    @pytest.mark.parametrize(
        "record", [pytest.param(p, id=p.parent.name + "/" + p.name) for p in _RECORDS]
    )
    def test_no_prompt_or_timestamp(self, record: Path) -> None:
        text = record.read_text(encoding="utf-8")
        loaded = json.loads(text)
        assert loaded["lines"] and loaded["renderings"]
        assert set(loaded["device"]) == {"family", "release", "date", "mode"}
        found = [what for what, shape in self._LEAKS.items() if shape.search(text)]
        assert not found

    @pytest.mark.parametrize(
        "record", [pytest.param(p, id=p.parent.name + "/" + p.name) for p in _RECORDS]
    )
    def test_every_value_is_synthetic(self, record: Path) -> None:
        values = _values(json.loads(record.read_text(encoding="utf-8")))
        assert values
        assert sorted(v for v in values if not self._VALUE.fullmatch(v)) == []

    def test_the_leak_shapes_catch_what_they_name(self) -> None:
        """Each shape refuses a synthetic sample of what it names."""
        samples = {
            "a CLI prompt": "operator@router1:fpc0% ",
            "a change or commit attribute": 'junos:commit-user="operator"',
            "a commit banner": "## Last commit: 2026-01-01 by operator",
            "a CLI banner": "{primary:0}[edit]",
            "an XML reply": "<rpc-reply>",
            "a time of day": "12:00:00",
            "a home path": "/var/home/operator/d2.set",
            "a host-name statement": "set system host-name router1",
        }
        assert set(samples) == set(self._LEAKS)
        for what, sample in samples.items():
            assert self._LEAKS[what].search(sample), what
        assert not self._VALUE.fullmatch("router2")

    def test_the_raw_session_names_nothing_in_the_repository(self) -> None:
        """Where the owner's raw session is on this machine, neither name of its
        prompt occurs under `tests/data/`. The names are read locally and never
        written anywhere."""
        if not _RAW_SESSION.is_file():
            pytest.skip("the raw probe session is not on this machine")
        prompt = re.search(r"([\w.-]+)@([\w.-]+)[>#]", _RAW_SESSION.read_text(encoding="utf-8"))
        assert prompt
        names = [re.compile(rf"\b{re.escape(name)}\b") for name in prompt.groups()]
        scanned = 0
        for path in sorted(TEST_DATA.rglob("*")):
            if not path.is_file():
                continue
            raw = path.read_bytes()
            text = (gzip.decompress(raw) if path.suffix == ".gz" else raw).decode(
                "utf-8", "replace"
            )
            scanned += 1
            assert not any(name.search(text) for name in names), path.relative_to(TEST_DATA)
        assert scanned
