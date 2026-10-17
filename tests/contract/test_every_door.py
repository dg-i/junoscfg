"""Every validation door gives a configuration the same verdict.

A configuration reaches validation through many doors: the public functions
`validate_set`, `validate_json`, `validate_yaml`, `validate_structured` and
`validate_config`, the `JunosValidator` facade and the `SetValidator` behind
it (the session fixtures), and the CLI's `-v -i <format>`; yaml-new reaches
the JSON schema through `validate_config`, the facade and the CLI. Each row of the
catalogues below is one configuration, written in every format it can be
written in, with the verdict the device gave; every door that takes one of
those formats must give that verdict. A door that cannot express a row (a
set-only line has no JSON door) is left out when the cases are built, not
skipped when they run.

All of it runs on the shipped artifacts. XML has no door here: the package
ships no XSD, and `validate_xml` says so (`TestValidateXmlNeedsACleanedXsd`
in `tests/unit/validate/test_validator.py`).

Synthetic values only, as AGENTS.md names them. The keyed-entry lines are the
ones a vMX on 23.2R2-S7.5 accepted and rejected, with the probe's synthetic
names (`tests/data/captures/keyed-entries-*`).
"""

from __future__ import annotations

import json
import warnings
from dataclasses import dataclass, field
from types import SimpleNamespace
from typing import TYPE_CHECKING, Any

import pytest
import yaml
from click.testing import CliRunner

from junoscfg import (
    Format,
    validate_config,
    validate_json,
    validate_set,
    validate_structured,
    validate_yaml,
)
from junoscfg.cli import main

if TYPE_CHECKING:
    from collections.abc import Callable


@dataclass(frozen=True)
class Verdict:
    """What a door said: valid or not, every message it gave, and its warnings."""

    valid: bool
    report: str
    warnings: str = ""


@dataclass(frozen=True)
class Row:
    """One configuration, in each format it is written in, and its verdict.

    `document` is the configuration as JSON and YAML carry it, under
    `configuration`. `messages` must each appear in what a door reports.
    """

    id: str
    valid: bool
    set: str | None = None
    document: dict[str, Any] | None = None
    structured: str | None = None
    messages: tuple[str, ...] = ()
    # Each must appear in the warnings of every door that takes the row.
    warnings: tuple[str, ...] = ()
    xfail: str | None = None
    # The doors the xfail holds for; empty, every door.
    xfail_on: tuple[str, ...] = ()

    def text(self, fmt: str) -> str | None:
        if fmt == "set":
            return self.set
        if fmt == "structured":
            return self.structured
        if self.document is None:
            return None
        wrapped = {"configuration": self.document}
        return json.dumps(wrapped) if fmt == "json" else yaml.safe_dump(wrapped)


@dataclass(frozen=True)
class Door:
    name: str
    fmt: str
    call: Callable[[str, Any], Verdict] = field(repr=False)


def _result(result: Any) -> Verdict:
    return Verdict(
        result.valid,
        "\n".join(error.message for error in result.errors),
        "\n".join(warning.message for warning in result.warnings),
    )


def _deprecated(call: Callable[[], Any]) -> Any:
    """A deprecated door's verdict, its `DeprecationWarning` held back.

    The warning is the door's unit test's to assert
    (`tests/unit/validate/test_structured_validator.py`); here only the verdict counts.
    """
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        return call()


def _cli(fmt: str) -> Callable[[str, Any], Verdict]:
    def call(text: str, _validators: Any) -> Verdict:
        result = CliRunner().invoke(main, ["-v", "-i", fmt], input=text)
        # 0 is valid and 1 invalid; anything else (3: the artifacts did not
        # load, or a traceback) is neither, and fails the case.
        assert result.exit_code in (0, 1), result.output
        return Verdict(result.exit_code == 0, result.output, result.output)

    return call


DOORS = (
    Door("SetValidator", "set", lambda t, v: _result(v.set_validator.validate(t))),
    Door("JunosValidator.validate_set", "set", lambda t, v: _result(v.facade.validate_set(t))),
    Door("validate_set", "set", lambda t, _: _result(validate_set(t))),
    Door("validate_config-set", "set", lambda t, _: _result(validate_config(t, format=Format.SET))),
    Door("cli-set", "set", _cli("set")),
    Door("JunosValidator.validate_json", "json", lambda t, v: _result(v.facade.validate_json(t))),
    Door("validate_json", "json", lambda t, _: _result(validate_json(t))),
    Door(
        "validate_config-json", "json", lambda t, _: _result(validate_config(t, format=Format.JSON))
    ),
    Door("cli-json", "json", _cli("json")),
    Door("JunosValidator.validate_yaml", "yaml", lambda t, v: _result(v.facade.validate_yaml(t))),
    Door("validate_yaml", "yaml", lambda t, _: _result(validate_yaml(t))),
    Door(
        "validate_config-yaml", "yaml", lambda t, _: _result(validate_config(t, format=Format.YAML))
    ),
    Door("cli-yaml", "yaml", _cli("yaml")),
    Door(
        "JunosValidator.validate_yaml_as_json",
        "yaml-new",
        lambda t, v: _result(v.facade.validate_yaml_as_json(t)),
    ),
    Door(
        "validate_config-yaml-new",
        "yaml-new",
        lambda t, _: _result(validate_config(t, format=Format.YAML_NEW)),
    ),
    Door("cli-yaml-new", "yaml-new", _cli("yaml-new")),
    Door(
        "JunosValidator.validate_structured",
        "structured",
        lambda t, v: _result(_deprecated(lambda: v.facade.validate_structured(t))),
    ),
    Door("validate_structured", "structured", lambda t, _: _result(validate_structured(t))),
    Door(
        "validate_config-structured",
        "structured",
        lambda t, _: _result(validate_config(t, format=Format.STRUCTURED)),
    ),
    Door("cli-structured", "structured", _cli("structured")),
)


def cases(rows: tuple[Row, ...]) -> list[Any]:
    """Each row through each door that takes one of its formats."""
    found = []
    for row in rows:
        for door in DOORS:
            if row.text(door.fmt) is None:
                continue
            # A door named in `xfail_on` fails on the verdict, never by crashing
            # (Test/Challenge F5).
            assert set(row.xfail_on) <= {d.name for d in DOORS}, row.xfail_on
            assert row.xfail or not row.xfail_on, f"{row.id}: xfail_on without xfail"
            failing = row.xfail and (not row.xfail_on or door.name in row.xfail_on)
            raises = AssertionError if row.xfail_on else None
            marks = (
                [pytest.mark.xfail(strict=True, raises=raises, reason=row.xfail)] if failing else []
            )
            found.append(pytest.param(row, door, id=f"{row.id}-{door.name}", marks=marks))
    return found


@pytest.fixture
def validators(bundled_set_validator: Any, bundled_validator: Any) -> Any:
    """The session's shipped `SetValidator` and `JunosValidator`, compiled once."""
    return SimpleNamespace(set_validator=bundled_set_validator, facade=bundled_validator)


def _check(row: Row, door: Door, validators: Any) -> None:
    text = row.text(door.fmt)
    assert text is not None
    verdict = door.call(text, validators)
    assert verdict.valid is row.valid, verdict.report
    for message in row.messages:
        assert message in verdict.report, verdict.report
    for warning in row.warnings:
        assert warning in verdict.warnings, verdict.warnings


# ── A keyed entry takes exactly its key values ───────────────────────

POLICY = "set policy-options policy-statement SAMPLE-POLICY"
FROM = f"{POLICY} term T1 from"
THEN = f"{POLICY} term T1 then"
EVENT = "set event-options policy SAMPLE-EVENT-POLICY attributes-match"
VIRTUAL_LINK = "set protocols ospf area 0.0.0.0 virtual-link"


def _term(where: str, slot: str, entry: dict[str, Any]) -> dict[str, Any]:
    """`policy-options` with term T1 of SAMPLE-POLICY holding one *slot* entry."""
    statement = {"name": "SAMPLE-POLICY", "term": [{"name": "T1", where: {slot: [entry]}}]}
    return {"policy-options": {"policy-statement": [statement]}}


def _policy_from(slot: str, entry: dict[str, Any]) -> dict[str, Any]:
    """`policy-options` with SAMPLE-POLICY's own `from` holding one *slot* entry."""
    statement = {"name": "SAMPLE-POLICY", "from": {slot: [entry]}}
    return {"policy-options": {"policy-statement": [statement]}}


def _structured_term(statement: str) -> str:
    return (
        "policy-options {\n    policy-statement SAMPLE-POLICY {\n        term T1 {\n"
        f"            {statement};\n        }}\n    }}\n}}\n"
    )


_ACCEPTED_PROBE = (
    f"{FROM} as-path-neighbors as-list SAMPLE-AS-LIST",
    f"{POLICY} from as-path-neighbors as-list SAMPLE-AS-LIST",
    f"{FROM} as-path-origins as-list-group SAMPLE-AS-LIST-GROUP",
    f"{FROM} as-path-transits as-list SAMPLE-AS-LIST-2",
    f"{FROM} as-path-neighbors as-list-group SAMPLE-AS-LIST",
    f"{FROM} route-filter 198.51.100.0/24 exact accept",
    f"{FROM} route-filter 198.51.100.0/24 orlonger",
    f"{FROM} source-address-filter 198.51.100.0/24 exact accept",
    f"{THEN} community add SAMPLE-COMM",
    f"{THEN} community delete SAMPLE-COMM",
    f"{THEN} community set SAMPLE-COMM",
    f"{THEN} community SAMPLE-COMM add",
    f'{EVENT} snmp_trap_link_down.interface-name matches "^xe-"',
    f'{EVENT} ping.test-owner matches "^uptime$"',
    "set groups SAMPLE-GROUP policy-options policy-statement <*> term T1 from "
    "as-path-neighbors as-list SAMPLE-AS-LIST",
    "set logical-systems SAMPLE-LS policy-options policy-statement SAMPLE-POLICY term T1 "
    "from as-path-neighbors as-list SAMPLE-AS-LIST",
)

KEYED_ENTRIES = (
    # The device probe's accepted lines (round 1). Where the device's
    # `| display json` shape is known, the row carries it, and the structured
    # form its `show` gives.
    Row(
        "as-path-neighbors-by-list",
        True,
        set=_ACCEPTED_PROBE[0],
        document=_term(
            "from", "as-path-neighbors", {"list-type": "as-list", "list-name": "SAMPLE-AS-LIST"}
        ),
        structured=_structured_term("from as-path-neighbors as-list SAMPLE-AS-LIST"),
    ),
    Row("policy-level-as-path-neighbors", True, set=_ACCEPTED_PROBE[1]),
    Row("as-path-origins-by-group", True, set=_ACCEPTED_PROBE[2]),
    Row("as-path-transits-by-list", True, set=_ACCEPTED_PROBE[3]),
    Row("as-path-neighbors-by-group", True, set=_ACCEPTED_PROBE[4]),
    Row(
        "route-filter-exact-accept",
        True,
        set=_ACCEPTED_PROBE[5],
        document=_term(
            "from",
            "route-filter",
            {"address": "198.51.100.0/24", "exact": [None], "accept": [None]},
        ),
        structured=_structured_term("from route-filter 198.51.100.0/24 exact accept"),
    ),
    Row("route-filter-orlonger", True, set=_ACCEPTED_PROBE[6]),
    Row(
        "source-address-filter-exact-accept",
        True,
        set=_ACCEPTED_PROBE[7],
        document=_term(
            "from",
            "source-address-filter",
            {"address": "198.51.100.0/24", "exact": [None], "accept": [None]},
        ),
        structured=_structured_term("from source-address-filter 198.51.100.0/24 exact accept"),
    ),
    Row(
        "community-add",
        True,
        set=_ACCEPTED_PROBE[8],
        document=_term("then", "community", {"add": [None], "community-name": "SAMPLE-COMM"}),
        structured=_structured_term("then community add SAMPLE-COMM"),
    ),
    Row("community-delete", True, set=_ACCEPTED_PROBE[9]),
    Row("community-set", True, set=_ACCEPTED_PROBE[10]),
    Row("community-key-choice-after-the-name", True, set=_ACCEPTED_PROBE[11]),
    Row("attributes-match-interface-name", True, set=_ACCEPTED_PROBE[12]),
    Row("attributes-match-test-owner", True, set=_ACCEPTED_PROBE[13]),
    Row("in-groups", True, set=_ACCEPTED_PROBE[14]),
    Row("in-logical-systems", True, set=_ACCEPTED_PROBE[15]),
    Row("the-probes-accepted-lines-together", True, set="\n".join(_ACCEPTED_PROBE)),
    Row(
        "as-path-origins-by-group-asg",
        True,
        set=f"{FROM} as-path-origins as-list-group SAMPLE-ASG",
        document=_term(
            "from", "as-path-origins", {"list-type": "as-list-group", "list-name": "SAMPLE-ASG"}
        ),
        structured=_structured_term("from as-path-origins as-list-group SAMPLE-ASG"),
    ),
    Row(
        "policy-level-as-path-origins",
        True,
        set=f"{POLICY} from as-path-origins as-list-group SAMPLE-ASG",
        document=_policy_from(
            "as-path-origins", {"list-type": "as-list-group", "list-name": "SAMPLE-ASG"}
        ),
    ),
    # The device probe's rejected lines (round 1).
    Row(
        "as-path-neighbors-without-its-name",
        False,
        set=f"{FROM} as-path-neighbors as-list",
        document=_term("from", "as-path-neighbors", {"name": "as-list"}),
    ),
    Row(
        "as-path-neighbors-without-its-type", False, set=f"{FROM} as-path-neighbors SAMPLE-AS-LIST"
    ),
    Row(
        "as-path-neighbors-with-a-further-value",
        False,
        set=f"{FROM} as-path-neighbors as-list SAMPLE-AS-LIST SAMPLE-EXTRA",
        structured=_structured_term("from as-path-neighbors as-list SAMPLE-AS-LIST SAMPLE-EXTRA"),
    ),
    Row(
        "route-filter-with-an-action-for-a-key",
        False,
        set=f"{FROM} route-filter 198.51.100.0/24 next-policy",
    ),
    Row(
        "route-filter-with-a-further-value",
        False,
        set=f"{FROM} route-filter 198.51.100.0/24 exact SAMPLE-EXTRA",
    ),
    Row(
        "attributes-match-with-a-further-value",
        False,
        set=f'{EVENT} snmp_trap_link_down.interface-name matches "^xe-" SAMPLE-EXTRA',
    ),
    Row(
        "apply-groups-takes-one-group-per-line",
        False,
        set="set apply-groups SAMPLE-GROUP SAMPLE-GROUP-2",
    ),
    Row(
        "a-numeric-list-type",
        False,
        set=f"{FROM} as-path-neighbors 1 SAMPLE-AS-LIST",
        # A key value takes its own leaf's type: `list-type` is `as-list` or
        # `as-list-group`. The XSD's union also names `xsd:unsignedLong`, but
        # the device rejected this at `set` with "syntax error, expecting
        # <flag-value> or <attribute-value>." (round-1 probe). Owner answer 8.
    ),
    Row(
        "the-bare-keyed-list-keyword",
        False,
        set=f"{FROM} as-path-neighbors",
        # Pre-existing on 0.14.0, about 380 keyword pairs; owner decision: a
        # separate change.
        xfail="follow-up change 'grammar keyword boundaries': a keyword terminal ends inside "
        "a word, so `as` takes `-path-neighbors` as its value",
    ),
    # Key fields given by keyword in either order, and `apply-macro` with one
    # to three values (device probe round 5).
    Row(
        "virtual-link-keys-in-order",
        True,
        set=f"{VIRTUAL_LINK} neighbor-id 10.255.255.1 transit-area 0.0.0.2",
    ),
    Row(
        "virtual-link-keys-reversed",
        True,
        set=f"{VIRTUAL_LINK} transit-area 0.0.0.3 neighbor-id 10.255.255.2",
    ),
    Row("apply-macro-one-value", True, set="set apply-macro ABCDE"),
    Row("apply-macro-two-values", True, set="set apply-macro ABCDE DEFGH"),
    Row("apply-macro-quoted-value", True, set='set apply-macro 12345 "KADJBF KU!H"'),
    Row(
        "apply-macro-three-values",
        True,
        set='set groups SAMPLE-GROUP apply-macro 12345 "KADJBF KU!H" balks',
    ),
    Row("location-building", True, set="set system location building SAMPLE-BUILDING"),
    Row("virtual-link-one-key", False, set=f"{VIRTUAL_LINK} neighbor-id 10.255.255.3"),
    Row("virtual-link-keys-without-keywords", False, set=f"{VIRTUAL_LINK} 10.255.255.4 0.0.0.2"),
    Row(
        "apply-macro-four-values",
        False,
        set='set groups SAMPLE-GROUP apply-macro 12345 "KADJBF KU!H" balks XXXXX',
    ),
    Row(
        "apply-macro-unquoted-four-values",
        False,
        set="set groups SAMPLE-GROUP apply-macro 12345 XXX XXXX XXX",
    ),
    Row("location-bare-value", False, set="set system location dc-a"),
    # The document shapes: the keys by their names, never `name`.
    Row(
        "as-path-neighbors-name-beside-the-type",
        False,
        document=_term(
            "from", "as-path-neighbors", {"name": "SAMPLE-AS-LIST", "list-type": "as-list"}
        ),
    ),
    Row(
        "source-address-filter-keyed-by-name",
        False,
        document=_term(
            "from", "source-address-filter", {"name": "198.51.100.0/24", "exact": [None]}
        ),
    ),
    Row(
        "route-filter-keyed-by-name",
        False,
        document=_term("from", "route-filter", {"name": "198.51.100.0/24", "exact": [None]}),
    ),
    Row(
        "policy-level-as-path-origins-keyed-by-name",
        False,
        document=_policy_from("as-path-origins", {"name": "as-list-group"}),
    ),
)


class TestAKeyedEntryTakesExactlyItsKeys:
    """Spec: validation/keyed-entries and validation/set-command-validation.

    Lists keyed by something other than `name` (an AS-list reference, a route
    filter, a community action, an event attribute match) take their key
    values and nothing else, in every format; the JSON and YAML schemas name
    the key fields, never `name`.
    """

    @pytest.mark.parametrize(("row", "door"), cases(KEYED_ENTRIES))
    def test_every_door_agrees(self, row: Row, door: Door, validators: Any) -> None:
        _check(row, door, validators)


# ── Several keyworded siblings on one line ───────────────────────────

SIBLINGS = (
    Row(
        "ntp-server-compact",
        True,
        set="set system ntp server 198.51.100.1 version 4 prefer routing-instance mgmt_junos",
    ),
    Row(
        "maximum-prefixes-compact",
        True,
        set="set routing-options maximum-prefixes 3000000 threshold 50 log-interval 5",
    ),
    Row(
        "ntp-server-expanded",
        True,
        set="set system ntp server 198.51.100.1 version 4\n"
        "set system ntp server 198.51.100.1 prefer\n"
        "set system ntp server 198.51.100.1 routing-instance mgmt_junos",
    ),
    Row(
        "maximum-prefixes-expanded",
        True,
        set="set routing-options maximum-prefixes 3000000\n"
        "set routing-options maximum-prefixes threshold 50\n"
        "set routing-options maximum-prefixes log-interval 5",
    ),
    Row(
        "traceoptions-file-compact",
        True,
        set="set protocols bgp traceoptions file bgp-log size 10m files 10",
    ),
    Row(
        "traceoptions-file-expanded",
        True,
        set="set protocols bgp traceoptions file bgp-log\n"
        "set protocols bgp traceoptions file size 10m\n"
        "set protocols bgp traceoptions file files 10",
    ),
    Row(
        "ntp-server-unknown-sibling", False, set="set system ntp server 198.51.100.1 bogus-option 5"
    ),
    Row(
        "maximum-prefixes-unknown-sibling",
        False,
        set="set routing-options maximum-prefixes 3000000 bogus-option 5",
    ),
    Row("traceoptions-file-unknown-sibling", False, set="set snmp traceoptions file rogue size 1"),
)


class TestSiblingsShareOneLine:
    """Spec: validation/set-command-validation, "Equivalent compact sibling forms
    validate" and "Sibling support remains structurally narrow".

    Junos writes several keyworded settings of one entry on one line; the
    compact and the expanded forms validate alike, and an unknown sibling is
    still rejected.
    """

    @pytest.mark.parametrize(("row", "door"), cases(SIBLINGS))
    def test_every_door_agrees(self, row: Row, door: Door, validators: Any) -> None:
        _check(row, door, validators)


# ── Bracket shorthand in raw set input ───────────────────────────────


def _bracket(line: str, lineno: int = 1) -> str:
    return f"Unsupported bracket syntax in set input on line {lineno}:\n{line}"


def _bracket_row(command: str) -> Row:
    line = f"{command} system apply-groups [ foo bar ]"
    return Row(f"{command}-with-brackets", False, set=line, messages=(_bracket(line),))


_COLLECTED = (
    "# ignored bracket [",
    "set system apply-groups [ foo bar ]",
    "set system host-name router1",
    "delete system apply-groups ]",
)

BRACKETS = (
    *(
        _bracket_row(command)
        for command in ("set", "delete", "deactivate", "activate", "protect", "replace")
    ),
    Row(
        "after-an-inline-comment",
        False,
        set="/* ignored */ set system apply-groups [ foo bar ]",
        messages=(_bracket("/* ignored */ set system apply-groups [ foo bar ]"),),
    ),
    Row(
        "each-offending-line",
        False,
        set="\n".join(_COLLECTED),
        messages=(_bracket(_COLLECTED[1], 2), _bracket(_COLLECTED[3], 4)),
    ),
    Row(
        "in-a-comment-and-in-quotes",
        True,
        set='# ignored bracket [\nset policy-options community FOO members "64498:[2-6]....$"',
    ),
    Row(
        "in-a-block-comment",
        True,
        set="/* ignored\n[ still ignored ]\n*/\nset system host-name router1",
    ),
)


class TestBracketShorthandIsRejected:
    """Spec: validation/raw-set-input.

    `[ a b ]` is device-valid interactive shorthand that raw junoscfg set input
    deliberately excludes. Every door reports each offending line, by number,
    with the line itself; a bracket in a comment or a quoted value is none.
    The CLI exits 1 with the complete diagnostic.
    """

    @pytest.mark.parametrize(("row", "door"), cases(BRACKETS))
    def test_every_door_agrees(self, row: Row, door: Door, validators: Any) -> None:
        _check(row, door, validators)


# ── Every verb names a statement path ─────────────────────────────────

VERBS = (
    Row(
        "protect-a-group",
        True,
        set="set groups GR-PROTECTED system host-name router1\nprotect groups GR-PROTECTED",
        structured="protect: groups {\n    GR-PROTECTED {\n        system {\n"
        "            host-name router1;\n        }\n    }\n}\n",
    ),
    Row(
        "deactivate-a-leaf-without-its-value",
        True,
        set="set system host-name router1\ndeactivate system host-name",
    ),
    Row("delete-a-leaf", True, set="delete system host-name"),
    Row("activate-a-container", True, set="activate system services ssh"),
    Row(
        "protect-an-unknown-path",
        False,
        set="protect system no-such-statement",
        messages=("Invalid syntax: protect system no-such-statement",),
    ),
    Row(
        # Stopped inside the entry's key, before its match type: the set reader
        # cannot place it (fresh review B2; change device-validation).
        "deactivate-inside-an-entry-key",
        False,
        set="set policy-options policy-statement P term T from route-filter 10.0.0.0/8 exact\n"
        "deactivate policy-options policy-statement P term T from route-filter 10.0.0.0/8",
        messages=(
            "Invalid syntax: deactivate policy-options policy-statement P term T from "
            "route-filter 10.0.0.0/8",
        ),
    ),
    Row(
        "another-verb",
        False,
        set="show system host-name",
        messages=("Unsupported command in set input on line 1",),
    ),
    # The QFX5120 25.2R2-S1.5 refuses a verb before a list's name ("syntax error,
    # expecting <identifier>", probe D5) and on one value of a leaf-list ("syntax
    # error, expecting ';', [Enter], or '|'", probe A2); the set reader refuses a
    # leaf's value. `tests/data/device/probes/qfx5120-25.2R2-S1.5/2026-10-16.json`.
    Row(
        "protect-a-list-without-its-entry",
        False,
        set="set policy-options policy-statement JUNOSCFG-PROBE term t1 then accept\n"
        "protect policy-options policy-statement",
        structured="policy-options {\n    protect: policy-statement {\n        JUNOSCFG-PROBE {\n"
        "            term t1 {\n                then accept;\n            }\n        }\n    }\n}\n",
        messages=("Invalid syntax: protect policy-options policy-statement",),
        xfail="WHOLE-LIST-TAGS-001: curly validation reads `protect: policy-statement {` "
        "as a tag on the whole list, which the set reader now refuses",
        xfail_on=(
            "validate_structured",
            "validate_config-structured",
            "cli-structured",
        ),
    ),
    Row(
        "deactivate-one-value-of-a-leaf-list",
        False,
        set="set routing-options static route 198.51.100.0/24 community 64496:1\n"
        "set routing-options static route 198.51.100.0/24 community 64496:2\n"
        "deactivate routing-options static route 198.51.100.0/24 community 64496:2",
        messages=(
            "Invalid syntax: deactivate routing-options static route 198.51.100.0/24 "
            "community 64496:2",
        ),
    ),
    Row(
        "deactivate-a-leaf-with-its-value",
        False,
        set="set system host-name router1\ndeactivate system host-name router1",
        messages=("Invalid syntax: deactivate system host-name router1",),
    ),
    Row(
        "deactivate-a-container-holding-a-hidden-list",
        True,
        set="set interfaces ge-0/0/0 description uplink\ndeactivate interfaces",
        structured="inactive: interfaces {\n    ge-0/0/0 {\n        description uplink;\n"
        "    }\n}\n",
    ),
    Row(
        "deactivate-a-route-and-a-leaf-of-it",
        True,
        set="set routing-options static route 198.51.100.0/24 description JUNOSCFG-PROBE\n"
        "deactivate routing-options static route 198.51.100.0/24\n"
        "protect routing-options static route 198.51.100.0/24 description",
    ),
    Row(
        "deactivate-a-keyed-entry-after-its-whole-key",
        True,
        set=f"{VIRTUAL_LINK} neighbor-id 10.255.255.1 transit-area 0.0.0.2\n"
        "deactivate protocols ospf area 0.0.0.0 virtual-link neighbor-id 10.255.255.1 "
        "transit-area 0.0.0.2",
    ),
    Row(
        "deactivate-before-a-key-value",
        False,
        set=f"{VIRTUAL_LINK} neighbor-id 10.255.255.1 transit-area 0.0.0.2\n"
        "deactivate protocols ospf area 0.0.0.0 virtual-link neighbor-id 10.255.255.1 "
        "transit-area",
        messages=(
            "Invalid syntax: deactivate protocols ospf area 0.0.0.0 virtual-link "
            "neighbor-id 10.255.255.1 transit-area",
        ),
    ),
)


class TestEveryVerbNamesAStatementPath:
    """Spec: validation/set-command-validation.

    The set reader reads `set`, `deactivate`, `protect`, `activate` and
    `delete`; each names a statement path, and only `set` gives a leaf its
    value. The device prints `protect groups GR-PROTECTED` and `deactivate ...
    max-hello-size` (`tests/data/device/synthetic/*/junoscfg-oracle.set.gz`);
    every door called the first no set command (change device-validation). A
    verb line names a container, a list entry after its whole key, or a leaf
    before its value, and nothing else (change device-probe-fixes).
    """

    @pytest.mark.parametrize(("row", "door"), cases(VERBS))
    def test_every_door_agrees(self, row: Row, door: Door, validators: Any) -> None:
        _check(row, door, validators)


# ── Structured text validates as conversion reads it ─────────────────

_SCHEMA_FREE = (
    "deprecated door, removed in the next minor: JunosValidator.validate_structured "
    "validates curly through the schema-free SetConverter.to_set(), which keeps a one-line "
    "statement whole and writes a tag as a line of its own"
)
_DEPRECATED_DOOR = ("JunosValidator.validate_structured",)


def _curly_interface(statement: str) -> str:
    return f"interfaces {{\n    ge-0/0/0 {{\n        {statement};\n    }}\n}}\n"


STRUCTURED_AS_READ = (
    # vMX 23.2R2-S7.5 and QFX5120 25.2R2-S1.5 print `hold-time up 2000 down 0;`
    # on one curly line and as two display-set lines
    # (`tests/data/device/synthetic/*/junoscfg-oracle.*`).
    Row(
        "a-one-line-container-statement",
        True,
        set="set interfaces ge-0/0/0 hold-time up 2000\nset interfaces ge-0/0/0 hold-time down 0",
        document={
            "interfaces": {
                "interface": [{"name": "ge-0/0/0", "hold-time": {"up": "2000", "down": "0"}}]
            }
        },
        structured=_curly_interface("hold-time up 2000 down 0"),
        xfail=_SCHEMA_FREE,
        xfail_on=_DEPRECATED_DOOR,
    ),
    # The device's curly writes `protect: autonomous-system 64496;` (same captures).
    Row(
        "a-protected-statement",
        True,
        structured="routing-options {\n    protect: autonomous-system 64496;\n}\n",
        xfail=_SCHEMA_FREE,
        xfail_on=_DEPRECATED_DOOR,
    ),
    Row(
        "a-block-on-one-line",
        False,
        set="set system bogus-statement 1",
        structured="system { bogus-statement 1; }",
    ),
    Row(
        "a-brace-too-many",
        False,
        structured="system {\n    host-name router1;\n}\n}\n",
        messages=("closes no block",),
    ),
    # Nothing to validate but a warning: the device's own curly for a group
    # under `apply-flags omit` (same captures, group GR-OMIT).
    Row(
        "the-omitted-placeholder",
        True,
        structured="groups {\n    GR-OMIT {\n        system { /* OMITTED */ };\n    }\n}\n",
        warnings=("groups GR-OMIT system: `apply-flags omit` hides this block's content",),
    ),
    # Test/Challenge F1: split at `down`, the set grammar takes `hold-time
    # down` as `hold-time` with the value `down`; the walk read `down` without
    # its value, an unsignedInt the device requires (inferred from the
    # schema; no capture holds a value-less `down`).
    Row(
        "a-sibling-without-its-value",
        False,
        structured=_curly_interface("hold-time up 2000 down"),
    ),
    # Guards against validating the writer's output instead of the input: the
    # walk joins `a b c` into one quoted value, and the writer drops `timeout`.
    Row(
        "an-unquoted-multi-word-value",
        False,
        set="set interfaces ge-0/0/0 description a b c",
        structured=_curly_interface("description a b c"),
    ),
    Row(
        "a-keyword-leaf-the-writer-drops",
        True,
        set="set protocols isis overload timeout 300",
        structured="protocols {\n    isis {\n        overload timeout 300;\n    }\n}\n",
    ),
)


class TestStructuredTextValidatesAsConversionReadsIt:
    """Spec: validation/structured-validation.

    Curly text is checked statement by statement as the conversion walk reads
    it, in the input's own tokens. NEW-B5 and OPEN-1 (makeover run
    2026-10-11): validation read curly through the schema-free `to_set()`, so
    the device's one-line `hold-time` was rejected, a `protect:` line was
    checked as a set command, and a block on one line passed as empty.
    """

    @pytest.mark.parametrize(("row", "door"), cases(STRUCTURED_AS_READ))
    def test_every_door_agrees(self, row: Row, door: Door, validators: Any) -> None:
        _check(row, door, validators)
