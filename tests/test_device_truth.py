"""junoscfg against a device's own rendering of its configuration.

A capture pairs a subtree in structured form with the same subtree as the
device rendered it through ``| display json``. That makes the device the
oracle: no schema is involved in the judging, so a difference is junoscfg's
or the artifacts', never a release gap read into the data. It is the only
such oracle this project has, and it is what showed the 24.4R0 artifacts to
be defective: every ``hop-limit`` came back as a fused key.

A pair is ``<name>.conf`` beside ``<name>.json``; the first line of the
``.conf`` names the subtree, ``## show configuration groups g policy-options``.
The device prints a subtree's *contents* while ``| display json`` wraps back
to the root, so the fragment is re-rooted along that path before converting,
or the two are not comparable. What is compared is shape: every key path,
with a list entry told from its siblings by its ``name`` or ``address``, so a
dropped term or a ``then`` under the wrong term is a difference. Values are
the field validator's. The device's ``@`` attributes are left out, and a
failure names element paths only, never what stood in them.

Pairs under ``tests/data/captures/`` always run; the one there is synthetic,
shaped after a device's rendering, so the helpers run on every clone. Pairs
under the gitignored ``private_test_data/captures/`` are a device's own words
and run on the machine that holds them; a capture is one operator's
configuration, and it is theirs to publish or not.
"""

from __future__ import annotations

import json
import shlex
from pathlib import Path
from typing import Any

import pytest

from junoscfg import Format, convert_config
from junoscfg.convert.ir import find_configuration

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CAPTURE_DIRS = (
    PROJECT_ROOT / "tests" / "data" / "captures",
    PROJECT_ROOT / "private_test_data" / "captures",
)
HEADER = "## show configuration "
#: The keys a device writes to tell one list entry from the next.
ENTRY_KEYS = ("name", "address")


def _pairs() -> list[Path]:
    """Every ``.conf`` with a ``.json`` beside it, committed ones first."""
    return [
        conf
        for directory in CAPTURE_DIRS
        if directory.is_dir()
        for conf in sorted(directory.glob("*.conf"))
        if conf.with_suffix(".json").is_file()
    ]


def _reroot(crumbs: list[str], body: str) -> str:
    """Wrap the subtree's contents back under its path, innermost first."""
    conf = body
    for name in reversed(crumbs):
        inner = "\n".join("    " + line for line in conf.splitlines())
        word = f'"{name}"' if " " in name else name
        conf = f"{word} {{\n{inner}\n}}"
    return conf


def _paths(obj: Any, prefix: tuple[str, ...] = ()) -> set[tuple[str, ...]]:
    """Every key path in *obj*, a list entry carrying its own name.

    Siblings in a list would otherwise pool their children into one set, and
    two terms would compare equal to one.
    """
    found: set[tuple[str, ...]] = set()
    if isinstance(obj, dict):
        for key, value in obj.items():
            if key.startswith("@"):
                continue
            path = (*prefix, key)
            found.add(path)
            found |= _paths(value, path)
    elif isinstance(obj, list):
        for item in obj:
            entry = _entry_id(item)
            found |= _paths(item, (*prefix[:-1], f"{prefix[-1]}[{entry}]") if entry else prefix)
    return found


def _entry_id(item: Any) -> str | None:
    if not isinstance(item, dict):
        return None
    for key in ENTRY_KEYS:
        value = item.get(key)
        if isinstance(value, str):
            return value
    return None


def _elide(path: tuple[str, ...]) -> str:
    """The path with element names only: no entry name, no fused value."""
    return ".".join(
        seg.split("[", 1)[0].split(" ", 1)[0] + ("…" if "[" in seg or " " in seg else "")
        for seg in path
    )


@pytest.mark.parametrize(
    "conf", [pytest.param(p, id=f"{p.parent.parent.name}/{p.stem}") for p in _pairs()]
)
def test_junoscfg_renders_what_the_device_renders(conf: Path) -> None:
    first, _, body = conf.read_text(encoding="utf-8").partition("\n")
    assert first.startswith(HEADER), f"{conf.name} does not name its subtree"
    crumbs = shlex.split(first[len(HEADER) :])
    device = find_configuration(json.loads(conf.with_suffix(".json").read_text(encoding="utf-8")))
    assert device is not None, f"{conf.stem}.json carries no configuration"

    rendered = convert_config(
        _reroot(crumbs, body), from_format=Format.STRUCTURED, to_format=Format.JSON, validate=False
    )
    ours = json.loads(rendered)["configuration"]

    theirs = _paths(device)
    mine = _paths(ours)
    assert theirs, "the device rendered nothing"
    assert mine, "junoscfg rendered nothing: the fragment did not parse"
    missing = sorted({_elide(p) for p in theirs - mine})
    extra = sorted({_elide(p) for p in mine - theirs})
    assert not missing and not extra, (
        f"{len(missing)} missing from junoscfg: {missing[:6]}\n"
        f"{len(extra)} extra in junoscfg: {extra[:6]}"
    )


# ── identifier-key-fields: every door against the device's keyed entries ──
#
# `tests/data/captures/keyed-entries-*` are the shapes a vMX on 23.2R2-S7.5
# displayed for the probe's statements, rebuilt with the probe's synthetic
# values and with prompts, hostnames and `junos:changed-*` attributes left
# out. A group is one `.json` (the oracle) beside the `.set`, `.conf` and
# `.xml` the device displayed for the same statements; the device showed no
# structured or XML display for some, so those groups hold fewer doors.
# Spec: openspec/changes/identifier-key-fields/specs/conversion/entry-keys.

KEYED_DIR = PROJECT_ROOT / "tests" / "data" / "captures"
KEYED_GROUPS = ("as-lists", "identity", "community", "filters", "attributes-match")
_DOORS = {".set": Format.SET, ".conf": Format.STRUCTURED, ".xml": Format.XML, ".json": Format.JSON}
_CHANGED = {
    "junos:changed-seconds": "1759900000",
    "junos:changed-localtime": "2026-10-08 09:00:00 UTC",
}


def _strip_attributes(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {k: _strip_attributes(v) for k, v in obj.items() if not k.startswith("@")}
    if isinstance(obj, list):
        return [_strip_attributes(v) for v in obj]
    return obj


def _door_source(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    if path.suffix != ".conf":
        return text
    first, _, body = text.partition("\n")
    assert first.startswith(HEADER), f"{path.name} does not name its subtree"
    return _reroot(shlex.split(first[len(HEADER) :]), body)


def _ir(source: str, fmt: Format) -> dict[str, Any]:
    rendered = convert_config(source, from_format=fmt, to_format=Format.JSON, validate=False)
    return json.loads(rendered)["configuration"]


def _device(group: str) -> dict[str, Any]:
    path = KEYED_DIR / f"keyed-entries-{group}.json"
    return json.loads(path.read_text(encoding="utf-8"))["configuration"]


@pytest.mark.parametrize("group", KEYED_GROUPS)
def test_every_door_gives_the_device_ir(group: str) -> None:
    device = _device(group)
    doors = [
        KEYED_DIR / f"keyed-entries-{group}{suffix}"
        for suffix in _DOORS
        if (KEYED_DIR / f"keyed-entries-{group}{suffix}").is_file()
    ]
    assert len(doors) >= 2, f"{group}: the oracle and at least one door"
    for path in doors:
        assert _ir(_door_source(path), _DOORS[path.suffix]) == device, path.name
    set_lines = (KEYED_DIR / f"keyed-entries-{group}.set").read_text(encoding="utf-8")
    rendered = convert_config(
        json.dumps({"configuration": device}),
        from_format=Format.JSON,
        to_format=Format.SET,
        validate=False,
    )
    assert rendered.strip().splitlines() == set_lines.strip().splitlines(), group


def _with_changed(obj: Any) -> Any:
    """*obj* with `junos:changed-*` on every element, as a device marks edits."""
    if isinstance(obj, dict):
        marked = {k: _with_changed(v) for k, v in obj.items()}
        marked["@"] = dict(_CHANGED)
        return marked
    if isinstance(obj, list):
        return [_with_changed(v) for v in obj]
    return obj


@pytest.mark.parametrize("group", KEYED_GROUPS)
def test_device_attributes_leave_the_keys_alone(group: str) -> None:
    """JSON and XML carrying `junos:changed-*` give the same keyed entries."""
    import re

    device = _device(group)
    marked = json.dumps({"configuration": _with_changed(device)})
    assert _strip_attributes(_ir(marked, Format.JSON)) == device

    xml_path = KEYED_DIR / f"keyed-entries-{group}.xml"
    if xml_path.is_file():
        attributes = " ".join(f'{k}="{v}"' for k, v in _CHANGED.items())
        xml = re.sub(r"<([a-z][\w-]*)>", rf"<\1 {attributes}>", xml_path.read_text("utf-8"))
        assert _strip_attributes(_ir(xml, Format.XML)) == device


def test_name_keyed_set_lines_match_the_device() -> None:
    """A `name`-keyed entry with two children is one line per child, as the
    device's `display set` wrote it. Pinned as it is; it must stay so."""
    device = (KEYED_DIR / "keyed-entries-name-keyed.json").read_text(encoding="utf-8")
    expected = (KEYED_DIR / "keyed-entries-name-keyed.set").read_text(encoding="utf-8")
    rendered = convert_config(device, from_format=Format.JSON, to_format=Format.SET, validate=False)
    assert rendered.strip().splitlines() == expected.strip().splitlines()
    back = convert_config(expected, from_format=Format.SET, to_format=Format.SET, validate=False)
    assert back.strip().splitlines() == expected.strip().splitlines()


def test_unexplained_structured_shapes_are_pinned() -> None:
    """The device's structured shapes junoscfg does not write, beside its own."""
    known = json.loads((KEYED_DIR / "keyed-entries-known-differences.json").read_text("utf-8"))
    assert len(known["cases"]) == 2
    for case in known["cases"]:
        rendered = convert_config(
            json.dumps(case["input"]),
            from_format=Format.JSON,
            to_format=Format.STRUCTURED,
            validate=False,
        )
        assert case["junoscfg"] in rendered, case["case"]
        assert case["device"] not in rendered, f"{case['case']}: no longer a difference"


# ── identifier-key-fields, device round 4: route-filter identity ─────
#
# `keyed-entries-route-filter.*`: R, one address with two match types, is two
# entries; S, `exact accept` then `exact metric 10` on one address, is one
# entry. Input acceptance and IR only, not structured layout (owner ruling).
# The device's JSON writes `metric` as a number, which the set and XML readers
# hold as text: numeric JSON normalization is outside this change, so those
# doors are compared with the device's numbers as text.


def _as_text(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {k: _as_text(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_as_text(v) for v in obj]
    if isinstance(obj, (int, float)) and not isinstance(obj, bool):
        return str(obj)
    return obj


def test_route_filter_entries_are_keyed_by_address_and_match_type() -> None:
    device = _device("route-filter")
    assert _ir(_door_source(KEYED_DIR / "keyed-entries-route-filter.json"), Format.JSON) == device
    for suffix in (".set", ".xml"):
        path = KEYED_DIR / f"keyed-entries-route-filter{suffix}"
        assert _ir(path.read_text(encoding="utf-8"), _DOORS[suffix]) == _as_text(device), suffix
    rendered = convert_config(
        json.dumps({"configuration": device}),
        from_format=Format.JSON,
        to_format=Format.SET,
        validate=False,
    )
    expected = (KEYED_DIR / "keyed-entries-route-filter.set").read_text(encoding="utf-8")
    assert rendered.strip().splitlines() == expected.strip().splitlines()


def test_a_match_type_before_the_address_is_accepted() -> None:
    """T: the device accepts `route-filter exact <address>` and stores it as
    `route-filter <address> exact` (round 4)."""
    term = "set policy-options policy-statement SAMPLE-POLICY term T11 from route-filter"
    before = f"{term} exact 198.51.100.0/24\n"
    after = f"{term} 198.51.100.0/24 exact\n"
    assert _ir(before, Format.SET) == _ir(after, Format.SET)
    rendered = convert_config(before, from_format=Format.SET, to_format=Format.SET, validate=False)
    assert rendered.strip().splitlines() == [after.strip()]
