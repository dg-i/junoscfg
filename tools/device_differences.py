"""Regenerate tests/data/device/known-differences.json from the device captures.

For each capture and rendering, junoscfg's set rendering is compared with the
device's own display set (`tests/support/devices.py`). Every line that differs
is recorded with its class: a junoscfg defect, a rendering the device loads as
the same configuration, a question the device has not answered yet, or a quirk
of the device's own renderings. The rules match on keywords and the shape of a
statement, never on a test value. A line no rule claims stops the tool: a new
difference is classified before it is recorded, never recorded blind.

Run after a fix, a recapture or a new capture:
``uv run python tools/device_differences.py``; the test
`tests/corpus/test_device_renderings.py` fails until the record matches.
"""

# Every class claims through one signature (line, side, suffix, capture); a rule
# that reads only some of them is not an unused argument.
# ruff: noqa: ARG005

from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tests.support.devices import FORMATS, KNOWN_DIFFERENCES, captures  # noqa: E402

if TYPE_CHECKING:
    from collections.abc import Callable

    from tests.support.devices import Capture


@dataclass(frozen=True)
class Class:
    """A kind of difference, with what it is and how a line is recognised."""

    name: str
    kind: str  # defect | equivalent | open | device-quirk
    definition: str
    claims: Callable[[str, str, str, Capture], bool]


def _re(pattern: str) -> Callable[[str], bool]:
    found = re.compile(pattern).search
    return lambda line: found(line) is not None


_POLICY_QUOTED = _re(r'\b(import|export) "\(')
_POLICY_BARE = _re(r"\b(import|export) \(")
_LEAKS = _re(
    r" rf_list | server-group server-group | other-variables | bridge-domains domain "
    r"| dynamic-tunnels dynamic-tunnel | hello-padding-type "
)
_LEAK_TARGETS = _re(
    r"\b(route-filter-list|server-group|predefined-variable-defaults|bridge-domains"
    r"|dynamic-tunnels|hello-padding)\b"
)


def _omitted_groups(capture: Capture) -> tuple[str, ...]:
    """Statements of a group the device's curly prints as `{ /* OMITTED */ }`.

    `apply-flags omit` hides a statement's content in curly output, the flag
    included, so the placeholder is all there is to find.
    """
    curly = capture.rendering("conf")
    found = re.findall(
        r"^    (\S+) \{\n(?:        .*\n)*?        (\S+) \{ /\* OMITTED \*/ \};", curly, re.M
    )
    return tuple(f"set groups {group} {statement} " for group, statement in found)


def _bare_deactivates(capture: Capture) -> tuple[str, ...]:
    """Statements the device's display set deactivates without a `set` line for them."""
    lines = capture.device_set()
    sets = [line[4:] for line in lines if line.startswith("set ")]
    return tuple(
        line[len("deactivate ") :]
        for line in lines
        if line.startswith("deactivate ")
        and not any(s.startswith(line[len("deactivate ") :]) for s in sets)
    )


CLASSES = (
    Class(
        "junos-variable-quoted",
        "equivalent",
        "junoscfg quotes `$junos-...` variables the device prints bare; the device loads both "
        "as the same configuration",
        lambda line, side, suffix, c: "$junos-" in line,
    ),
    Class(
        "transport-class-dict",
        "defect",
        "`routing-options transport-class name N ...` is written with a Python dict as the "
        "name, and every entry after the first is lost; a JSON number stays a number inside it",
        lambda line, side, suffix, c: "transport-class" in line,
    ),
    Class(
        "overload-timeout-dropped",
        "defect",
        "`isis overload timeout N` is written `overload N`, which the device rejects",
        lambda line, side, suffix, c: _re(r"\boverload (timeout )?\S+$")(line),
    ),
    Class(
        "radius-timeout-dropped",
        "defect",
        "`radius-server <address> timeout N` is written `radius-server <address> N`, which the "
        "device accepts and loads without the timeout",
        lambda line, side, suffix, c: _re(r"\bradius-server \S+ (timeout )?\d+$")(line),
    ),
    Class(
        "policy-expression-double-quoted",
        "defect",
        'from XML, a policy expression is written `""( P )""`, which does not load',
        lambda line, side, suffix, c: '""(' in line,
    ),
    Class(
        "policy-expression-quoted",
        "defect",
        'a single-term policy expression `( P )` is written `"( P )"`, which the device reads '
        "as a policy name",
        lambda line, side, suffix, c: (
            (side == "extra" and _POLICY_QUOTED(line)) or (side == "missing" and _POLICY_BARE(line))
        ),
    ),
    Class(
        "policy-name-unquoted",
        "defect",
        'the quoted policy name `"( A && B )"` is written unquoted, which the device reads as '
        "an expression",
        lambda line, side, suffix, c: (
            (side == "extra" and _POLICY_BARE(line)) or (side == "missing" and _POLICY_QUOTED(line))
        ),
    ),
    Class(
        "escaped-quote-lost",
        "defect",
        'a value holding an escaped quote `\\"` is written with bare inner quotes, which does '
        "not load",
        lambda line, side, suffix, c: (
            (side == "missing" and '\\"' in line)
            or (side == "extra" and _re(r'"[^"]* "[^"\s]+""$')(line))
        ),
    ),
    Class(
        "inactive-keyed-entry-repeated",
        "defect",
        "from set input, an inactive keyed entry such as `port-mirroring ... routing-instance "
        "R` is written `... routing-instance R R`",
        lambda line, side, suffix, c: suffix == "set" and "port-mirroring" in line,
    ),
    Class(
        "inactive-keyed-entry-name-leak",
        "defect",
        "from curly input, the same entry is written `... routing-instance R name`",
        lambda line, side, suffix, c: suffix == "conf" and "port-mirroring" in line,
    ),
    Class(
        "xml-element-name-leak",
        "defect",
        "from XML or JSON, an element the CLI hides appears in the set path (rf_list, "
        "server-group server-group, other-variables, bridge-domains domain, dynamic-tunnels "
        "dynamic-tunnel, hello-padding-type); the same statements curly input reports as "
        "not placed in the schema",
        lambda line, side, suffix, c: (
            suffix in ("xml", "json")
            and (_LEAKS(line) or (side == "missing" and _LEAK_TARGETS(line)))
        ),
    ),
    Class(
        "xml-value-whitespace-lost",
        "defect",
        'from XML, leading or trailing spaces in a value are stripped (`"^show "` becomes '
        '`"^show"`)',
        lambda line, side, suffix, c: (
            suffix == "xml"
            and (
                _re(r'"\s[^"]*"$|"[^"]*\s"$')(line)
                if side == "missing"
                else _re(r'"[^"\s]+"$')(line)
            )
        ),
    ),
    Class(
        "trigger-after-split",
        "device-quirk",
        "the device's display set prints `within N trigger after 1` as two lines, `... trigger "
        "after` and `... trigger 1`; curly, XML and JSON hold one statement",
        lambda line, side, suffix, c: side == "missing" and _re(r" trigger (after|\d+)$")(line),
    ),
    Class(
        "trigger-after-one-line",
        "open",
        "junoscfg writes `within N trigger after 1` as one set line where the device prints "
        "two; whether set input loads both alike needs a device load test",
        lambda line, side, suffix, c: side == "extra" and _re(r" trigger after \d+$")(line),
    ),
    Class(
        "omitted-curly",
        "device-quirk",
        "the device's curly prints a group with `apply-flags omit` as `/* OMITTED */`, so the "
        "curly rendering lacks that group's content; XML, JSON and set carry it",
        lambda line, side, suffix, c: (
            suffix == "conf"
            and side == "missing"
            and line.startswith(("set ", "deactivate ", "protect "))
            and any(line.split(" ", 1)[1].startswith(g[4:]) for g in _omitted_groups(c))
        ),
    ),
    Class(
        "bare-deactivate-route-filter",
        "device-quirk",
        "the device's display set prints an inactive route-filter as a bare `deactivate` with "
        "no `set` line for it",
        lambda line, side, suffix, c: (
            "route-filter" in line and any(b in line for b in _bare_deactivates(c))
        ),
    ),
)


def classify(line: str, side: str, suffix: str, capture: Capture) -> str | None:
    """The first class that claims the line, or None."""
    return next((k.name for k in CLASSES if k.claims(line, side, suffix, capture)), None)


def main() -> int:
    """Write the record; refuse, listing them, while any line has no class."""
    differences: dict[str, dict[str, dict[str, str]]] = {}
    unclaimed = []
    for capture in captures():
        for suffix in FORMATS:
            found = capture.difference(suffix)
            entry = {}
            for side, lines in found.items():
                labelled = {}
                for line in lines:
                    name = classify(line, side, suffix, capture)
                    if name is None:
                        unclaimed.append(f"{capture.key}.{suffix} {side}: {line}")
                    labelled[line] = name
                if labelled:
                    entry[side] = labelled
            if entry:
                differences[f"{capture.key}.{suffix}"] = entry
    if unclaimed:
        print("\n".join(unclaimed))
        print(f"\n{len(unclaimed)} line(s) no class claims; classify them first", file=sys.stderr)
        return 1
    record = {
        "classes": {k.name: {"kind": k.kind, "definition": k.definition} for k in CLASSES},
        "differences": differences,
    }
    KNOWN_DIFFERENCES.write_text(
        json.dumps(record, indent=1, sort_keys=True) + "\n", encoding="utf-8"
    )
    lines = sum(len(v) for e in differences.values() for v in e.values())
    print(f"{lines} lines in {len(differences)} renderings")
    return 0


if __name__ == "__main__":
    sys.exit(main())
