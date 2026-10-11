"""Every anonymize rule keeps one law, through the named surfaces.

One configuration holds a value for every rule, most of them twice, and the
catalogue names exactly which values each rule replaces in it. Each rule, run
through ``convert_config(..., anon_config=AnonymizeConfig(...))`` and through
``junoscfg convert --anonymize-*``, must:

- replace exactly its values, each with something else;
- give the same output for the same salt, every run;
- give other replacements for another salt, except where a rule numbers its
  replacements (AS numbers, plain-text secrets), which no salt changes;
- replace one value alike everywhere it appears, and change nothing else;
- give distinct values distinct replacements;
- dump a mapping that names every replacement and restores the original.

Two rules together do not overlap: a value goes to the first rule that takes
it, in the order the rows are listed, which is the order the walker tries the
rules in. Each rule replaces a value the same whether or not the other is on.

These laws used to be one copy per rule file, and revert was checked for four
rules of nine.
"""

from __future__ import annotations

import itertools
import json
import tempfile
from dataclasses import dataclass, field
from functools import cache
from pathlib import Path
from typing import TYPE_CHECKING, Any

import pytest
from click.testing import CliRunner

from junoscfg import Format, convert_config
from junoscfg.anonymize import AnonymizeConfig
from junoscfg.cli import main

if TYPE_CHECKING:
    from collections.abc import Iterator

_RSA = "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDx admin@acme"
_ED25519 = "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIExAmPlE operator@sw1"

#: One configuration with a value for every rule. "acme" and "LAX" appear in
#: values other rules own, so the sensitive-word rows contest them. The group
#: is applied at the root, in `system` and beside the interfaces, so each rule
#: is checked where the walker reaches a universal statement and a transparent
#: container's other child (change anonymize-every-placed-value: below the root
#: the walker saw no reference, and a second pass rewrote the root's again).
CONFIGURATION: dict[str, Any] = {
    "configuration": {
        "apply-groups": ["acme-base"],
        "groups": [
            {
                "name": "acme-base",
                "system": {
                    "host-name": "acme-router1",
                    "domain-name": "lax001.example.net",
                    "login": {
                        "user": [
                            {
                                "name": "admin",
                                "class": "super-user",
                                "authentication": {"encrypted-password": "$9$ExAmPlEhAsH.KEY"},
                            }
                        ]
                    },
                },
                "snmp": {"community": [{"name": "acme-ro", "authorization": "read-only"}]},
                "protocols": {
                    "bgp": {"group": [{"name": "transit", "authentication-key": "acme-secret"}]}
                },
            }
        ],
        "system": {
            "apply-groups": ["acme-base"],
            "host-name": "acme-router1",
            "domain-name": "lax001.example.net",
            "root-authentication": {
                "encrypted-password": "$6$abc123$xyzHashValueHere",
                "ssh-rsa": [{"name": _RSA}],
            },
            "login": {
                "user": [
                    {
                        "name": "admin",
                        "full-name": "acme admin",
                        "class": "super-user",
                        "authentication": {
                            "encrypted-password": "$9$ExAmPlEhAsH.KEY",
                            "ssh-rsa": [{"name": _RSA}],
                        },
                    },
                    {
                        "name": "operator",
                        "class": "read-only",
                        "authentication": {"ssh-ed25519": [{"name": _ED25519}]},
                    },
                ]
            },
            "name-server": [{"name": "203.0.114.53"}, {"name": "203.0.114.54"}],
            "ntp": {"server": [{"name": "203.0.114.53"}]},
        },
        "interfaces": {
            "apply-groups-except": ["acme-base"],
            "interface": [
                {
                    "name": "ge-0/0/0",
                    "description": "acme uplink",
                    "unit": [
                        {"name": "0", "family": {"inet": {"address": [{"name": "10.1.2.3/24"}]}}}
                    ],
                },
                {"name": "ge-0/0/1", "description": "acme uplink"},
                {"name": "ge-0/0/2", "description": "LAX002 core"},
            ],
        },
        "snmp": {
            "location": "LAX001 rack 4",
            "contact": "noc",
            "community": [
                {"name": "acme-ro", "authorization": "read-only"},
                {"name": "public-rw", "authorization": "read-write"},
            ],
        },
        "routing-options": {"autonomous-system": {"as-number": "64497"}},
        "protocols": {
            "bgp": {
                "group": [
                    {
                        "name": "acme-peers",
                        "type": "external",
                        "peer-as": "64496",
                        "authentication-key": "$9$j1Hqf3nCO1ECApBI",
                        "neighbor": [{"name": "203.0.114.1"}],
                    },
                    {
                        "name": "transit",
                        "type": "external",
                        "peer-as": "64496",
                        "authentication-key": "acme-secret",
                    },
                ]
            }
        },
    }
}


@dataclass(frozen=True)
class RuleRow:
    """One rule: how to switch it on, and what it replaces in CONFIGURATION."""

    id: str
    key: str  # its name in the dumped mapping
    config: dict[str, Any]
    flags: tuple[str, ...]
    replaces: frozenset[str]
    unsalted: frozenset[str] = field(default_factory=frozenset)


#: In the order the walker tries the rules: the first that matches a value owns it.
RULES: tuple[RuleRow, ...] = (
    RuleRow(
        "password",
        "password",
        {"passwords": True},
        ("--anonymize-passwords",),
        frozenset(
            {
                "$6$abc123$xyzHashValueHere",
                "$9$ExAmPlEhAsH.KEY",
                "$9$j1Hqf3nCO1ECApBI",
                "acme-secret",
            }
        ),
        unsalted=frozenset({"acme-secret"}),  # plain text is numbered: netconanRemoved<N>
    ),
    RuleRow(
        "ssh-key",
        "ssh_key",
        {"ssh_keys": True},
        ("--anonymize-ssh-keys",),
        frozenset({_RSA, _ED25519}),
    ),
    RuleRow(
        "ip",
        "ip",
        {"ips": True},
        ("--anonymize-ips",),
        frozenset({"203.0.114.53", "203.0.114.54", "203.0.114.1", "10.1.2.3/24"}),
    ),
    RuleRow(
        "community",
        "community",
        {"communities": True},
        ("--anonymize-communities",),
        frozenset({"acme-ro", "public-rw"}),
    ),
    RuleRow(
        "identity",
        "identity",
        {"identities": True},
        ("--anonymize-identities",),
        frozenset({"admin", "operator", "acme admin"}),
    ),
    RuleRow(
        "group",
        "group",
        {"groups": True},
        ("--anonymize-groups",),
        frozenset({"acme-base", "acme-peers", "transit"}),
    ),
    RuleRow(
        "description",
        "description",
        {"descriptions": True},
        ("--anonymize-descriptions",),
        frozenset({"acme uplink", "LAX002 core", "LAX001 rack 4", "noc"}),
    ),
    RuleRow(
        "as-number",
        "as_number",
        {"as_numbers": [64496, 64497]},
        ("--anonymize-as-numbers", "64496,64497"),
        frozenset({"64496", "64497"}),
        unsalted=frozenset({"64496", "64497"}),  # numbered from 64496 up, by design
    ),
    RuleRow(
        "sensitive-word",
        "sensitive_word",
        {"sensitive_words": ["acme"]},
        ("--anonymize-sensitive-words", "acme"),
        frozenset(
            {
                "acme-base",
                "acme-router1",
                "acme-ro",
                "acme admin",
                "acme uplink",
                "acme-peers",
                "acme-secret",
                _RSA,
            }
        ),
    ),
    RuleRow(
        "sensitive-pattern",
        "sensitive_word",
        {"sensitive_patterns": [r"LAX\d+"]},
        ("--anonymize-sensitive-patterns", r"LAX\d+"),
        frozenset({"lax001.example.net", "LAX002 core", "LAX001 rack 4"}),
    ),
)

_SOURCE = json.dumps(CONFIGURATION)
_PRECEDENCE = {row.id: n for n, row in enumerate(RULES)}


@dataclass(frozen=True)
class Run:
    """What one anonymizing conversion produced."""

    output: str
    ir: dict[str, Any]
    mapping: dict[str, dict[str, str]]
    reverted: dict[str, Any]

    @property
    def replacements(self) -> dict[str, str]:
        """Every original and its replacement, over all rules."""
        return {old: new for pairs in self.mapping.values() for old, new in pairs.items()}


def _convert(source: str, config: AnonymizeConfig | None = None) -> str:
    return convert_config(
        source, from_format=Format.JSON, to_format=Format.JSON, validate=False, anon_config=config
    )


@cache
def _baseline() -> str:
    return _convert(_SOURCE)


def _run(rows: tuple[RuleRow, ...], salt: str = "contract-salt") -> Run:
    """Anonymize CONFIGURATION with *rows* on, dump the mapping and revert with it."""
    options: dict[str, Any] = {}
    for row in rows:
        options.update(row.config)
    with tempfile.TemporaryDirectory() as scratch:
        dumped = Path(scratch) / "map.json"
        output = _convert(_SOURCE, AnonymizeConfig(salt=salt, dump_map=str(dumped), **options))
        mapping = json.loads(dumped.read_text(encoding="utf-8"))
        reverted = _convert(output, AnonymizeConfig(revert_map=str(dumped)))
    return Run(output, json.loads(output), mapping, json.loads(reverted))


@cache
def _alone(row_id: str) -> Run:
    return _run((_row(row_id),))


def _row(row_id: str) -> RuleRow:
    return next(row for row in RULES if row.id == row_id)


def _leaves(node: Any, path: tuple[Any, ...] = ()) -> Iterator[tuple[tuple[Any, ...], Any]]:
    if isinstance(node, dict):
        for key, value in node.items():
            yield from _leaves(value, (*path, key))
    elif isinstance(node, list):
        for index, value in enumerate(node):
            yield from _leaves(value, (*path, index))
    else:
        yield path, node


def _values() -> list[Any]:
    return [value for _, value in _leaves(CONFIGURATION)]


def _unexplained(run: Run) -> list[tuple[tuple[Any, ...], Any, Any]]:
    """Leaves the mapping does not explain: a value replaced otherwise, or not at all."""
    original = list(_leaves(json.loads(_baseline())))
    anonymized = list(_leaves(run.ir))
    assert [path for path, _ in original] == [path for path, _ in anonymized], "shape changed"
    table = run.replacements
    return [
        (path, before, after)
        for (path, before), (_, after) in zip(original, anonymized, strict=True)
        if after != table.get(before, before)
    ]


def _owners(rows: tuple[RuleRow, ...]) -> dict[str, set[str]]:
    """The mapping the precedence predicts: each value goes to the first row that takes it."""
    expected: dict[str, set[str]] = {}
    taken: set[str] = set()
    for row in sorted(rows, key=lambda r: _PRECEDENCE[r.id]):
        expected.setdefault(row.key, set()).update(row.replaces - taken)
        taken |= row.replaces
    return {key: values for key, values in expected.items() if values}


_IDS = [row.id for row in RULES]


@pytest.mark.parametrize("row", RULES, ids=_IDS)
class TestEveryRule:
    """The law each rule keeps on its own."""

    def test_it_replaces_exactly_its_values(self, row: RuleRow) -> None:
        run = _alone(row.id)
        assert set(run.mapping) == {row.key}
        assert set(run.mapping[row.key]) == row.replaces
        assert row.replaces <= set(_values()), "the catalogue names a value the source lacks"
        for original, replacement in run.mapping[row.key].items():
            assert replacement != original, f"{original!r} was not changed"

    def test_the_same_salt_gives_the_same_output(self, row: RuleRow) -> None:
        first, second = _run((row,), salt="same-salt"), _run((row,), salt="same-salt")
        assert first.output == second.output
        assert first.mapping == second.mapping

    def test_another_salt_gives_other_replacements(self, row: RuleRow) -> None:
        one = _run((row,), salt="salt-a").mapping[row.key]
        other = _run((row,), salt="salt-b").mapping[row.key]
        assert set(one) == set(other)
        for original in one:
            if original in row.unsalted:
                assert one[original] == other[original], f"{original!r} depends on the salt"
            else:
                assert one[original] != other[original], f"{original!r} ignores the salt"

    def test_a_value_is_replaced_alike_everywhere(self, row: RuleRow) -> None:
        values = _values()
        assert any(values.count(value) > 1 for value in row.replaces), "no value appears twice"
        assert _unexplained(_alone(row.id)) == []

    def test_distinct_values_get_distinct_replacements(self, row: RuleRow) -> None:
        replacements = list(_alone(row.id).mapping[row.key].values())
        assert len(replacements) > 1
        assert len(set(replacements)) == len(replacements)

    def test_the_dumped_mapping_restores_the_original(self, row: RuleRow) -> None:
        assert _alone(row.id).reverted == json.loads(_baseline())

    def test_the_cli_flags_keep_the_same_law(self, row: RuleRow, tmp_path: Path) -> None:
        """`--anonymize-*` with a salt gives what the library gives, and reverts."""
        dumped = tmp_path / "map.json"
        common = ["convert", "-i", "json", "-e", "json", "--no-field-validate"]
        runner = CliRunner()
        anonymized = runner.invoke(
            main,
            [*common, *row.flags, "--anonymize-salt", "contract-salt"]
            + ["--anonymize-dump-map", str(dumped)],
            input=_SOURCE,
        )
        assert anonymized.exit_code == 0, anonymized.output
        assert json.loads(anonymized.stdout) == _alone(row.id).ir
        assert json.loads(dumped.read_text(encoding="utf-8")) == _alone(row.id).mapping

        reverted = runner.invoke(
            main, [*common, "--anonymize-revert-map", str(dumped)], input=anonymized.stdout
        )
        assert reverted.exit_code == 0, reverted.output
        assert json.loads(reverted.stdout) == json.loads(_baseline())


def _pairs() -> list[Any]:
    """Every pair of rules."""
    return [
        pytest.param(first, second, id=f"{first.id}+{second.id}")
        for first, second in itertools.combinations(RULES, 2)
    ]


class TestRulesDoNotOverlap:
    """Two rules on together: each value is replaced once, by the first that takes it."""

    @pytest.mark.parametrize(("first", "second"), _pairs())
    def test_a_value_goes_to_the_first_rule_that_takes_it(
        self, first: RuleRow, second: RuleRow
    ) -> None:
        run = _run((first, second))
        assert {key: set(pairs) for key, pairs in run.mapping.items()} == _owners((first, second))
        assert _unexplained(run) == []
        assert run.reverted == json.loads(_baseline())

    @pytest.mark.parametrize(("first", "second"), _pairs())
    def test_a_rule_replaces_its_values_alike_with_another_on(
        self, first: RuleRow, second: RuleRow
    ) -> None:
        """A salted replacement does not depend on which other rule runs beside it."""
        together = _run((first, second)).mapping
        for row in (first, second):
            alone = _alone(row.id).mapping[row.key]
            for original, replacement in together.get(row.key, {}).items():
                if original in alone and original not in row.unsalted:
                    assert replacement == alone[original], (row.id, original)


class TestEveryRuleTogether:
    """Every rule on at once: the precedence chain holds and the mapping reverts."""

    @pytest.mark.parametrize(
        "rows",
        [
            pytest.param(
                tuple(row for row in RULES if not row.id.startswith("sensitive")),
                id="every-rule-but-sensitive-words",
            ),
            pytest.param(RULES, id="every-rule"),
        ],
    )
    def test_every_rule_together_reverts(self, rows: tuple[RuleRow, ...]) -> None:
        run = _run(rows)
        assert {key: set(pairs) for key, pairs in run.mapping.items()} == _owners(rows)
        assert _unexplained(run) == []
        assert run.reverted == json.loads(_baseline())
