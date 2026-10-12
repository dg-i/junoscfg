"""The shape catalogue: one configuration per row, in every format it is written in.

A shape is data. It names a configuration, gives it in each format it can be
written in (XML is input only), and says what must hold:

- every source reads as the same IR (``ir``; when omitted, the IR the first
  source reads as, so the row asserts that the readers agree);
- every writer's output reads back as that IR, except where a writer cannot
  carry part of it (``read_back``, keyed by writer, with the reason in
  ``why``);
- a writer never writes what it cannot carry (``never_written``), and writes
  a statement as the device spells it where a row names the text
  (``written``);
- every reader keeps an entry's key fields first, in the declared order,
  where a row says the order is meaning (``ordered``);
- set output is one line per statement, the device's ``display set``, where a
  row declares it (``set_output``);
- the JSON and YAML renderings validate against the bundled schemas, unless
  the row is not valid Junos as written (``valid``), when they are rejected.

`tests/contract/test_format_matrix.py` checks every row through every reader
and writer, and `tests/contract/test_round_trip_validates.py` checks every
row's JSON and YAML rendering against the bundled schemas. A fix to
conversion adds a row here; provenance (device evidence, the change that
added it) goes in ``why``.

The IR is read through the public door: the JSON rendering's
``configuration`` object, so a row compares what a library user sees.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import TYPE_CHECKING, Any
from xml.sax.saxutils import escape as xml_escape

from junoscfg import Format, convert_config

if TYPE_CHECKING:
    from collections.abc import Mapping

SET = Format.SET
STRUCTURED = Format.STRUCTURED
JSON = Format.JSON
YAML = Format.YAML
XML = Format.XML

#: Every format junoscfg writes; XML output is not implemented.
WRITERS: tuple[Format, ...] = (SET, STRUCTURED, JSON, YAML)

#: The key under which a level keeps the statements the reader could not
#: place, each as its own tokens (spec conversion/entry-keys). A consumer sees
#: it in JSON and YAML output, so the rows pin the literal.
UNPLACED_RECORD = "junoscfg:unplaced"


def read_ir(text: str, fmt: Format) -> Any:
    """The IR *text* reads as: the ``configuration`` object of its JSON rendering."""
    return json.loads(convert_config(text, from_format=fmt, to_format=JSON))["configuration"]


def _empty() -> Mapping[Any, Any]:
    return MappingProxyType({})


@dataclass(frozen=True)
class Shape:
    """One configuration, its sources, and what reading and writing it must keep."""

    name: str
    sources: Mapping[Format, str]
    ir: Any = None
    set_output: str | None = None
    read_back: Mapping[Format, Any] = field(default_factory=_empty)
    never_written: Mapping[Format, tuple[str, ...]] = field(default_factory=_empty)
    written: Mapping[Format, tuple[str, ...]] = field(default_factory=_empty)
    ordered: bool = False
    valid: bool = True
    why: str = ""

    def expected_ir(self) -> Any:
        """The IR every source must read as."""
        if self.ir is not None:
            return self.ir
        first = next(iter(self.sources))
        return read_ir(self.sources[first], first)

    def expected_after(self, writer: Format) -> Any:
        """The IR *writer*'s output must read back as."""
        if writer in self.read_back:
            return self.read_back[writer]
        return self.expected_ir()

    @property
    def lossless(self) -> bool:
        """Every writer carries the whole IR."""
        return not self.read_back


def _json(config: dict[str, Any]) -> str:
    return json.dumps({"configuration": config})


def _xml(body: str) -> str:
    return f"<configuration>{body}</configuration>"


def _nest(path: list[str], body: str) -> str:
    """Wrap *body* in the curly blocks *path* opens, four spaces a level."""
    text = body
    for depth, opener in reversed(list(enumerate(path))):
        pad = "    " * depth
        text = f"{pad}{opener} {{\n{text}{pad}}}\n"
    return text


def _unit_751(unit: dict[str, Any]) -> dict[str, Any]:
    """Unit 751 of xe-0/0/0 holding *unit*: the IR the deactivate6.txt rows share."""
    return {"interfaces": {"interface": [{"name": "xe-0/0/0", "unit": [{"name": "751", **unit}]}]}}


#: `vlan-id 751` tagged inactive, as a device's JSON writes it: the value and a sibling `@`.
_VLAN_ID_INACTIVE = {"vlan-id": "751", "@vlan-id": {"inactive": True}}
_INET_INACTIVE = {
    "@": {"inactive": True},
    "filter": {"input": {"filter-name": "FILTER-V4"}},
    "address": [{"name": "198.51.100.1/24"}],
}
_ROUTE_V6 = {
    "route": [{"@": {"inactive": True}, "name": "::/0", "apply-groups": ["G_LOC", "G_DEF"]}]
}


SHAPES: list[Shape] = []


def _add(*shapes: Shape) -> None:
    SHAPES.extend(shapes)


# ── Plain statements ─────────────────────────────────────────────────

_add(
    Shape(
        "a-leaf",
        {
            SET: "set system host-name r1\n",
            STRUCTURED: "system {\n    host-name r1;\n}\n",
            JSON: _json({"system": {"host-name": "r1"}}),
            YAML: "configuration:\n  system:\n    host-name: r1\n",
            XML: _xml("<system><host-name>r1</host-name></system>"),
        },
        ir={"system": {"host-name": "r1"}},
        set_output="set system host-name r1\n",
        why="One leaf through every pair: the former TestConvert<A>To<B> classes, "
        "TestPublicAPI and TestYamlPublicAPI.",
    ),
    Shape(
        "two-leaves",
        {
            SET: "set system host-name r1\nset system domain-name example.com\n",
            STRUCTURED: "system {\n    host-name r1;\n    domain-name example.com;\n}\n",
            JSON: _json({"system": {"host-name": "r1", "domain-name": "example.com"}}),
            YAML: "configuration:\n  system:\n    host-name: r1\n    domain-name: example.com\n",
            XML: _xml(
                "<system><host-name>r1</host-name><domain-name>example.com</domain-name></system>"
            ),
        },
        ir={"system": {"host-name": "r1", "domain-name": "example.com"}},
        set_output="set system host-name r1\nset system domain-name example.com\n",
    ),
    Shape(
        "a-leaf-under-nested-containers",
        {
            SET: "set system services ssh root-login deny\n",
            JSON: _json({"system": {"services": {"ssh": {"root-login": "deny"}}}}),
        },
        ir={"system": {"services": {"ssh": {"root-login": "deny"}}}},
        set_output="set system services ssh root-login deny\n",
    ),
    Shape(
        "a-value-with-a-space",
        {
            SET: 'set system host-name "my router"\n',
            STRUCTURED: 'system {\n    host-name "my router";\n}\n',
            JSON: _json({"system": {"host-name": "my router"}}),
        },
        ir={"system": {"host-name": "my router"}},
        set_output='set system host-name "my router"\n',
        why="A value with a space is quoted in set output.",
    ),
    Shape(
        "a-numeric-leaf",
        {
            XML: _xml(
                "<system><login><user><name>admin</name><uid>2000</uid></user></login></system>"
            ),
            STRUCTURED: _nest(["system", "login", "user admin"], "            uid 2000;\n"),
            SET: "set system login user admin uid 2000\n",
        },
        ir={"system": {"login": {"user": [{"name": "admin", "uid": "2000"}]}}},
        set_output="set system login user admin uid 2000\n",
        why="Junos JSON is string-valued and the IR follows it: XML input once gave an int "
        "where structured gave a string, and set output hid it (xml-ir-parity).",
    ),
    Shape(
        "a-key-alias",
        {
            XML: _xml(
                "<interfaces><interface><name>ge-0/0/2</name><ether-options><ieee-802.3ad>"
                "<bundle>ae0</bundle></ieee-802.3ad></ether-options></interface></interfaces>"
            ),
            STRUCTURED: _nest(
                ["interfaces", "ge-0/0/2", "ether-options"], "            802.3ad ae0;\n"
            ),
            SET: "set interfaces ge-0/0/2 ether-options 802.3ad ae0\n",
        },
        ir={
            "interfaces": {
                "interface": [{"name": "ge-0/0/2", "ether-options": {"802.3ad": {"bundle": "ae0"}}}]
            }
        },
        set_output="set interfaces ge-0/0/2 ether-options 802.3ad ae0\n",
        why="`<ieee-802.3ad>` is `802.3ad`: `KEY_ALIASES` was once consulted by the set "
        "reader only, so XML input kept the element's name (xml-ir-parity).",
    ),
    Shape(
        "an-empty-configuration",
        {
            SET: "",
            STRUCTURED: "",
            JSON: '{"configuration": {}}',
            YAML: "configuration: {}\n",
            XML: "<configuration/>",
        },
        ir={},
        set_output="",
    ),
    Shape(
        "a-json-rpc-reply-wrapper",
        {JSON: json.dumps({"rpc-reply": {"configuration": {"system": {"host-name": "test"}}}})},
        ir={"system": {"host-name": "test"}},
        set_output="set system host-name test\n",
        why="The JSON reader finds the configuration inside an rpc-reply.",
    ),
    Shape(
        "yaml-with-ansible-meta-keys",
        {
            YAML: "configuration:\n  system:\n    host-name: r1\n"
            "  _ansible_version: '2.9'\n  _meta_timestamp: '2024-01-01'\n"
        },
        ir={"system": {"host-name": "r1"}},
        why="The YAML reader drops the underscore keys Ansible adds.",
    ),
)

# ── Named lists, transparent keys, groups ────────────────────────────

_add(
    Shape(
        "two-interfaces",
        {
            SET: "set interfaces ge-0/0/0 description uplink\n"
            "set interfaces ge-0/0/1 description downlink\n",
            STRUCTURED: "interfaces {\n    ge-0/0/0 {\n        description uplink;\n    }\n"
            "    ge-0/0/1 {\n        description downlink;\n    }\n}\n",
            JSON: _json(
                {
                    "interfaces": {
                        "interface": [
                            {"name": "ge-0/0/0", "description": "uplink"},
                            {"name": "ge-0/0/1", "description": "downlink"},
                        ]
                    }
                }
            ),
        },
        ir={
            "interfaces": {
                "interface": [
                    {"name": "ge-0/0/0", "description": "uplink"},
                    {"name": "ge-0/0/1", "description": "downlink"},
                ]
            }
        },
        set_output="set interfaces ge-0/0/0 description uplink\n"
        "set interfaces ge-0/0/1 description downlink\n",
    ),
    Shape(
        "an-interface-address",
        {
            SET: "set interfaces ge-0/0/0 unit 0 family inet address 10.0.0.1/24\n",
            JSON: _json(
                {
                    "interfaces": {
                        "interface": [
                            {
                                "name": "ge-0/0/0",
                                "unit": [
                                    {
                                        "name": "0",
                                        "family": {"inet": {"address": [{"name": "10.0.0.1/24"}]}},
                                    }
                                ],
                            }
                        ]
                    }
                }
            ),
            XML: _xml(
                "<interfaces><interface><name>ge-0/0/0</name><unit><name>0</name><family><inet>"
                "<address><name>10.0.0.1/24</name></address></inet></family></unit></interface>"
                "</interfaces>"
            ),
        },
        set_output="set interfaces ge-0/0/0 unit 0 family inet address 10.0.0.1/24\n",
    ),
    Shape(
        "a-system-and-a-bare-unit",
        {
            SET: "set system host-name r1\nset system domain-name example.com\n"
            "set interfaces ge-0/0/0 unit 0\n",
            JSON: _json(
                {
                    "system": {"host-name": "r1", "domain-name": "example.com"},
                    "interfaces": {"interface": [{"name": "ge-0/0/0", "unit": [{"name": "0"}]}]},
                }
            ),
        },
        ir={
            "system": {"host-name": "r1", "domain-name": "example.com"},
            "interfaces": {"interface": [{"name": "ge-0/0/0", "unit": [{"name": "0"}]}]},
        },
    ),
    Shape(
        "a-system-and-an-addressed-interface",
        {
            SET: "set system host-name router1\nset system domain-name example.com\n"
            "set interfaces ge-0/0/0 description uplink\n"
            "set interfaces ge-0/0/0 unit 0 family inet address 10.0.0.1/24\n",
            JSON: _json(
                {
                    "system": {"host-name": "router1", "domain-name": "example.com"},
                    "interfaces": {
                        "interface": [
                            {
                                "name": "ge-0/0/0",
                                "description": "uplink",
                                "unit": [
                                    {
                                        "name": "0",
                                        "family": {"inet": {"address": [{"name": "10.0.0.1/24"}]}},
                                    }
                                ],
                            }
                        ]
                    },
                }
            ),
        },
    ),
    Shape(
        "groups",
        {
            SET: "set groups mygroup system host-name r1\n"
            "set groups other system domain-name example.com\n",
            STRUCTURED: "groups {\n    mygroup {\n        system {\n            host-name r1;\n"
            "        }\n    }\n    other {\n        system {\n"
            "            domain-name example.com;\n        }\n    }\n}\n",
            JSON: _json(
                {
                    "groups": [
                        {"name": "mygroup", "system": {"host-name": "r1"}},
                        {"name": "other", "system": {"domain-name": "example.com"}},
                    ]
                }
            ),
            YAML: "configuration:\n  groups:\n  - name: mygroup\n    system:\n      host-name: r1\n"
            "  - name: other\n    system:\n      domain-name: example.com\n",
        },
        ir={
            "groups": [
                {"name": "mygroup", "system": {"host-name": "r1"}},
                {"name": "other", "system": {"domain-name": "example.com"}},
            ]
        },
        why='Native Junos JSON: "groups" holds the entries, not {"group": [...]}.',
    ),
    Shape(
        "a-prefix-list",
        {
            SET: "set policy-options prefix-list MY-LIST 127.0.0.1/32\n"
            "set policy-options prefix-list MY-LIST 10.0.0.0/8\n",
            STRUCTURED: "policy-options {\n    prefix-list MY-LIST {\n        127.0.0.1/32;\n"
            "        10.0.0.0/8;\n    }\n}\n",
            JSON: _json(
                {
                    "policy-options": {
                        "prefix-list": [
                            {
                                "name": "MY-LIST",
                                "prefix-list-item": [
                                    {"name": "127.0.0.1/32"},
                                    {"name": "10.0.0.0/8"},
                                ],
                            }
                        ]
                    }
                }
            ),
        },
        ir={
            "policy-options": {
                "prefix-list": [
                    {
                        "name": "MY-LIST",
                        "prefix-list-item": [{"name": "127.0.0.1/32"}, {"name": "10.0.0.0/8"}],
                    }
                ]
            }
        },
        why="prefix-list-item is a transparent list key: set and curly name no keyword.",
    ),
    Shape(
        "syslog-contents",
        {
            SET: "set system syslog file messages interactive-commands any\n",
            JSON: _json(
                {
                    "system": {
                        "syslog": {
                            "file": [
                                {
                                    "name": "messages",
                                    "contents": [{"name": "interactive-commands", "any": [None]}],
                                }
                            ]
                        }
                    }
                }
            ),
        },
        ir={
            "system": {
                "syslog": {
                    "file": [
                        {
                            "name": "messages",
                            "contents": [{"name": "interactive-commands", "any": [None]}],
                        }
                    ]
                }
            }
        },
        why="contents is a transparent list key.",
    ),
)

# ── JSON keeps the shape it was given ────────────────────────────────
#
# The JSON reader keeps its supplied value shapes without loading the schema
# (src/junoscfg/convert/CONTRACT.md), so these JSON spellings stay as given in
# the JSON and YAML renderings; set and structured output, and the YAML
# reader where a leaf-list is concerned, canonicalize them.

_NAME_SERVERS = {"host-name": "r1", "domain-name": "example.com"}
_FW_TERM = {"name": "accept-ssh", "then": {"accept": [None]}}

_add(
    Shape(
        "name-servers-as-plain-strings-in-json",
        {JSON: _json({"system": {**_NAME_SERVERS, "name-server": ["8.8.8.8", "8.8.4.4"]}})},
        ir={"system": {**_NAME_SERVERS, "name-server": ["8.8.8.8", "8.8.4.4"]}},
        read_back={
            w: {
                "system": {
                    **_NAME_SERVERS,
                    "name-server": [{"name": "8.8.8.8"}, {"name": "8.8.4.4"}],
                }
            }
            for w in (SET, STRUCTURED)
        },
        why="name-server is a named list; set and curly have no spelling for bare strings.",
    ),
    Shape(
        "a-next-hop-as-a-scalar-in-json",
        {
            JSON: _json(
                {
                    "routing-options": {
                        "static": {"route": [{"name": "0.0.0.0/0", "next-hop": "10.0.0.1"}]}
                    }
                }
            )
        },
        ir={
            "routing-options": {
                "static": {"route": [{"name": "0.0.0.0/0", "next-hop": "10.0.0.1"}]}
            }
        },
        read_back={
            w: {
                "routing-options": {
                    "static": {"route": [{"name": "0.0.0.0/0", "next-hop": ["10.0.0.1"]}]}
                }
            }
            for w in (SET, STRUCTURED, YAML)
        },
        why="next-hop is a leaf-list; the set, structured and YAML readers promote a scalar.",
    ),
    Shape(
        "a-firewall-term-with-scalar-leaf-lists-in-json",
        {
            JSON: _json(
                {
                    "firewall": {
                        "family": {
                            "inet": {
                                "filter": [
                                    {
                                        "name": "PROTECT",
                                        "term": [
                                            {
                                                **_FW_TERM,
                                                "from": {
                                                    "protocol": "tcp",
                                                    "destination-port": "ssh",
                                                },
                                            }
                                        ],
                                    }
                                ]
                            }
                        }
                    }
                }
            )
        },
        read_back={
            w: {
                "firewall": {
                    "family": {
                        "inet": {
                            "filter": [
                                {
                                    "name": "PROTECT",
                                    "term": [
                                        {
                                            **_FW_TERM,
                                            "from": {
                                                "protocol": ["tcp"],
                                                "destination-port": ["ssh"],
                                            },
                                        }
                                    ],
                                }
                            ]
                        }
                    }
                }
            }
            for w in (SET, STRUCTURED, YAML)
        },
    ),
    Shape(
        "a-policy-expression-as-a-scalar-in-json",
        {
            JSON: _json(
                {
                    "policy-options": {
                        "policy-statement": [
                            {
                                "name": "test",
                                "term": [{"name": "t1", "from": {"policy": "(( a && ! b ) || c)"}}],
                            }
                        ]
                    }
                }
            )
        },
        set_output="set policy-options policy-statement test term t1 "
        "from policy (( a && ! b ) || c)\n",
        read_back={
            w: {
                "policy-options": {
                    "policy-statement": [
                        {
                            "name": "test",
                            "term": [{"name": "t1", "from": {"policy": ["(( a && ! b ) || c)"]}}],
                        }
                    ]
                }
            }
            for w in (SET, STRUCTURED, YAML)
        },
        why="A policy expression is written unquoted, parentheses and all.",
    ),
    Shape(
        "a-number-value-in-device-json",
        {
            JSON: _json(
                {
                    "interfaces": {
                        "interface": [
                            {
                                "name": "xe-0/0/0",
                                "unit": [
                                    {"name": "751", "vlan-id": 751, "@vlan-id": {"inactive": True}}
                                ],
                            }
                        ]
                    }
                }
            )
        },
        set_output="set interfaces xe-0/0/0 unit 751 vlan-id 751\n"
        "deactivate interfaces xe-0/0/0 unit 751 vlan-id\n",
        read_back={
            w: {
                "interfaces": {
                    "interface": [
                        {
                            "name": "xe-0/0/0",
                            "unit": [
                                {"name": "751", "vlan-id": "751", "@vlan-id": {"inactive": True}}
                            ],
                        }
                    ]
                }
            }
            for w in (SET, STRUCTURED)
        },
        why='deactivate6.txt writes `"vlan-id" : 751`, a number; the set lines are the '
        "same as for the XML spelling (the inactive-vlan-id row).",
    ),
    Shape(
        "a-json-leaf-the-schema-has-as-a-container",
        {JSON: _json({"system": {"location": "dc-a"}})},
        ir={"system": {"location": "dc-a"}},
        set_output="set system location dc-a\n",
        read_back={
            w: {"system": {"location": {UNPLACED_RECORD: {"dc-a": [None]}}}}
            for w in (SET, STRUCTURED)
        },
        valid=False,
        why="`location` is a container and `dc-a` none of its statements: set and "
        "structured input keep the word as written rather than drop it. The annotation "
        "rows once used `location dc-a` as their second leaf.",
    ),
    Shape(
        "an-inactive-vlan-id",
        {
            SET: "set interfaces xe-0/0/0 unit 751 vlan-id 751\n"
            "deactivate interfaces xe-0/0/0 unit 751 vlan-id\n",
            XML: _xml(
                "<interfaces><interface><name>xe-0/0/0</name><unit><name>751</name>"
                '<vlan-id inactive="inactive">751</vlan-id></unit></interface></interfaces>'
            ),
            STRUCTURED: _nest(
                ["interfaces", "xe-0/0/0", "unit 751"], "            inactive: vlan-id 751;\n"
            ),
            JSON: _json(_unit_751(_VLAN_ID_INACTIVE)),
        },
        ir=_unit_751(_VLAN_ID_INACTIVE),
        set_output="set interfaces xe-0/0/0 unit 751 vlan-id 751\n"
        "deactivate interfaces xe-0/0/0 unit 751 vlan-id\n",
        why="deactivate6.txt (23.2R2-S7.5): XML tags the element, set writes `deactivate` "
        "without the value, curly prints `inactive: vlan-id 751;`, JSON the value and a "
        "sibling `@vlan-id`. XML input once nested the value under its own name, so set "
        "output read `vlan-id vlan-id 751`. Spec conversion/meta-tags (xml-inactive-leaf).",
    ),
)

# ── Annotations: `@` on a container or a leaf ────────────────────────
#
# docs/guide/annotations.md. The second leaf keeps the annotation visibly the
# container's: a tag that moved onto a leaf would change the set lines.

_SYSTEM = {"host-name": "r1", "domain-name": "example.com"}
_SYSTEM_SET = "set system host-name r1\nset system domain-name example.com\n"
_SYSTEM_CURLY = "    host-name r1;\n    domain-name example.com;\n"

_add(
    Shape(
        "an-inactive-container",
        {
            SET: _SYSTEM_SET + "deactivate system\n",
            STRUCTURED: "inactive: system {\n" + _SYSTEM_CURLY + "}\n",
            JSON: _json({"system": {"@": {"inactive": True}, **_SYSTEM}}),
        },
        ir={"system": {"@": {"inactive": True}, **_SYSTEM}},
        set_output=_SYSTEM_SET + "deactivate system\n",
    ),
    Shape(
        "an-active-container",
        {
            SET: _SYSTEM_SET + "activate system\n",
            JSON: _json({"system": {"@": {"active": "active"}, **_SYSTEM}}),
        },
        ir={"system": {"@": {"active": "active"}, **_SYSTEM}},
        set_output=_SYSTEM_SET + "activate system\n",
        read_back={STRUCTURED: {"system": _SYSTEM}},
        why="Active is the default state; structured output carries no marker for it.",
    ),
    Shape(
        "a-protected-container",
        {
            SET: _SYSTEM_SET + "protect system\n",
            STRUCTURED: "protect: system {\n" + _SYSTEM_CURLY + "}\n",
            JSON: _json({"system": {"@": {"protect": "protect"}, **_SYSTEM}}),
        },
        ir={"system": {"@": {"protect": "protect"}, **_SYSTEM}},
        set_output=_SYSTEM_SET + "protect system\n",
    ),
    Shape(
        "a-replaced-container",
        {
            STRUCTURED: "replace: system {\n" + _SYSTEM_CURLY + "}\n",
            JSON: _json({"system": {"@": {"operation": "replace"}, **_SYSTEM}}),
        },
        ir={"system": {"@": {"operation": "replace"}, **_SYSTEM}},
        set_output=_SYSTEM_SET,
        read_back={SET: {"system": _SYSTEM}},
        never_written={SET: ("replace",)},
        why="Display-set syntax has no replace command; set output drops the annotation.",
    ),
    Shape(
        "an-inactive-container-with-one-leaf",
        {
            SET: "set system host-name r1\ndeactivate system\n",
            STRUCTURED: "inactive: system {\n    host-name r1;\n}\n",
            JSON: _json({"system": {"@": {"inactive": True}, "host-name": "r1"}}),
            YAML: "configuration:\n  system:\n    '@':\n      inactive: true\n    host-name: r1\n",
            XML: '<configuration><system inactive="inactive">'
            "<host-name>r1</host-name></system></configuration>",
        },
        ir={"system": {"@": {"inactive": True}, "host-name": "r1"}},
        set_output="set system host-name r1\ndeactivate system\n",
        why="The deactivate line follows the content it deactivates.",
    ),
    Shape(
        "an-inactive-leaf-beside-an-active-one",
        {
            SET: "set system host-name r1\ndeactivate system host-name\n"
            "set system domain-name example.com\n",
            STRUCTURED: "system {\n    inactive: host-name r1;\n    domain-name example.com;\n}\n",
            JSON: _json(
                {
                    "system": {
                        "host-name": "r1",
                        "@host-name": {"inactive": True},
                        "domain-name": "example.com",
                    }
                }
            ),
        },
        ir={
            "system": {
                "host-name": "r1",
                "@host-name": {"inactive": True},
                "domain-name": "example.com",
            }
        },
        set_output="set system host-name r1\ndeactivate system host-name\n"
        "set system domain-name example.com\n",
        why="A curly tag on a leaf marks the leaf, not its container.",
    ),
    Shape(
        "uninterpreted-annotation-content",
        {
            JSON: _json(
                {
                    "system": {
                        "@": {
                            "inactive": True,
                            "comment": "/* managed by ansible */",
                            "junos:commit-seconds": "1500000000",
                            "junos:commit-user": "admin",
                        },
                        "host-name": "r1",
                    }
                }
            )
        },
        set_output="set system host-name r1\ndeactivate system\n",
        read_back={
            w: {"system": {"@": {"inactive": True}, "host-name": "r1"}} for w in (SET, STRUCTURED)
        },
        never_written={w: ("junos:", "managed by ansible") for w in (SET, STRUCTURED)},
        why="JSON and YAML pass comments and junos: metadata through verbatim; set and "
        "structured output keep only the tags they have a spelling for.",
    ),
    Shape(
        "a-container-annotation-as-a-sibling-key",
        {JSON: _json({"system": {"host-name": "r1"}, "@system": {"inactive": True}})},
        ir={"system": {"host-name": "r1"}, "@system": {"inactive": True}},
        set_output="set system host-name r1\ndeactivate system\n",
        read_back={
            w: {"system": {"@": {"inactive": True}, "host-name": "r1"}} for w in (SET, STRUCTURED)
        },
        why="The JSON reader keeps a sibling `@system` as given; set and structured "
        "input write the container's own `@`.",
    ),
    Shape(
        "an-inactive-interface",
        {
            SET: "set interfaces ge-0/0/0 description uplink\ndeactivate interfaces ge-0/0/0\n",
            STRUCTURED: "interfaces {\n    inactive: ge-0/0/0 {\n        description uplink;\n"
            "    }\n}\n",
        },
        ir={
            "interfaces": {
                "interface": [
                    {"@": {"inactive": True}, "name": "ge-0/0/0", "description": "uplink"}
                ]
            }
        },
        set_output="set interfaces ge-0/0/0 description uplink\ndeactivate interfaces ge-0/0/0\n",
    ),
    Shape(
        "a-quoted-value-that-reads-like-a-tag",
        {
            SET: 'set interfaces ge-0/0/0 description "inactive: do not use"\n',
            STRUCTURED: "interfaces {\n    ge-0/0/0 {\n"
            '        description "inactive: do not use";\n'
            "    }\n}\n",
        },
        ir={
            "interfaces": {
                "interface": [{"name": "ge-0/0/0", "description": "inactive: do not use"}]
            }
        },
        set_output='set interfaces ge-0/0/0 description "inactive: do not use"\n',
        why="A tag word inside a quoted value is the value.",
    ),
    Shape(
        "a-quoted-value-that-reads-like-a-tagged-route",
        {
            STRUCTURED: _nest(
                ["interfaces", "xe-0/0/0"], '        description "inactive: route 10.0.0.0/8";\n'
            )
        },
        ir={
            "interfaces": {
                "interface": [{"name": "xe-0/0/0", "description": "inactive: route 10.0.0.0/8"}]
            }
        },
        why="meta-tag-placement test challenge.",
    ),
)

# ── delete ───────────────────────────────────────────────────────────
#
# Set output writes `delete <path>` after the content; structured output
# cannot carry a delete and drops it with a note (tests/unit/convert/
# test_delete_operation.py checks the note).

_SERVICES_DELETED = {"system": {"services": {"@": {"operation": "delete"}, "ssh": [None]}}}

_add(
    Shape(
        "a-deleted-container",
        {
            SET: "set system services ssh\ndelete system services\n",
            STRUCTURED: "system {\n    delete: services {\n        ssh;\n    }\n}\n",
            JSON: _json(_SERVICES_DELETED),
        },
        ir=_SERVICES_DELETED,
        set_output="set system services ssh\ndelete system services\n",
        read_back={STRUCTURED: {"system": {"services": {"ssh": [None]}}}},
        never_written={STRUCTURED: ("delete",)},
    ),
    Shape(
        "a-deleted-container-with-a-null-flag-in-yaml",
        {
            YAML: "configuration:\n  system:\n    services:\n      '@':\n"
            "        operation: delete\n      ssh: null\n"
        },
        ir={"system": {"services": {"@": {"operation": "delete"}, "ssh": None}}},
        set_output="set system services ssh\ndelete system services\n",
        read_back={SET: _SERVICES_DELETED, STRUCTURED: {"system": {"services": {"ssh": [None]}}}},
        never_written={STRUCTURED: ("delete",)},
        why="The YAML reader keeps `ssh: null` as given; set input writes the flag `[null]`.",
    ),
    Shape(
        "a-deleted-leaf",
        {
            SET: "set system host-name router1\ndelete system host-name\n",
            STRUCTURED: "system {\n    delete: host-name router1;\n}\n",
            JSON: _json(
                {"system": {"host-name": "router1", "@host-name": {"operation": "delete"}}}
            ),
        },
        ir={"system": {"host-name": "router1", "@host-name": {"operation": "delete"}}},
        set_output="set system host-name router1\ndelete system host-name\n",
        read_back={STRUCTURED: {"system": {"host-name": "router1"}}},
        never_written={STRUCTURED: ("delete",)},
    ),
    Shape(
        "a-statement-set-then-deleted",
        {SET: "set system services ssh\ndelete system services ssh"},
        ir={"system": {"services": {"ssh": {"@": {"operation": "delete"}}}}},
        set_output="delete system services ssh\n",
        read_back={STRUCTURED: {}},
        never_written={STRUCTURED: ("delete", "ssh")},
        why="The delete replaces what the line before it set.",
    ),
    Shape(
        "a-delete-with-nothing-under-it",
        {
            SET: "delete system ntp\n",
            JSON: _json({"system": {"ntp": {"@": {"operation": "delete"}}}}),
        },
        ir={"system": {"ntp": {"@": {"operation": "delete"}}}},
        set_output="delete system ntp\n",
        read_back={STRUCTURED: {}},
        never_written={STRUCTURED: ("delete",)},
        why="Only the delete line: no `set` for an empty node.",
    ),
    Shape(
        "a-delete-after-the-content-it-deletes",
        {
            SET: "set system ntp server 10.0.0.1\ndelete system ntp\n",
            JSON: _json(
                {
                    "system": {
                        "ntp": {"@": {"operation": "delete"}, "server": [{"name": "10.0.0.1"}]}
                    }
                }
            ),
        },
        ir={"system": {"ntp": {"@": {"operation": "delete"}, "server": [{"name": "10.0.0.1"}]}}},
        set_output="set system ntp server 10.0.0.1\ndelete system ntp\n",
        read_back={STRUCTURED: {"system": {"ntp": {"server": [{"name": "10.0.0.1"}]}}}},
        never_written={STRUCTURED: ("delete",)},
    ),
)

# ── Meta tags: where a tag lands ─────────────────────────────────────
#
# Device evidence (23.2R2-S7.5, deactivate6.txt) and the specs under
# openspec/specs/conversion/{curly-meta-tags,tag-acceptance,meta-tags}/. Each
# set source was a hand-written set -> structured -> set round trip in
# tests/unit/convert/test_meta_tags.py or the meta-tag-placement and
# xml-inactive-leaf test challenges.

_add(
    Shape(
        "a-one-line-route-with-apply-groups",
        {
            SET: "set routing-options rib inet6.0 bgp-static route ::/0 apply-groups G_LOC\n"
            "set routing-options rib inet6.0 bgp-static route ::/0 apply-groups G_DEF\n"
            "deactivate routing-options rib inet6.0 bgp-static route ::/0\n",
            STRUCTURED: _nest(
                ["routing-options", "rib inet6.0", "bgp-static"],
                "            inactive: route ::/0 apply-groups [ G_LOC G_DEF ];\n",
            ),
            JSON: _json(
                {"routing-options": {"rib": [{"name": "inet6.0", "bgp-static": _ROUTE_V6}]}}
            ),
            XML: _xml(
                "<routing-options><rib><name>inet6.0</name><bgp-static>"
                '<route inactive="inactive"><name>::/0</name>'
                "<apply-groups>G_LOC</apply-groups><apply-groups>G_DEF</apply-groups>"
                "</route></bgp-static></rib></routing-options>"
            ),
        },
        ir={"routing-options": {"rib": [{"name": "inet6.0", "bgp-static": _ROUTE_V6}]}},
        why="`inactive: route ::/0 apply-groups [ … ];` is `<route inactive=…>` (23.2R2): "
        "curly input once tagged the last token instead of the route. Spec "
        "conversion/curly-meta-tags (meta-tag-placement).",
    ),
    Shape(
        "a-protected-route",
        {
            SET: "set routing-options static route 0.0.0.0/0 next-hop 10.0.0.1\n"
            "protect routing-options static route 0.0.0.0/0\n",
            STRUCTURED: _nest(
                ["routing-options", "static"],
                "        protect: route 0.0.0.0/0 next-hop 10.0.0.1;\n",
            ),
            JSON: _json(
                {
                    "routing-options": {
                        "static": {
                            "route": [
                                {
                                    "@": {"protect": True},
                                    "name": "0.0.0.0/0",
                                    "next-hop": ["10.0.0.1"],
                                }
                            ]
                        }
                    }
                }
            ),
            XML: _xml(
                "<routing-options><static>"
                '<route protect="protect"><name>0.0.0.0/0</name><next-hop>10.0.0.1</next-hop>'
                "</route></static></routing-options>"
            ),
        },
        ir={
            "routing-options": {
                "static": {
                    "route": [
                        {
                            "@": {"protect": "protect"},
                            "name": "0.0.0.0/0",
                            "next-hop": ["10.0.0.1"],
                        }
                    ]
                }
            }
        },
        why="`protect: route … next-hop …;` is `<route protect=…>` (23.2R2): XML input once "
        'dropped `protect`. A JSON `"protect": true` reads as the set spelling. Spec '
        "conversion/tag-acceptance (meta-tag-placement).",
    ),
    Shape(
        "an-inactive-next-hop",
        {
            SET: "set routing-options static route 0.0.0.0/0 next-hop 10.0.0.1\n"
            "deactivate routing-options static route 0.0.0.0/0 next-hop\n"
        },
    ),
    Shape(
        "an-inactive-family-inet",
        {
            SET: "set interfaces xe-0/0/0 unit 751 family inet filter input FILTER-V4\n"
            "set interfaces xe-0/0/0 unit 751 family inet address 198.51.100.1/24\n"
            "deactivate interfaces xe-0/0/0 unit 751 family inet\n",
            STRUCTURED: _nest(
                ["interfaces", "xe-0/0/0", "unit 751"],
                "            inactive: family inet {\n"
                "                filter {\n                    input FILTER-V4;\n"
                "                }\n                address 198.51.100.1/24;\n            }\n",
            ),
            JSON: _json(_unit_751({"family": {"inet": _INET_INACTIVE}})),
            XML: _xml(
                "<interfaces><interface><name>xe-0/0/0</name>"
                '<unit><name>751</name><family><inet inactive="inactive">'
                "<filter><input><filter-name>FILTER-V4</filter-name></input></filter>"
                "<address><name>198.51.100.1/24</name></address>"
                "</inet></family></unit></interface></interfaces>"
            ),
        },
        ir=_unit_751({"family": {"inet": _INET_INACTIVE}}),
        why="`inactive: family inet {` is `<inet inactive=…>` (23.2R2). Spec "
        "conversion/curly-meta-tags (meta-tag-placement).",
    ),
    Shape(
        "a-protected-family-with-an-inactive-address",
        {
            SET: "set interfaces xe-0/0/0 unit 0 family inet address 10.0.0.1/24\n"
            "deactivate interfaces xe-0/0/0 unit 0 family inet address 10.0.0.1/24\n"
            "protect interfaces xe-0/0/0 unit 0 family inet\n",
            XML: _xml(
                "<interfaces><interface><name>xe-0/0/0</name><unit><name>0</name>"
                '<family><inet protect="protect"><address inactive="inactive">'
                "<name>10.0.0.1/24</name></address></inet></family>"
                "</unit></interface></interfaces>"
            ),
            STRUCTURED: _nest(
                ["interfaces", "xe-0/0/0", "unit 0"],
                "            protect: family inet {\n"
                "                inactive: address 10.0.0.1/24;\n            }\n",
            ),
        },
        why="deactivate6.txt: `protect: family inet { inactive: address …; }`, `<inet protect>`.",
    ),
    Shape(
        "an-inactive-leaf-and-unit",
        {
            SET: "set interfaces xe-0/0/0 unit 751 vlan-id 751\n"
            "deactivate interfaces xe-0/0/0 unit 751 vlan-id\n"
            "deactivate interfaces xe-0/0/0 unit 751\n",
            STRUCTURED: _nest(
                ["interfaces", "xe-0/0/0"],
                "        inactive: unit 751 {\n            inactive: vlan-id 751;\n        }\n",
            ),
            JSON: _json(_unit_751({"@": {"inactive": True}, **_VLAN_ID_INACTIVE})),
            XML: _xml(
                "<interfaces><interface><name>xe-0/0/0</name>"
                '<unit inactive="inactive"><name>751</name>'
                '<vlan-id inactive="inactive">751</vlan-id>'
                "</unit></interface></interfaces>"
            ),
        },
        ir=_unit_751({"@": {"inactive": True}, **_VLAN_ID_INACTIVE}),
        why="`deactivate … unit 751 vlan-id`, then the unit (23.2R2). Spec "
        "conversion/meta-tags (xml-inactive-leaf).",
    ),
    Shape(
        "an-inactive-route-filter-entry",
        {
            SET: "set policy-options policy-statement P1 term T1 from "
            "route-filter 198.51.100.0/24 exact accept\n"
            "deactivate policy-options policy-statement P1 term T1 from "
            "route-filter 198.51.100.0/24 exact\n"
        },
    ),
    Shape(
        "an-inactive-accept-under-then",
        {
            SET: "set policy-options policy-statement P1 term T1 then accept\n"
            "deactivate policy-options policy-statement P1 term T1 then accept\n"
        },
    ),
    Shape(
        "protect-and-inactive-on-one-route",
        {
            SET: "set routing-options static route 0.0.0.0/0 next-hop 10.0.0.1\n"
            "protect routing-options static route 0.0.0.0/0\n"
            "deactivate routing-options static route 0.0.0.0/0\n"
        },
    ),
    Shape(
        "a-route-and-its-next-hop-both-inactive",
        {
            SET: "set routing-options static route 0.0.0.0/0 next-hop 10.0.0.1\n"
            "deactivate routing-options static route 0.0.0.0/0\n"
            "deactivate routing-options static route 0.0.0.0/0 next-hop\n"
        },
    ),
    Shape(
        "a-route-filter-entry-and-its-action-inactive",
        {
            SET: "set policy-options policy-statement P1 term T1 from "
            "route-filter 198.51.100.0/24 exact accept\n"
            "deactivate policy-options policy-statement P1 term T1 from "
            "route-filter 198.51.100.0/24 exact accept\n"
            "deactivate policy-options policy-statement P1 term T1 from "
            "route-filter 198.51.100.0/24 exact\n"
        },
    ),
    Shape(
        "a-family-inet-with-its-one-child-inactive",
        {
            SET: "set interfaces xe-0/0/0 unit 0 family inet dhcp\n"
            "deactivate interfaces xe-0/0/0 unit 0 family inet dhcp\n"
        },
    ),
    Shape(
        "two-families-one-protected-one-inactive",
        {
            SET: "set interfaces xe-0/0/0 unit 0 family inet address 10.0.0.1/24\n"
            "set interfaces xe-0/0/0 unit 0 family inet6 address 2001:db8::1/64\n"
            "protect interfaces xe-0/0/0 unit 0 family inet\n"
            "deactivate interfaces xe-0/0/0 unit 0 family inet6\n"
        },
    ),
    Shape(
        "then-and-its-one-child-inactive",
        {
            SET: "set policy-options policy-statement P1 term T1 then accept\n"
            "deactivate policy-options policy-statement P1 term T1 then\n"
            "deactivate policy-options policy-statement P1 term T1 then accept\n"
        },
    ),
    Shape(
        "an-inactive-group",
        {SET: "set groups G_LOC system host-name router1\ndeactivate groups G_LOC\n"},
    ),
    Shape(
        "an-inactive-firewall-from",
        {
            SET: "set firewall family inet filter FILTER-V4 term T1 from protocol tcp\n"
            "set firewall family inet filter FILTER-V4 term T1 then accept\n"
            "deactivate firewall family inet filter FILTER-V4 term T1 from\n"
        },
    ),
    Shape(
        "an-xml-leaf-with-protect-and-inactive",
        {
            XML: _xml(
                '<system><host-name protect="protect" inactive="inactive">router1'
                "</host-name></system>"
            ),
            SET: "set system host-name router1\ndeactivate system host-name\n"
            "protect system host-name\n",
        },
    ),
)

# A tag on a whole list (set `deactivate system name-server`, JSON
# `"@name-server"`). Structured output once wrote it on the first entry's
# line, which reads back as that entry's tag.

_add(
    Shape(
        "a-whole-list-of-name-servers-inactive",
        {
            SET: "set system name-server 192.168.0.1\nset system name-server 192.168.0.2\n"
            "deactivate system name-server\n"
        },
    ),
    Shape(
        "a-whole-list-of-static-routes-protected",
        {
            SET: "set routing-options static route 0.0.0.0/0 next-hop 10.0.0.1\n"
            "set routing-options static route 198.51.100.0/24 discard\n"
            "protect routing-options static route\n"
        },
    ),
    Shape(
        "a-whole-list-of-one-name-server-inactive",
        {SET: "set system name-server 192.168.0.1\ndeactivate system name-server\n"},
    ),
    Shape(
        "a-whole-one-line-route-filter-list-inactive",
        {
            SET: "set policy-options policy-statement P1 term T1 from "
            "route-filter 198.51.100.0/24 exact accept\n"
            "deactivate policy-options policy-statement P1 term T1 from route-filter\n"
        },
    ),
)

# Leaf-lists: a tag on the whole leaf-list. Device (deactivate6.txt,
# 23.2R2-S7.5): after `deactivate policy-options community C1 members` the
# curly display is `inactive: members [ … ];`, set writes one `deactivate …
# members` after both values, XML tags every value, JSON one `@members`.

_COMMUNITY_INACTIVE = (
    "set policy-options community C1 members 64496:1\n"
    "set policy-options community C1 members 64496:2\n"
    "deactivate policy-options community C1 members\n"
)

_add(
    Shape(
        "an-inactive-leaf-list",
        {
            SET: _COMMUNITY_INACTIVE,
            XML: _xml(
                "<policy-options><community><name>C1</name>"
                '<members inactive="inactive">64496:1</members>'
                '<members inactive="inactive">64496:2</members>'
                "</community></policy-options>"
            ),
            STRUCTURED: _nest(
                ["policy-options", "community C1"],
                "        inactive: members [ 64496:1 64496:2 ];\n",
            ),
        },
        set_output=_COMMUNITY_INACTIVE,
        why="deactivate6.txt: the device's curly, set and XML of one inactive leaf-list.",
    ),
    Shape(
        "a-protected-leaf-list",
        {
            SET: "set policy-options community C1 members 64496:1\n"
            "set policy-options community C1 members 64496:2\n"
            "protect policy-options community C1 members\n"
        },
    ),
    Shape(
        "an-inactive-leaf-list-of-next-hops",
        {
            SET: "set routing-options static route 0.0.0.0/0 next-hop 10.0.0.1\n"
            "set routing-options static route 0.0.0.0/0 next-hop 10.0.0.2\n"
            "deactivate routing-options static route 0.0.0.0/0 next-hop\n"
        },
    ),
    Shape(
        "an-inactive-leaf-list-of-vlan-members",
        {
            SET: "set interfaces xe-0/0/0 unit 0 family ethernet-switching vlan members V10\n"
            "set interfaces xe-0/0/0 unit 0 family ethernet-switching vlan members V20\n"
            "deactivate interfaces xe-0/0/0 unit 0 family ethernet-switching vlan members\n"
        },
    ),
    Shape(
        "an-inactive-leaf-list-of-one-value",
        {
            XML: _xml(
                "<policy-options><community><name>C1</name>"
                '<members inactive="inactive">64496:1</members></community></policy-options>'
            ),
            SET: "set policy-options community C1 members 64496:1\n"
            "deactivate policy-options community C1 members\n",
            JSON: _json(
                {
                    "policy-options": {
                        "community": [
                            {"name": "C1", "members": ["64496:1"], "@members": {"inactive": True}}
                        ]
                    }
                }
            ),
        },
    ),
)

# A list whose entries have no children: the device prints it as a block of
# entry names (`source-prefix-list { PL1; PL2; }`; the 23.2R2 re-export uses
# this layout throughout). A tag on one entry leads that entry's line inside
# the block; a tag on the keyword's line is the whole list's.

_FILTER_FROM = ["firewall", "family inet", "filter FILTER-V4", "term T1", "from"]
_FILTER_FROM_SET = "firewall family inet filter FILTER-V4 term T1 from"


def _block_list(path: list[str], set_path: str, tagged: str, other: str) -> Shape:
    """A list block with its first entry inactive, curly and set."""
    pad = "    " * len(path)
    return Shape(
        f"an-inactive-entry-in-a-{path[-1].split()[0]}-block",
        {
            SET: f"set {set_path} {tagged}\nset {set_path} {other}\n"
            f"deactivate {set_path} {tagged}\n",
            STRUCTURED: _nest(path, f"{pad}inactive: {tagged};\n{pad}{other};\n"),
        },
    )


_add(
    _block_list(
        [*_FILTER_FROM, "source-prefix-list"],
        f"{_FILTER_FROM_SET} source-prefix-list",
        "PL1",
        "PL2",
    ),
    _block_list(
        [*_FILTER_FROM, "source-address"],
        f"{_FILTER_FROM_SET} source-address",
        "198.51.100.0/24",
        "192.168.0.0/16",
    ),
    _block_list(["system", "name-server"], "system name-server", "192.168.0.1", "192.168.0.2"),
    _block_list(
        ["snmp", "community public", "clients"],
        "snmp community public clients",
        "10.0.0.0/8",
        "192.168.0.0/16",
    ),
    Shape(
        "an-inactive-entry-in-a-transparent-list-block",
        {
            SET: "set policy-options prefix-list PL1 198.51.100.0/24\n"
            "set policy-options prefix-list PL1 192.168.0.0/16\n"
            "deactivate policy-options prefix-list PL1 198.51.100.0/24\n",
            STRUCTURED: _nest(
                ["policy-options", "prefix-list PL1"],
                "        inactive: 198.51.100.0/24;\n        192.168.0.0/16;\n",
            ),
        },
        why="`prefix-list PL1 { inactive: 198.51.100.0/24; }`: a transparent list key.",
    ),
    Shape(
        "a-tag-on-a-bare-list-keyword",
        {
            SET: f"set {_FILTER_FROM_SET} source-prefix-list PL1\n"
            f"set {_FILTER_FROM_SET} source-prefix-list PL2\n"
            f"deactivate {_FILTER_FROM_SET} source-prefix-list\n"
            f"deactivate {_FILTER_FROM_SET} source-prefix-list PL2\n",
            STRUCTURED: _nest(
                _FILTER_FROM,
                "                    inactive: source-prefix-list {\n"
                "                        PL1;\n                        inactive: PL2;\n"
                "                    }\n",
            ),
        },
        why="`inactive: source-prefix-list { PL1; }` is `deactivate … source-prefix-list`, "
        "as `inactive: routing-instance { R1 {…} }` is `deactivate … routing-instance` "
        "(deactivate6.txt); a tag on an entry's line is the entry's.",
    ),
)

# ── XML: an inactive element that is empty or wrapped ────────────────
#
# openspec/specs/conversion/meta-tags/ (xml-inactive-leaf). A childless XML
# element is a presence flag or an empty container; set and structured input
# give a container with nothing in it `{"@": {...}}`.

_add(
    Shape(
        "an-empty-inactive-protocols-container",
        {
            XML: _xml('<protocols><lldp inactive="inactive"/></protocols>'),
            SET: "set protocols lldp\ndeactivate protocols lldp\n",
        },
        set_output="set protocols lldp\ndeactivate protocols lldp\n",
    ),
    Shape(
        "an-empty-inactive-system-container",
        {
            XML: _xml('<system><services inactive="inactive"/></system>'),
            SET: "set system services\ndeactivate system services\n",
        },
        set_output="set system services\ndeactivate system services\n",
    ),
    Shape(
        "an-inactive-disable-flag",
        {
            SET: "set interfaces xe-0/0/0 disable\ndeactivate interfaces xe-0/0/0 disable\n",
            XML: _xml(
                "<interfaces><interface><name>xe-0/0/0</name>"
                '<disable inactive="inactive"/></interface></interfaces>'
            ),
            JSON: _json(
                {
                    "interfaces": {
                        "interface": [
                            {"name": "xe-0/0/0", "disable": [None], "@disable": {"inactive": True}}
                        ]
                    }
                }
            ),
        },
        set_output="set interfaces xe-0/0/0 disable\ndeactivate interfaces xe-0/0/0 disable\n",
        why="`disable` is one spelling of the tree's `enable-disable`, so it has no node of "
        "its own: XML read it as an empty container, and set and structured output dropped "
        "its tag, so the interface loaded disabled.",
    ),
    Shape(
        "an-inactive-flag-under-a-container",
        {SET: "set protocols lldp disable\ndeactivate protocols lldp disable\n"},
        why="Under a container, structured output merged the flag into its parent's line: "
        "alone, `protocols inactive: lldp disable;`, a line the device rejects.",
    ),
    Shape(
        "an-inactive-flag-under-a-container-beside-a-sibling",
        {
            SET: "set protocols lldp interface all\nset protocols lldp disable\n"
            "deactivate protocols lldp disable\n"
        },
        why="Beside a sibling, structured output wrote `lldp disable;` without the tag, and "
        "LLDP loaded disabled.",
    ),
    Shape(
        "an-inactive-leaf-the-attribute-namespaced",
        {
            XML: '<configuration xmlns:junos="http://xml.juniper.net/junos/23.2R2/junos">'
            '<system><host-name junos:inactive="inactive">router1</host-name></system>'
            "</configuration>",
            SET: "set system host-name router1\ndeactivate system host-name\n",
        },
        ir={"system": {"host-name": "router1", "@host-name": {"inactive": True}}},
    ),
    Shape(
        "an-inactive-leaf-inside-undocumented",
        {
            XML: _xml(
                '<system><undocumented><host-name inactive="inactive">router1</host-name>'
                "</undocumented></system>"
            ),
        },
        ir={"system": {"host-name": "router1", "@host-name": {"inactive": True}}},
    ),
)

# ── Shapes the schema once rejected in junoscfg's own output ─────────
#
# tests/contract/test_round_trip_validates.py: each was a separate cause of the
# JSON and YAML schemas rejecting the converter's output.

_add(
    Shape(
        "a-named-list-key",
        {SET: "set interfaces ge-0/0/0 mtu 9192\n"},
        why='Rendered with its "name" key.',
    ),
    Shape(
        "a-statement-switch-off",
        {SET: "set interfaces ge-0/0/0 disable\n"},
    ),
    Shape(
        "a-statement-switch-on",
        {SET: "set interfaces ge-0/0/0 enable\n"},
    ),
    Shape(
        "a-presence-flag",
        {SET: "set protocols ospf area 0.0.0.0 interface lo0.0 passive\n"},
        why="Rendered as null.",
    ),
    Shape(
        "a-bare-container",
        {SET: "set system services netconf ssh\n"},
        why="Rendered as null.",
    ),
    Shape(
        "a-universal-statement",
        {SET: "set system apply-groups GLOBAL\n"},
    ),
    Shape(
        "a-flat-entry-key",
        {
            SET: "set policy-options policy-statement P term T from route-filter "
            "10.0.0.0/8 orlonger\n"
        },
        why='Rendered with its "address" key.',
    ),
    Shape(
        "an-overridden-entry-key",
        {SET: "set policy-options policy-statement P term T then community add COMM-A\n"},
    ),
)

# ── Keyed entries: a list entry is keyed by its declared fields ──────
#
# openspec/specs/conversion/entry-keys/ (identifier-key-fields). A list entry
# is keyed by the fields the XSD declares, in order: `as-path-neighbors` by
# `list-type` and `list-name`, route-filter by its address and match type,
# `then community` by its action and `community-name`. The shapes are the
# ones a vMX on 23.2R2-S7.5 displayed for the same statements
# (`tests/data/captures/keyed-entries-*`, checked against the device in
# `tests/corpus/test_device_truth.py`); the values are synthetic. A row's
# YAML is the JSON source's YAML rendering, which the writer law reads back.

_TERM = "set policy-options policy-statement SAMPLE-POLICY term T1"
_TERM_CRUMBS = ["policy-options", "policy-statement SAMPLE-POLICY", "term T1"]
_AS_LIST_NAME = "SAMPLE-AS-LIST"
_AS_LIST = {"list-type": "as-list", "list-name": _AS_LIST_NAME}


def _curly(crumbs: list[str], statements: str) -> str:
    """*statements* nested inside *crumbs*, one brace level each."""
    text = statements
    for crumb in reversed(crumbs):
        inner = "\n".join("    " + line for line in text.splitlines())
        text = f"{crumb} {{\n{inner}\n}}"
    return text + "\n"


def _device_xml(config: dict[str, Any]) -> str:
    """The device's XML for an IR: a list repeats its element, `[null]` is an
    empty element, and an entry's `@` its attributes."""

    def element(name: str, value: Any) -> str:
        if isinstance(value, list):
            return "".join(f"<{name}/>" if item is None else element(name, item) for item in value)
        if isinstance(value, dict):
            attributes = "".join(f' {key}="{key}"' for key in value.get("@", {}))
            inner = "".join(element(k, v) for k, v in value.items() if not k.startswith("@"))
            return f"<{name}{attributes}>{inner}</{name}>"
        text = str(value).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        return f"<{name}>{text}</{name}>"

    return element("configuration", config)


def _in_term(**term: Any) -> dict[str, Any]:
    """Term T1 of SAMPLE-POLICY holding *term*."""
    return {
        "policy-options": {
            "policy-statement": [{"name": "SAMPLE-POLICY", "term": [{"name": "T1", **term}]}]
        }
    }


def _keyed(
    name: str,
    lines: list[str],
    curly: str,
    config: dict[str, Any],
    *,
    xml: bool = True,
    **extra: Any,
) -> Shape:
    """A keyed entry as set *lines*, *curly*, JSON and XML: one IR, the same set lines."""
    sources = {SET: "\n".join(lines) + "\n", STRUCTURED: curly, JSON: _json(config)}
    if xml:
        sources[XML] = _device_xml(config)
    return Shape(name, sources, ir=config, set_output="\n".join(lines) + "\n", **extra)


#: Where a policy statement may stand: (set prefix, curly crumbs, wrap).
_PLACEMENTS: dict[str, tuple[str, list[str], Any]] = {
    "root": ("set", [], lambda po: {"policy-options": po}),
    "logical-system": (
        "set logical-systems SAMPLE-LS",
        ["logical-systems SAMPLE-LS"],
        lambda po: {"logical-systems": [{"name": "SAMPLE-LS", "policy-options": po}]},
    ),
    "group": (
        "set groups SAMPLE-GROUP",
        ["groups", "SAMPLE-GROUP"],
        lambda po: {"groups": [{"name": "SAMPLE-GROUP", "policy-options": po}]},
    ),
    "grouped-logical-system": (
        "set groups SAMPLE-GROUP logical-systems SAMPLE-LS",
        ["groups", "SAMPLE-GROUP", "logical-systems SAMPLE-LS"],
        lambda po: {
            "groups": [
                {
                    "name": "SAMPLE-GROUP",
                    "logical-systems": [{"name": "SAMPLE-LS", "policy-options": po}],
                }
            ]
        },
    ),
}


def _as_list_reference(slot: str, level: str, placement: str) -> Shape:
    """`<slot> as-list SAMPLE-AS-LIST` under a policy or its term, wherever a policy stands."""
    prefix, crumbs, wrap = _PLACEMENTS[placement]
    # A wildcard name where a group may hold one.
    policy = "<*>" if placement == "group" else "SAMPLE-POLICY"
    where = ["policy-options", f"policy-statement {policy}"]
    set_where = f"policy-options policy-statement {policy}"
    entry: dict[str, Any] = {"name": policy}
    body = {"from": {slot: [dict(_AS_LIST)]}}
    if level == "term":
        where.append("term T1")
        set_where += " term T1"
        entry["term"] = [{"name": "T1", **body}]
    else:
        entry.update(body)
    statement = f"{slot} as-list {_AS_LIST_NAME}"
    return _keyed(
        f"{slot}-as-list-in-a-{level}-at-{placement}",
        [f"{prefix} {set_where} from {statement}"],
        _curly([*crumbs, *where, "from"], statement + ";"),
        wrap({"policy-statement": [entry]}),
    )


_add(
    *(
        _as_list_reference(slot, level, placement)
        for slot in ("as-path-neighbors", "as-path-origins", "as-path-transits")
        for level in ("term", "policy")
        for placement in _PLACEMENTS
    )
)

_MATCH = {
    "from-event-attribute": "ping.test-owner",
    "condition": "matches",
    "to-event-attribute-value": "^uptime$",
}
_SPACED_MATCH = {**_MATCH, "to-event-attribute-value": "^up time$"}
_FILTER_ENTRY = {"address": "198.51.100.0/24", "exact": [None], "accept": [None]}

_add(
    _keyed(
        "attributes-match-keyed-by-its-three-fields",
        [
            "set event-options policy SAMPLE-EVENT-POLICY attributes-match ping.test-owner "
            'matches "^uptime$"',
            "set event-options policy SAMPLE-EVENT-POLICY attributes-match ping.test-owner "
            'matches "^up time$"',
        ],
        _curly(
            ["event-options", "policy SAMPLE-EVENT-POLICY"],
            'attributes-match ping.test-owner matches "^uptime$";\n'
            'attributes-match ping.test-owner matches "^up time$";',
        ),
        {
            "event-options": {
                "policy": [
                    {"name": "SAMPLE-EVENT-POLICY", "attributes-match": [_MATCH, _SPACED_MATCH]}
                ]
            }
        },
        why="The three fields, never a `name` or positional `_v0`/`_v1` keys.",
    ),
    *(
        _keyed(
            f"a-{slot}-entry-holds-its-action",
            [f"{_TERM} from {slot} 198.51.100.0/24 exact accept"],
            _curly([*_TERM_CRUMBS, "from"], f"{slot} 198.51.100.0/24 exact accept;"),
            _in_term(**{"from": {slot: [dict(_FILTER_ENTRY)]}}),
            ordered=True,
        )
        for slot in ("route-filter", "source-address-filter")
    ),
)

for _action in ("add", "delete"):
    _community = _in_term(then={"community": [{_action: [None], "community-name": "SAMPLE-COMM"}]})
    _add(
        _keyed(
            f"a-community-{_action}-action",
            [f"{_TERM} then community {_action} SAMPLE-COMM"],
            _curly([*_TERM_CRUMBS, "then"], f"community {_action} SAMPLE-COMM;"),
            _community,
            ordered=True,
            why="Keyed by the action, then the name, in the declared order.",
        ),
        Shape(
            f"a-community-{_action}-action-written-after-the-name",
            {SET: f"{_TERM} then community SAMPLE-COMM {_action}\n"},
            ir=_community,
            set_output=f"{_TERM} then community {_action} SAMPLE-COMM\n",
            ordered=True,
            why="The device takes the action on either side of the name and stores it first.",
        ),
    )

_add(
    Shape(
        "as-list-entries-are-told-apart-by-both-keys",
        {
            SET: f"{_TERM} from as-path-neighbors as-list {_AS_LIST_NAME}\n"
            f"{_TERM} from as-path-neighbors as-list {_AS_LIST_NAME}\n"
            f"{_TERM} from as-path-neighbors as-list-group {_AS_LIST_NAME}\n"
            f"{_TERM} from as-path-neighbors as-list SAMPLE-AS-LIST-2\n"
        },
        ir=_in_term(
            **{
                "from": {
                    "as-path-neighbors": [
                        dict(_AS_LIST),
                        {"list-type": "as-list-group", "list-name": _AS_LIST_NAME},
                        {"list-type": "as-list", "list-name": "SAMPLE-AS-LIST-2"},
                    ]
                }
            }
        ),
        why="An entry's identity is its key tuple: a repeated line is one entry.",
    ),
    Shape(
        "route-filter-entries-are-told-apart-by-address-and-match-type",
        {
            SET: f"{_TERM} from route-filter 198.51.100.0/24 exact\n"
            f"{_TERM} from route-filter 198.51.100.0/24 orlonger\n"
            f"{_TERM} from route-filter 198.51.100.0/24 exact accept\n"
        },
        ir=_in_term(
            **{
                "from": {
                    "route-filter": [
                        dict(_FILTER_ENTRY),
                        {"address": "198.51.100.0/24", "orlonger": [None]},
                    ]
                }
            }
        ),
        why="One address with two match types is two entries; the action joins its entry. "
        "The device's round-4 probe of the same shape is "
        "`tests/data/captures/keyed-entries-route-filter.*`.",
    ),
)


def _as_path_neighbors(list_type: str, name: str) -> dict[str, Any]:
    return _in_term(
        **{"from": {"as-path-neighbors": [{"list-type": list_type, "list-name": name}]}}
    )


#: A `list-name` of every shape, by row label: (the name, its set spelling).
_LIST_NAMES = {
    "a-keyword": ("as-list", "as-list"),
    "the-other-keyword": ("as-list-group", "as-list-group"),
    "a-number": ("64496", "64496"),
    "a-space": ("SAMPLE AS LIST", '"SAMPLE AS LIST"'),
    "punctuation": ("S_1.2-x", "S_1.2-x"),
}

_add(
    *(
        Shape(
            f"device-json-{list_type}-named-with-{label}",
            {JSON: _json(_as_path_neighbors(list_type, name))},
            ir=_as_path_neighbors(list_type, name),
            set_output=f"{_TERM} from as-path-neighbors {list_type} {spelled}\n",
            why="Device JSON to one set line and back, over both enum values and every "
            "shape a `list-name` takes.",
        )
        for list_type in ("as-list", "as-list-group")
        for label, (name, spelled) in {
            **_LIST_NAMES,
            # `as-list SAMPLE-AS-LIST` from JSON is a source of the row
            # as-path-neighbors-as-list-in-a-term-at-root.
            **(
                {"a-plain-name": (_AS_LIST_NAME, _AS_LIST_NAME)}
                if list_type == "as-list-group"
                else {}
            ),
        }.items()
    )
)

_EVERY_KIND = [
    f"{_TERM} from as-path-neighbors as-list SAMPLE-AS-LIST-2",
    f"{_TERM} from as-path-neighbors as-list-group {_AS_LIST_NAME}",
    f"{_TERM} from as-path-neighbors as-list {_AS_LIST_NAME}",
    f"{_TERM} from route-filter 198.51.100.128/25 orlonger",
    f"{_TERM} from route-filter 198.51.100.0/24 exact accept",
    f"{_TERM} then community delete SAMPLE-COMM-2",
    f"{_TERM} then community add SAMPLE-COMM",
    "set event-options policy SAMPLE-EVENT-POLICY attributes-match ping.test-owner "
    'matches "^up time$"',
]
_EVERY_KIND_TERM = {
    "from": {
        "as-path-neighbors": [
            {"list-type": "as-list", "list-name": "SAMPLE-AS-LIST-2"},
            {"list-type": "as-list-group", "list-name": _AS_LIST_NAME},
            dict(_AS_LIST),
        ],
        "route-filter": [
            {"address": "198.51.100.128/25", "orlonger": [None]},
            dict(_FILTER_ENTRY),
        ],
    },
    "then": {
        "community": [
            {"delete": [None], "community-name": "SAMPLE-COMM-2"},
            {"add": [None], "community-name": "SAMPLE-COMM"},
        ]
    },
}
_DEVICE_KEYED = {
    **_in_term(
        **{
            "from": {
                "as-path-neighbors": [dict(_AS_LIST)],
                "route-filter": [dict(_FILTER_ENTRY)],
                "source-address-filter": [dict(_FILTER_ENTRY)],
            },
            "then": {"community": [{"add": [None], "community-name": "SAMPLE-COMM"}]},
        }
    ),
    "event-options": {"policy": [{"name": "SAMPLE-EVENT-POLICY", "attributes-match": [_MATCH]}]},
}

_add(
    Shape(
        "keyed-entries-of-every-kind",
        {SET: "\n".join(_EVERY_KIND) + "\n"},
        ir={
            **_in_term(**_EVERY_KIND_TERM),
            "event-options": {
                "policy": [{"name": "SAMPLE-EVENT-POLICY", "attributes-match": [_SPACED_MATCH]}]
            },
        },
        set_output="\n".join(_EVERY_KIND) + "\n",
        why="Every writer's output reads back as the IR, with the entries' order kept.",
    ),
    Shape(
        "keyed-entries-as-the-device-writes-them",
        {JSON: _json(_DEVICE_KEYED), XML: _device_xml(_DEVICE_KEYED)},
        ir=_DEVICE_KEYED,
        set_output=f"{_TERM} from as-path-neighbors as-list {_AS_LIST_NAME}\n"
        f"{_TERM} from route-filter 198.51.100.0/24 exact accept\n"
        f"{_TERM} from source-address-filter 198.51.100.0/24 exact accept\n"
        f"{_TERM} then community add SAMPLE-COMM\n"
        "set event-options policy SAMPLE-EVENT-POLICY attributes-match ping.test-owner "
        'matches "^uptime$"\n',
        why="JSON and XML input write the device's set lines.",
    ),
    Shape(
        "keyed-entries-in-structured-output",
        {
            SET: f"{_TERM} from as-path-neighbors as-list {_AS_LIST_NAME}\n"
            f"{_TERM} from as-path-origins as-list-group SAMPLE-AS-LIST-GROUP\n"
            f"{_TERM} from route-filter 198.51.100.0/24 exact accept\n"
            f"{_TERM} from source-address-filter 198.51.100.0/24 exact accept\n"
            f"{_TERM} then community add SAMPLE-COMM\n"
            "set event-options policy SAMPLE-EVENT-POLICY attributes-match ping.test-owner "
            'matches "^uptime$"'
        },
        written={
            STRUCTURED: (
                f"as-path-neighbors as-list {_AS_LIST_NAME};",
                "as-path-origins as-list-group SAMPLE-AS-LIST-GROUP;",
                "route-filter 198.51.100.0/24 exact accept;",
                "source-address-filter 198.51.100.0/24 exact accept;",
                "community add SAMPLE-COMM;",
                'attributes-match ping.test-owner matches "^uptime$";',
            )
        },
        never_written={STRUCTURED: ("list-type", "list-name")},
        why="Structured output writes an entry's keys as its values, in the declared order, "
        "never by their field names.",
    ),
)

_INACTIVE_ENTRY = _in_term(
    **{"from": {"as-path-neighbors": [{"@": {"inactive": True}, **_AS_LIST}]}}
)
_PROTECTED_ENTRY = _in_term(
    **{"from": {"as-path-neighbors": [{"@": {"protect": "protect"}, **_AS_LIST}]}}
)

_add(
    _keyed(
        "an-inactive-keyed-entry",
        [
            f"{_TERM} from as-path-neighbors as-list {_AS_LIST_NAME}",
            f"deactivate {_TERM[4:]} from as-path-neighbors as-list {_AS_LIST_NAME}",
        ],
        _curly([*_TERM_CRUMBS, "from"], f"inactive: as-path-neighbors as-list {_AS_LIST_NAME};"),
        _INACTIVE_ENTRY,
    ),
    _keyed(
        "a-protected-keyed-entry",
        [
            f"{_TERM} from as-path-neighbors as-list {_AS_LIST_NAME}",
            f"protect {_TERM[4:]} from as-path-neighbors as-list {_AS_LIST_NAME}",
        ],
        _curly([*_TERM_CRUMBS, "from"], f"protect: as-path-neighbors as-list {_AS_LIST_NAME};"),
        _PROTECTED_ENTRY,
    ),
    Shape(
        "an-empty-keyed-list",
        {JSON: _json(_in_term(**{"from": {"as-path-neighbors": []}, "then": {"accept": [None]}}))},
        set_output=f"{_TERM} then accept\n",
        read_back={w: _in_term(then={"accept": [None]}) for w in (SET, STRUCTURED)},
        why="No device writes it, and no output invents an entry: set and structured "
        "output write nothing for it.",
    ),
)

# ── Statements kept whole ────────────────────────────────────────────

_BARE_BESIDE_PLACED = {"apply-groups": ["SAMPLE-GROUP"], UNPLACED_RECORD: {"apply-groups": [None]}}
_LEAF_WITHOUT_VALUE = {"system": {"host-name": "router1", UNPLACED_RECORD: {"host-name": [None]}}}
_QUOTED_MACRO = 'apply-macro 12345 "KADJBF KU!H" balks XXXXX'
_QUOTED_UNKNOWN = 'nonsense "alpha beta" gamma'
_KEPT_QUOTES = {
    "groups": [{"name": "SAMPLE-GROUP", UNPLACED_RECORD: {_QUOTED_MACRO: [None]}}],
    "interfaces": {"interface": [{"name": "ge-0/0/0", UNPLACED_RECORD: {_QUOTED_UNKNOWN: [None]}}]},
}

_add(
    Shape(
        "a-bare-keyword-beside-the-node-it-names",
        {
            SET: "set apply-groups SAMPLE-GROUP\nset apply-groups\n",
            STRUCTURED: "apply-groups;\napply-groups SAMPLE-GROUP;\n",
            JSON: _json(_BARE_BESIDE_PLACED),
            YAML: "configuration:\n  apply-groups:\n  - SAMPLE-GROUP\n"
            "  junoscfg:unplaced:\n    apply-groups:\n    - null\n",
        },
        ir=_BARE_BESIDE_PLACED,
        written={SET: ("set apply-groups SAMPLE-GROUP\n", "set apply-groups\n")},
        valid=False,
        why="OPEN-2: the device rejects a bare `set apply-groups` (corpus CORRECTLY_REJECTED); "
        "kept as its parent's key, it vanished after the valid one, and before it the valid "
        "one was kept and reported too. Change kept-whole-statements.",
    ),
    Shape(
        "a-leaf-without-its-value-beside-its-value",
        {
            SET: "set system host-name\nset system host-name router1\n",
            STRUCTURED: "system {\n    host-name router1;\n    host-name;\n}\n",
            JSON: _json(_LEAF_WITHOUT_VALUE),
            YAML: "configuration:\n  system:\n    host-name: router1\n"
            "    junoscfg:unplaced:\n      host-name:\n      - null\n",
        },
        ir=_LEAF_WITHOUT_VALUE,
        written={SET: ("set system host-name router1\n", "set system host-name\n")},
        valid=False,
        why="NEW-C1: a leaf with no value is a statement the device rejects (corpus "
        "CORRECTLY_REJECTED); it replaced router1 with null and was written back without a "
        "word. Change kept-whole-statements.",
    ),
    Shape(
        "a-kept-statement-keeps-its-quotes",
        {
            SET: f"set groups SAMPLE-GROUP {_QUOTED_MACRO}\n"
            f"set interfaces ge-0/0/0 {_QUOTED_UNKNOWN}\n",
            STRUCTURED: f"groups {{\n    SAMPLE-GROUP {{\n        {_QUOTED_MACRO};\n    }}\n}}\n"
            f"interfaces {{\n    ge-0/0/0 {{\n        {_QUOTED_UNKNOWN};\n    }}\n}}\n",
            JSON: _json(_KEPT_QUOTES),
            YAML: "configuration:\n  groups:\n  - name: SAMPLE-GROUP\n    junoscfg:unplaced:\n"
            f"      '{_QUOTED_MACRO}': [null]\n"
            "  interfaces:\n    interface:\n    - name: ge-0/0/0\n      junoscfg:unplaced:\n"
            f"        '{_QUOTED_UNKNOWN}': [null]\n",
        },
        ir=_KEPT_QUOTES,
        written={
            SET: (
                f"set groups SAMPLE-GROUP {_QUOTED_MACRO}\n",
                f"set interfaces ge-0/0/0 {_QUOTED_UNKNOWN}\n",
            ),
            STRUCTURED: (f"{_QUOTED_MACRO};", f"{_QUOTED_UNKNOWN};"),
        },
        valid=False,
        why="OPEN-3: a kept statement is its original tokens; joined after their quotes were "
        'stripped, `"KADJBF KU!H"` became two words and read back as another statement. '
        "The device rejects a fourth apply-macro value (vMX 23.2R2-S7.5). Change "
        "kept-whole-statements.",
    ),
)

# ── Statements valid at every level ──────────────────────────────────
#
# The tree declares `apply-groups`, `apply-groups-except`, `apply-flags` and
# `apply-macro` once, on the root; every reader and writer resolves them below
# it through `junoscfg.display.schema_child` (spec
# schema-pipeline/universal-statements, change universal-statements-from-tree).

_GR_OMIT = {
    "groups": [
        {
            "name": "GR-OMIT",
            "system": {"apply-flags": {"omit": [None]}, "location": {"building": "omit probe"}},
        }
    ]
}
_BELOW_THE_ROOT = {
    "apply-groups": ["SAMPLE-GROUP"],
    "system": {
        "apply-groups": ["SAMPLE-GROUP", "SAMPLE-GROUP-2"],
        "apply-groups-except": ["SAMPLE-GROUP-3"],
        "apply-macro": [{"name": "M1", "data": [{"name": "k1", "value": "v1"}]}],
        "apply-flags": {"omit": [None]},
        "host-name": "router1",
    },
    "interfaces": {
        "interface": [
            {"name": "ge-0/0/0", "apply-groups": ["SAMPLE-GROUP"], "description": "uplink"}
        ]
    },
}

_add(
    Shape(
        "apply-flags-omit-as-the-device-writes-it",
        {
            SET: "set groups GR-OMIT system apply-flags omit\n"
            'set groups GR-OMIT system location building "omit probe"\n',
            STRUCTURED: _nest(
                ["groups", "GR-OMIT", "system"],
                "            apply-flags omit;\n            location {\n"
                '                building "omit probe";\n            }\n',
            ),
            JSON: _json(_GR_OMIT),
            YAML: "configuration:\n  groups:\n  - name: GR-OMIT\n    system:\n"
            "      apply-flags:\n        omit:\n        - null\n"
            "      location:\n        building: omit probe\n",
            XML: _xml(
                "<groups><name>GR-OMIT</name><system><apply-flags><omit/></apply-flags>"
                "<location><building>omit probe</building></location></system></groups>"
            ),
        },
        ir=_GR_OMIT,
        set_output="set groups GR-OMIT system apply-flags omit\n"
        'set groups GR-OMIT system location building "omit probe"\n',
        why="DEV-V2: the device writes `apply-flags` as a container holding the flag `omit` "
        "(group GR-OMIT, tests/data/device/synthetic/{vmx-23.2R2-S7.5,qfx5120-25.2R2-S1.5}/"
        "junoscfg-oracle.{set,xml,json}.gz). The tree had a leaf, so set and curly input kept "
        "the line whole and reported it. Change universal-statements-from-tree.",
    ),
    Shape(
        "universal-statements-below-the-root",
        {
            SET: "set apply-groups SAMPLE-GROUP\n"
            "set system apply-groups SAMPLE-GROUP\n"
            "set system apply-groups SAMPLE-GROUP-2\n"
            "set system apply-groups-except SAMPLE-GROUP-3\n"
            "set system apply-macro M1 k1 v1\n"
            "set system apply-flags omit\n"
            "set system host-name router1\n"
            "set interfaces ge-0/0/0 apply-groups SAMPLE-GROUP\n"
            "set interfaces ge-0/0/0 description uplink\n",
            STRUCTURED: "apply-groups SAMPLE-GROUP;\n"
            "system {\n    apply-groups [ SAMPLE-GROUP SAMPLE-GROUP-2 ];\n"
            "    apply-groups-except SAMPLE-GROUP-3;\n"
            "    apply-macro M1 {\n        k1 v1;\n    }\n"
            "    apply-flags omit;\n    host-name router1;\n}\n"
            "interfaces {\n    ge-0/0/0 {\n        apply-groups SAMPLE-GROUP;\n"
            "        description uplink;\n    }\n}\n",
            JSON: _json(_BELOW_THE_ROOT),
            # One group as a scalar, as YAML may hold it: read as its list.
            YAML: "configuration:\n  apply-groups: SAMPLE-GROUP\n  system:\n"
            "    apply-groups:\n    - SAMPLE-GROUP\n    - SAMPLE-GROUP-2\n"
            "    apply-groups-except: SAMPLE-GROUP-3\n"
            "    apply-macro:\n    - name: M1\n      data:\n      - name: k1\n        value: v1\n"
            "    apply-flags:\n      omit:\n      - null\n    host-name: router1\n"
            "  interfaces:\n    interface:\n    - name: ge-0/0/0\n"
            "      apply-groups: SAMPLE-GROUP\n      description: uplink\n",
            XML: _xml(
                "<apply-groups>SAMPLE-GROUP</apply-groups>"
                "<system><apply-groups>SAMPLE-GROUP</apply-groups>"
                "<apply-groups>SAMPLE-GROUP-2</apply-groups>"
                "<apply-groups-except>SAMPLE-GROUP-3</apply-groups-except>"
                "<apply-macro><name>M1</name><data><name>k1</name><value>v1</value></data>"
                "</apply-macro><apply-flags><omit/></apply-flags>"
                "<host-name>router1</host-name></system>"
                "<interfaces><interface><name>ge-0/0/0</name>"
                "<apply-groups>SAMPLE-GROUP</apply-groups><description>uplink</description>"
                "</interface></interfaces>"
            ),
        },
        ir=_BELOW_THE_ROOT,
        set_output="set apply-groups SAMPLE-GROUP\n"
        "set system apply-groups SAMPLE-GROUP\n"
        "set system apply-groups SAMPLE-GROUP-2\n"
        "set system apply-groups-except SAMPLE-GROUP-3\n"
        "set system apply-macro M1 k1 v1\n"
        "set system apply-flags omit\n"
        "set system host-name router1\n"
        "set interfaces ge-0/0/0 apply-groups SAMPLE-GROUP\n"
        "set interfaces ge-0/0/0 description uplink\n",
        why="ARCH-C06: below the root the four statements met no node; XML and YAML read a "
        "nested `apply-groups` with one group as a scalar where set input and the top level "
        "read a list (the device's JSON writes a list at every level, e.g. "
        '`"apply-groups" : ["GR-MACRO"]` in tests/data/device/synthetic/vmx-23.2R2-S7.5/'
        "junoscfg-oracle.json.gz). Change universal-statements-from-tree.",
    ),
)

# Value quoting by the leaf's type (spec conversion/value-quoting; change
# value-quoting-by-type). The device writes a policy-algebra expression bare
# and keeps a quoted policy name's quotes in its XML and JSON; it escapes `"`
# inside a quoted value (vMX 23.2R2-S7.5 and QFX5120 25.2R2-S1.5
# junoscfg-oracle.{set,conf,json,xml}.gz, vMX synthetic-probes.{set,xml,json}.gz).
_NEIGHBOR = ["protocols", "bgp", "group G", "neighbor 192.168.1.2"]
_NEIGHBOR_SET = "set protocols bgp group G neighbor 192.168.1.2"
_NEIGHBOR_XML = (
    "<protocols><bgp><group><name>G</name><neighbor><name>192.168.1.2</name>"
    "{}</neighbor></group></bgp></protocols>"
)


def _neighbor(**leaves: Any) -> dict[str, Any]:
    """BGP group G's neighbor 192.168.1.2 holding *leaves*."""
    return {
        "protocols": {
            "bgp": {"group": [{"name": "G", "neighbor": [{"name": "192.168.1.2", **leaves}]}]}
        }
    }


def _neighbor_yaml(lines: str) -> str:
    return (
        "configuration:\n  protocols:\n    bgp:\n      group:\n      - name: G\n"
        "        neighbor:\n        - name: 192.168.1.2\n" + lines
    )


def _description(value: str) -> dict[str, Any]:
    """Interface ge-0/0/0 whose description is *value*."""
    return {"interfaces": {"interface": [{"name": "ge-0/0/0", "description": value}]}}


def _quoting_row(name: str, value: str, spelled: str, why: str, **sources: str) -> Shape:
    """A description *value*, written *spelled* in set and curly, read from each source.

    *sources* add hand-written spellings (`structured`, `set`) around the same
    value: a one-line block, comments. A statement across lines is refused
    whatever it quotes (`tests/unit/display/test_set_converter.py`, probe P7).
    """
    line = f"set interfaces ge-0/0/0 description {spelled}\n"
    return Shape(
        name,
        {
            SET: sources.get("set", line),
            STRUCTURED: sources.get(
                "structured", _nest(["interfaces", "ge-0/0/0"], f"        description {spelled};\n")
            ),
            JSON: _json(_description(value)),
            YAML: "configuration:\n  interfaces:\n    interface:\n    - name: ge-0/0/0\n"
            f"      description: {json.dumps(value)}\n",
            XML: _xml(
                "<interfaces><interface><name>ge-0/0/0</name>"
                f"<description>{xml_escape(value)}</description></interface></interfaces>"
            ),
        },
        ir=_description(value),
        set_output=line,
        why=why,
    )


_add(
    Shape(
        "a-one-term-policy-expression",
        {
            SET: f"{_NEIGHBOR_SET} import ( P-A )\n{_NEIGHBOR_SET} export ( P-A || P-B )\n",
            STRUCTURED: _nest(
                _NEIGHBOR,
                "                import ( P-A );\n                export ( P-A || P-B );\n",
            ),
            JSON: _json(_neighbor(**{"import": ["( P-A )"], "export": ["( P-A || P-B )"]})),
            YAML: _neighbor_yaml(
                "          import:\n          - ( P-A )\n"
                "          export:\n          - ( P-A || P-B )\n"
            ),
            XML: _xml(
                _NEIGHBOR_XML.format("<import>( P-A )</import><export>( P-A || P-B )</export>")
            ),
        },
        ir=_neighbor(**{"import": ["( P-A )"], "export": ["( P-A || P-B )"]}),
        set_output=f"{_NEIGHBOR_SET} import ( P-A )\n{_NEIGHBOR_SET} export ( P-A || P-B )\n",
        why="DEV-4: `( P-A )` is an expression of one term, written bare as the device "
        "writes it; quoted it names a policy called `( P-A )`.",
    ),
    Shape(
        "a-quoted-policy-name-that-reads-as-an-expression",
        {
            SET: f'{_NEIGHBOR_SET} import "( P-A && P-B )"\n{_NEIGHBOR_SET} export "( P-A )"\n',
            STRUCTURED: _nest(
                _NEIGHBOR,
                '                import "( P-A && P-B )";\n                export "( P-A )";\n',
            ),
            JSON: _json(_neighbor(**{"import": ['"( P-A && P-B )"'], "export": ['"( P-A )"']})),
            YAML: _neighbor_yaml(
                "          import:\n          - '\"( P-A && P-B )\"'\n"
                "          export:\n          - '\"( P-A )\"'\n"
            ),
            XML: _xml(
                _NEIGHBOR_XML.format(
                    '<import>"( P-A &amp;&amp; P-B )"</import><export>"( P-A )"</export>'
                )
            ),
        },
        ir=_neighbor(**{"import": ['"( P-A && P-B )"'], "export": ['"( P-A )"']}),
        set_output=f'{_NEIGHBOR_SET} import "( P-A && P-B )"\n{_NEIGHBOR_SET} export "( P-A )"\n',
        why="DEV-5, DEV-6: the device keeps a quoted policy name's quotes in its own XML and "
        "JSON (synthetic-probes); set input read it as an expression, and the value from XML "
        'or JSON was written `""( P-A )""`.',
    ),
    Shape(
        "a-quoted-plain-policy-name",
        {
            SET: f'{_NEIGHBOR_SET} import "P-1"\n',
            STRUCTURED: _nest(_NEIGHBOR, '                import "P-1";\n'),
            JSON: _json(_neighbor(**{"import": ["P-1"]})),
        },
        ir=_neighbor(**{"import": ["P-1"]}),
        set_output=f"{_NEIGHBOR_SET} import P-1\n",
        why="A quoted name that cannot read as an expression reads without its quotes, as "
        "before; what the device holds for it is probe P12.",
    ),
    Shape(
        "a-policy-chain-holding-a-quoted-name",
        {
            SET: f'{_NEIGHBOR_SET} import "( P-A && P-B )"\n{_NEIGHBOR_SET} import P-C\n',
            STRUCTURED: _nest(_NEIGHBOR, '                import [ "( P-A && P-B )" P-C ];\n'),
            JSON: _json(_neighbor(**{"import": ['"( P-A && P-B )"', "P-C"]})),
            YAML: _neighbor_yaml(
                "          import:\n          - '\"( P-A && P-B )\"'\n          - P-C\n"
            ),
            XML: _xml(
                _NEIGHBOR_XML.format(
                    '<import>"( P-A &amp;&amp; P-B )"</import><import>P-C</import>'
                )
            ),
        },
        ir=_neighbor(**{"import": ['"( P-A && P-B )"', "P-C"]}),
        set_output=f'{_NEIGHBOR_SET} import "( P-A && P-B )"\n{_NEIGHBOR_SET} import P-C\n',
        written={STRUCTURED: ('import [ "( P-A && P-B )" P-C ];',)},
        why="Test/Challenge F1: a policy chain is a leaf-list; curly writes it `[ ... ]` "
        "with each value the device's token (dict_walker's bracket path), and reads the "
        "quoted name inside it as the name. A chain holding a bare expression is "
        "specification challenge SC1 (curly splits it; probe P13).",
    ),
    Shape(
        "a-policy-chain-of-names",
        {
            SET: f'{_NEIGHBOR_SET} import P-A\n{_NEIGHBOR_SET} import "P 1"\n',
            STRUCTURED: _nest(_NEIGHBOR, '                import [ P-A "P 1" ];\n'),
            JSON: _json(_neighbor(**{"import": ["P-A", "P 1"]})),
            XML: _xml(_NEIGHBOR_XML.format("<import>P-A</import><import>P 1</import>")),
        },
        ir=_neighbor(**{"import": ["P-A", "P 1"]}),
        set_output=f'{_NEIGHBOR_SET} import P-A\n{_NEIGHBOR_SET} import "P 1"\n',
        written={STRUCTURED: ('import [ P-A "P 1" ];',)},
        why="Test/Challenge F1: a chain of plain names, one needing quotes (pin: as on the base).",
    ),
    _quoting_row(
        "a-value-holding-an-escaped-quote",
        'uplink to sw1 "core"',
        '"uplink to sw1 \\"core\\""',
        "DEV-7, NEW-C6, ANON-P4: the inner quotes were written bare and the line did not "
        'load; the device writes `\\"` (junoscfg-oracle.set.gz).',
    ),
    _quoting_row(
        "an-expression-in-a-description",
        "( P-A && P-B )",
        '"( P-A && P-B )"',
        "A description is text: the look of an expression no longer drops its quotes.",
    ),
    _quoting_row(
        "an-escaped-quote-in-a-one-line-block",
        'a "b" {c}; d',
        '"a \\"b\\" {c}; d"',
        "Lexing row: a one-line curly block.",
        structured='interfaces { ge-0/0/0 { description "a \\"b\\" {c}; d"; } }\n',
    ),
    _quoting_row(
        "an-escaped-quote-beside-comments",
        'after "comments" ; { }',
        '"after \\"comments\\" ; { }"',
        "Lexing row: comments holding `;`, `{`, `}` and quotes around the value.",
        structured='interfaces {\n    /* a comment; { } "quoted" */\n    ge-0/0/0 {\n'
        '        # a line comment; { } "q"\n'
        '        description "after \\"comments\\" ; { }"; /* trailing "x"; } */\n'
        "    }\n}\n",
        set='# a comment; { } "q"\n'
        'set interfaces ge-0/0/0 description "after \\"comments\\" ; { }"\n',
    ),
    _quoting_row(
        "an-escaped-quote-in-a-template",
        '${SITE} "core" uplink',
        '"${SITE} \\"core\\" uplink"',
        "Lexing row: a template `${SITE}`, as Juniper's published snippets use.",
    ),
    _quoting_row(
        "an-escaped-quote-in-prose",
        'Don\'t "panic": call ops, 24/7 (not && never) #1',
        '"Don\'t \\"panic\\": call ops, 24/7 (not && never) #1"',
        "Lexing row: prose with an apostrophe, a colon, a hash and an expression's operators.",
    ),
    _quoting_row(
        "address-forms-inside-words-beside-an-escaped-quote",
        'peer "10.255.0.1:100" target:198.51.100.1:5 host:198.51.100.2 lo_198.51.100.3',
        '"peer \\"10.255.0.1:100\\" target:198.51.100.1:5 host:198.51.100.2 lo_198.51.100.3"',
        "Lexing row: address-form values inside words.",
    ),
)


# Review F2: these complete expressions passed every input reader and exact
# baseline round trips, but the canonical-kept-statement guard refused them.
# Single-space word layout is not an expression requirement.
for _row_name, _expression in (
    ("a-compact-quoted-policy-name-expression", '("P 1" && P-B)'),
    ("a-nested-compact-quoted-policy-name-expression", '(("P 1") && P-B)'),
    ("an-expression-preserving-spaces-inside-a-quoted-name", '( "P  1" && P-B )'),
):
    _expression_ir = _neighbor(**{"import": [_expression]})
    _add(
        Shape(
            _row_name,
            {
                SET: f"{_NEIGHBOR_SET} import {_expression}\n",
                STRUCTURED: _nest(_NEIGHBOR, f"        import {_expression};\n"),
                JSON: _json(_expression_ir),
                YAML: _neighbor_yaml(f"          import: [{json.dumps(_expression)}]\n"),
                XML: _xml(_NEIGHBOR_XML.format(f"<import>{xml_escape(_expression)}</import>")),
            },
            ir=_expression_ir,
            set_output=f"{_NEIGHBOR_SET} import {_expression}\n",
            why="Review F2: complete expression quoted names can touch parentheses; "
            "meaningful spaces inside a quoted name stay unchanged.",
        )
    )


# Keyworded leaves and hierarchical triggers, with positional syntax controls.
# NEW-A-S1/DEV-2/DEV-3/NEW-B2/NEW-B3. Only overload and radius timeout
# are device-backed; other rows assert the corrected-schema preservation law.
def _leaf_hint_xml(config: dict[str, Any]) -> str:
    """Spell these scalar/list-entry fixtures as XML without using a product writer."""
    parts = []
    for key, value in config.items():
        for item in value if isinstance(value, list) else [value]:
            body = (
                _leaf_hint_xml(item)
                if isinstance(item, dict)
                else ""
                if item is None
                else xml_escape(str(item))
            )
            parts.append(f"<{key}>{body}</{key}>")
    return "".join(parts)


for _name, _set, _curly, _ir, _why in (
    (
        "a-keyworded-overload-timeout",
        "set protocols isis overload timeout 300",
        "protocols { isis { overload { timeout 300; } } }",
        {"protocols": {"isis": {"overload": {"timeout": "300"}}}},
        "DEV-2: junoscfg-oracle.set.gz, vMX23.2R2-S7.5 and QFX5120 25.2R2-S1.5, "
        "tests/data/device/synthetic/: overload timeout retains its keyword.",
    ),
    (
        "a-keyworded-radius-timeout",
        "set access radius-server 192.168.50.10 timeout 10",
        "access { radius-server 192.168.50.10 { timeout 10; } }",
        {"access": {"radius-server": [{"name": "192.168.50.10", "timeout": "10"}]}},
        "DEV-3: same committed vMX/QFX junoscfg-oracle captures retain radius timeout.",
    ),
    (
        "a-keyworded-as-path-path",
        'set routing-options static route 10.1.0.0/16 as-path path "64496 64497"',
        'routing-options { static { route 10.1.0.0/16 { as-path { path "64496 64497"; } } } }',
        {
            "routing-options": {
                "static": {"route": [{"name": "10.1.0.0/16", "as-path": {"path": "64496 64497"}}]}
            }
        },
        "NEW-B2: XSD keyworded path, independently expected IR; no device claim.",
    ),
    (
        "a-keyworded-capture-filename",
        "set forwarding-options packet-capture file filename pcap1",
        "forwarding-options { packet-capture { file { filename pcap1; } } }",
        {"forwarding-options": {"packet-capture": {"file": {"filename": "pcap1"}}}},
        "NEW-B2: XSD keyworded filename; no device claim.",
    ),
    (
        "a-keyworded-syslog-limit",
        "set services service-set SS1 syslog cache limit 100",
        "services { service-set SS1 { syslog { cache { limit 100; } } } }",
        {"services": {"service-set": [{"name": "SS1", "syslog": {"cache": {"limit": "100"}}}]}},
        "NEW-B2: XSD keyworded limit; no device claim.",
    ),
    (
        "an-optical-trigger-with-nested-content",
        "set interfaces et-0/0/0 otn-options trigger oc-los hold-time up 100",
        "interfaces { et-0/0/0 { otn-options { trigger { oc-los { hold-time { up 100; } } } } } }",
        {
            "interfaces": {
                "interface": [
                    {
                        "name": "et-0/0/0",
                        "otn-options": {"trigger": {"oc-los": {"hold-time": {"up": "100"}}}},
                    }
                ]
            }
        },
        "NEW-B3: XSD hierarchical otn trigger; no device claim.",
    ),
    (
        "a-sonet-trigger-with-nested-content",
        "set interfaces so-0/0/0 sonet-options trigger lol hold-time up 100",
        "interfaces { so-0/0/0 { sonet-options { trigger { lol { hold-time { up 100; } } } } } }",
        {
            "interfaces": {
                "interface": [
                    {
                        "name": "so-0/0/0",
                        "sonet-options": {"trigger": {"lol": {"hold-time": {"up": "100"}}}},
                    }
                ]
            }
        },
        "NEW-B3: XSD hierarchical sonet trigger; no device claim.",
    ),
    (
        "a-positional-trace-filename-with-siblings",
        "set protocols bgp traceoptions file bgp-log size 10m files 10",
        "protocols { bgp { traceoptions { file bgp-log size 10m files 10; } } }",
        {
            "protocols": {
                "bgp": {
                    "traceoptions": {"file": {"filename": "bgp-log", "size": "10m", "files": "10"}}
                }
            }
        },
        "Negative control: genuine nokeyword filename retains its positional spelling.",
    ),
    (
        "a-positional-maximum-prefixes-limit-with-siblings",
        "set routing-options maximum-prefixes 3000000 threshold 50 log-interval 5",
        "routing-options { maximum-prefixes 3000000 threshold 50 log-interval 5; }",
        {
            "routing-options": {
                "maximum-prefixes": {"limit": "3000000", "threshold": "50", "log-interval": "5"}
            }
        },
        "Negative control: genuine nokeyword limit retains its positional spelling.",
    ),
):
    _add(
        Shape(
            _name,
            {
                SET: _set + "\n",
                STRUCTURED: _curly + "\n",
                JSON: _json(_ir),
                YAML: _json(_ir),
                XML: _xml(_leaf_hint_xml(_ir)),
            },
            ir=_ir,
            written={} if _name.startswith("a-positional-") else {SET: (_set,)},
            why=_why,
        )
    )


_event_trigger_ir = {
    "event-options": {
        "policy": [
            {"name": "P", "within": [{"name": "1800", "trigger": {"after": [None], "count": "1"}}]}
        ]
    }
}
_add(
    Shape(
        "an-event-trigger-with-its-supported-count",
        {
            SET: "set event-options policy P within 1800 trigger after 1\n",
            STRUCTURED: "event-options { policy P { within 1800 { trigger after 1; } } }\n",
            JSON: _json(_event_trigger_ir),
            YAML: _json(_event_trigger_ir),
            XML: _xml(_leaf_hint_xml(_event_trigger_ir)),
        },
        ir=_event_trigger_ir,
        why="DEV-V6 carry: preserve currently supported after/count behavior; "
        "the Set-input device equivalence probe remains unresolved.",
    )
)


# Keyed single-entry lists: device-backed paths; singleton cardinality is not
# permission for a second entry. Makeover #11, DEV-1/8/9, NEW-B4, OPEN-21.
_port_entry_ir = {
    "forwarding-options": {
        "port-mirroring": {
            "family": {
                "inet": {
                    "output": {
                        "routing-instance": [
                            {"name": "VRF-A", "ip-address": "10.0.0.1", "@": {"inactive": True}}
                        ]
                    }
                }
            }
        }
    }
}
_port_prefix = "forwarding-options port-mirroring family inet output routing-instance VRF-A"
_add(
    Shape(
        "a-keyed-singleton-port-mirroring-entry",
        {
            SET: f"set {_port_prefix} ip-address 10.0.0.1\ndeactivate {_port_prefix}\n",
            STRUCTURED: "forwarding-options { port-mirroring { family inet { output { "
            "routing-instance { inactive: VRF-A { ip-address 10.0.0.1; } } } } } }\n",
            JSON: _json(_port_entry_ir),
            YAML: _json(_port_entry_ir),
            XML: _xml(
                "<forwarding-options><port-mirroring><family><inet><output>"
                '<routing-instance inactive="inactive"><name>VRF-A</name>'
                "<ip-address>10.0.0.1</ip-address></routing-instance>"
                "</output></inet></family></port-mirroring></forwarding-options>"
            ),
        },
        ir=_port_entry_ir,
        set_output=f"set {_port_prefix} ip-address 10.0.0.1\ndeactivate {_port_prefix}\n",
        why="DEV-8/9, OPEN-21, meta-tag F1: tests/data/device/synthetic/"
        "{vmx-23.2R2-S7.5,qfx5120-25.2R2-S1.5}/junoscfg-oracle captures show "
        "an inactive keyed array. vMX23.2R2-S7.5/QFX5120 25.2R2-S1.5; "
        "private deactivate6.txt supports entry tag placement only.",
    )
)
for _name, _set, _curly, _ir, _why in (
    (
        "a-keyed-singleton-srgb-range",
        "set protocols mpls label-range srgb-label-range 800000 890000",
        "protocols { mpls { label-range { srgb-label-range 800000 890000; } } }",
        {
            "protocols": {
                "mpls": {
                    "label-range": {"srgb-label-range": [{"name": "800000", "range-end": "890000"}]}
                }
            }
        },
        "NEW-B4: tests/data/device/jvd/vmx-23.2R2-S7.5/bng1_mx304 captures "
        "(synthetic JVD on vMX23.2R2-S7.5) show one range array and both values. "
        "String expected values isolate this change from numeric normalization #13.",
    ),
    (
        "a-keyed-singleton-attribute-group",
        "set protocols isis interface ge-0/0/0 level 2 application-specific "
        "attribute-group ASLA te-metric 25",
        "protocols { isis { interface ge-0/0/0 { level 2 { application-specific { "
        "attribute-group ASLA { te-metric 25; } } } } } }",
        {
            "protocols": {
                "isis": {
                    "interface": [
                        {
                            "name": "ge-0/0/0",
                            "level": [
                                {
                                    "name": "2",
                                    "application-specific": {
                                        "attribute-group": [{"name": "ASLA", "te-metric": "25"}]
                                    },
                                }
                            ],
                        }
                    ]
                }
            }
        },
        "OPEN-14: tests/data/device/jvd/vmx-23.2R2-S7.5/mdr1_acx7509 captures "
        "(synthetic JVD on vMX23.2R2-S7.5) show attribute-group arrays with child metrics.",
    ),
    (
        "a-transport-class-container-with-two-entries",
        "set routing-options transport-class name gold color 4000\n"
        "set routing-options transport-class name bronze color 6000\n"
        "set routing-options transport-class auto-create",
        "routing-options { transport-class { name gold { color 4000; } "
        "name bronze { color 6000; } auto-create; } }",
        {
            "routing-options": {
                "transport-class": {
                    "name": [
                        {"name": "gold", "color": "4000"},
                        {"name": "bronze", "color": "6000"},
                    ],
                    "auto-create": [None],
                }
            }
        },
        "DEV-1: synthetic vMX23.2R2-S7.5 and QFX5120 25.2R2-S1.5 "
        "junoscfg-oracle captures retain transport-class name entries and auto-create. "
        "The container itself is not an entry.",
    ),
    (
        "a-known-container-with-a-keyworded-name",
        "set snmp name sw1\nset snmp location lab",
        "snmp { name sw1; location lab; }",
        {"snmp": {"name": "sw1", "location": "lab"}},
        "NEW-B1 corrected-schema preservation control; no device validity claim. "
        "Keyworded name is a leaf, not an entry identifier.",
    ),
):
    _add(
        Shape(
            _name,
            {
                SET: _set + "\n",
                STRUCTURED: _curly + "\n",
                JSON: _json(_ir),
                YAML: _json(_ir),
                XML: _xml(_leaf_hint_xml(_ir)),
            },
            ir=_ir,
            written={SET: tuple(_set.splitlines())},
            why=_why,
        )
    )


#: The shapes by name, for a test that needs one row.
BY_NAME: Mapping[str, Shape] = MappingProxyType({shape.name: shape for shape in SHAPES})
assert len(BY_NAME) == len(SHAPES), "two shapes share a name"
