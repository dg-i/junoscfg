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
