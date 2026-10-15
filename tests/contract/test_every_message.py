"""No message of an anonymized run quotes the configuration, through any door.

An anonymized run is one whose `anon_config` enables a rule: `convert_config`,
`convert_config_result` (the `pipeline` behind them) and `junoscfg convert
--anonymize-*`. Each door below is a place a message leaves such a run: the
conversion's diagnostics, `FieldValidationError`, a refusal to read the input,
the structured writer's notes, the `anonymize:` warnings, the read notes, a
rule's Python warnings and errors, and on the command line `-v` (with `-e` and
validate-only), `--strict`, the error lines and a failure no handler expects.

Each row drives one door with a configuration every non-schema word of which
carries the marker `acme`, plus an address, and asserts of everything the run
lets out -- stderr, stdout when the run failed or only validated, Python
warnings, and an exception's whole formatted chain -- that it holds no `acme`
(any case), no dotted quad, and none of the row's other words; that it still
says what the door exists to say (its path, reason, line or count); and that
the same run without anonymization prints the door's own message.

Lesson #1 of the makeover run ("no original value may reach a diagnostic, a
warning, stderr or a ValidationError in an anonymized run"), NEW-R1, NEW-R4,
NEW-R9, NEW-R10, Test/Challenge findings F1-F5 of change anonymized-run-messages;
spec anonymization/placed-values. A word no rule replaced is an original value
too (change anonymize-every-placed-value, C12), and a replacement in a message
ties the output back to its place: messages carry neither (ruling F5).
`log_level="debug"` pairs each original with its replacement by design.

Synthetic values only, as AGENTS.md names them.
"""

from __future__ import annotations

import json
import re
import traceback
import warnings
from dataclasses import dataclass
from functools import cache
from typing import TYPE_CHECKING

import pytest
import yaml
from click.testing import CliRunner
from ipanon import PassThroughCollisionError

from junoscfg import FieldValidationError, Format, convert_config, convert_config_result
from junoscfg.anonymize import AnonymizeConfig
from junoscfg.cli import main
from tests.support.aliases import nested_yaml

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

ADDRESS = "203.0.114.9"
SALT = "s"
MARKER = "acme"
DOTTED_QUAD = re.compile(r"\b\d{1,3}(\.\d{1,3}){3}\b")


def _config(**options: object) -> AnonymizeConfig:
    return AnonymizeConfig(ips=True, salt=SALT, **options)  # type: ignore[arg-type]


@cache
def _pseudonym() -> str:
    """The address's replacement under the run's salt."""
    out = convert_config(
        f"set system name-server {ADDRESS}\n",
        from_format=Format.SET,
        to_format=Format.SET,
        anon_config=_config(),
    )
    return out.split()[-1]


def _warned(caught: list[warnings.WarningMessage]) -> str:
    """Each warning as Python prints it to stderr."""
    return "".join(
        warnings.formatwarning(w.message, w.category, w.filename, w.lineno, None) for w in caught
    )


def _said(error: BaseException) -> str:
    """The exception's own message, as Python's last traceback line shows it."""
    return "".join(traceback.format_exception_only(error))


def _chain(error: BaseException) -> str:
    """The exception as Python prints it uncaught: its whole chain."""
    return "".join(traceback.format_exception(error))


@dataclass(frozen=True)
class Door:
    """One way a message leaves a run.

    ``run(anonymized, tmp)`` returns the exit code (``None`` for the library),
    what the door said (an exception's own message, the diagnostics, stderr)
    and everything the run let out (that, Python warnings, the formatted
    chain). ``shown`` are fragments the anonymized run must still say (the
    door's meaning: path, reason, line, count), matched against what it said
    only: a traceback's frame lines say ``line 113`` too (Reviewer R3).
    ``kept`` is a fragment of the door's own message a run without
    anonymization prints; ``None`` for a door only an anonymized run opens.
    ``words`` are input words beyond the marker and the address.
    """

    run: Callable[[bool, Path], tuple[int | None, str, str]]
    shown: tuple[str, ...]
    kept: str | None
    words: tuple[str, ...] = ()


def _library(
    source: str, fmt: Format, to: Format = Format.SET, *, strict: bool = False, **options: object
) -> Callable[[bool, Path], tuple[int | None, str, str]]:
    def run(anonymized: bool, tmp: Path) -> tuple[int | None, str, str]:
        anon = _config(**options) if anonymized else None
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            try:
                result = convert_config_result(
                    source, from_format=fmt, to_format=to, strict=strict, anon_config=anon
                )
            except FieldValidationError as error:
                details = [f"{e.path} {e.message} {e.value}" for e in error.result.errors]
                said = "\n".join([_said(error), *details])
                return None, said, "\n".join([said, _chain(error), _warned(caught)])
            except (
                ValueError,
                yaml.YAMLError,
                PassThroughCollisionError,
                RuntimeError,
                TypeError,
            ) as error:
                return None, _said(error), "\n".join([_chain(error), _warned(caught)])
        said = "\n".join(d.render() for d in result.diagnostics)
        return None, said, "\n".join([said, _warned(caught)])

    return run


def _cli(
    source: str, args: list[str], *options: str, xsd: str | None = None
) -> Callable[[bool, Path], tuple[int | None, str, str]]:
    def run(anonymized: bool, tmp: Path) -> tuple[int | None, str, str]:
        flags = ["--anonymize-ips", "--anonymize-salt", SALT, *options] if anonymized else []
        extra: list[str] = []
        if xsd is not None:
            (tmp / "junos-validated.xsd").write_text(xsd, encoding="utf-8")
            extra = ["--artifacts", str(tmp)]
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            result = CliRunner().invoke(main, ["convert", *args, *extra, *flags], input=source)
        # A Python warning reaches stderr on the command line; pytest records it instead.
        said = result.stderr + _warned(caught)
        if result.exit_code != 0 or "-e" not in args:
            # stdout is the output, which carries the configuration, only on success.
            said += result.stdout
        scanned = said
        if result.exception is not None and not isinstance(result.exception, SystemExit):
            scanned += _chain(result.exception)
        return result.exit_code, said, scanned

    return run


_BRACKET = f"set system host-name [ sw1-acme {ADDRESS} ]\n"
_NO_SEMICOLON = "system {\n    host-name sw1-acme\n}\n"
_TAG_INSIDE = "system {\n    host-name {\n        inactive: sw1-acme;\n    }\n}\n"
_OPEN_QUOTE = f'system {{\n    host-name "sw1-acme {ADDRESS};\n}}\n'
_BROKEN_YAML = f"configuration:\n  system: [sw1-acme, {ADDRESS}\n"
_BROKEN_XML = "<configuration><system><host-name>sw1</host-name></sys-acme></configuration>"
_BROKEN_JSON = '{"configuration": {"system": {"host-name": "sw1-acme"'
_ENUM_WORD = "set system services ssh protocol-version v9-acme\n"
_ENUM_ADDRESS = f"set system services ssh protocol-version {ADDRESS}\n"
_ENUM_SHOWN = ("system.services.ssh.protocol-version", "must be one of [v2]")
_UNKNOWN_KEY = json.dumps({"configuration": {"system": {f"bogus-acme {ADDRESS}": None}}})
_FAMILY_TAG = json.dumps(
    {
        "configuration": {
            "protocols": {
                "bgp": {
                    "group": [
                        {
                            "name": "G-ACME",
                            "neighbor": [
                                {
                                    "name": ADDRESS,
                                    "family": {
                                        "@": {"inactive": True},
                                        "inet": {"unicast": {}},
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
_EMPTY_BLOCK = "interfaces {\n    interface-range R-ACME {\n    }\n}\n"
_XSD = """<?xml version="1.0"?>
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
 <xs:element name="configuration"><xs:complexType><xs:sequence>
  <xs:element name="system"><xs:complexType><xs:sequence>
   <xs:element name="host-name"><xs:simpleType><xs:restriction base="xs:string">
    <xs:pattern value="[a-z]+"/></xs:restriction></xs:simpleType></xs:element>
  </xs:sequence></xs:complexType></xs:element>
 </xs:sequence></xs:complexType></xs:element>
</xs:schema>"""
_XML_HOST = (
    f"<configuration><system><host-name>sw1-acme {ADDRESS}</host-name></system></configuration>"
)
_AS_ORIGINALS = tuple(str(65000 + i) for i in range(18))
_AS_REPLACEMENTS = tuple(str(64496 + i) for i in range(18))
_AS_SOURCE = "".join(
    f"set protocols bgp group G{i}-ACME peer-as {asn}\n" for i, asn in enumerate(_AS_ORIGINALS)
)
#: A wildcard with literal text the group rule renames (ANON-P3, change
#: group-wildcards-pass): reported by schema path, never by its text.
_WILDCARD = (
    "set groups GR-ACME protocols bgp group <ACME-*> hold-time 30\n"
    f"set protocols bgp group ACME-PEERS neighbor {ADDRESS}\n"
)
_WILDCARD_SHOWN = ("groups.protocols.bgp.group", "wildcard")
#: An apply-path the tree cannot read to its end, and one whose wildcard the
#: group rule cannot keep (NEW-A-N7, change anonymize-embedded-values): each
#: reported by the apply-path's schema path, never by its words.
_APPLY_PATH = (
    "set policy-options prefix-list PL-ACME apply-path "
    f'"protocols bgp bogus-acme EBGP-ACME {ADDRESS}"\n'
)
_APPLY_PATH_SHOWN = ("policy-options.prefix-list.apply-path", "1 statement(s)")
_APPLY_PATH_WILDCARD = (
    "set policy-options prefix-list PL-ACME apply-path "
    '"protocols bgp group <ACME-*> neighbor <*>"\n'
    f"set protocols bgp group ACME-PEERS neighbor {ADDRESS}\n"
)
_APPLY_PATH_WILDCARD_SHOWN = ("policy-options.prefix-list.apply-path", "selector")
_READ = ("could not be read",)
_WITHHELD = "; details withheld: the run anonymizes"
_YAML_DATE = "configuration:\n  system:\n    x-acme: 2026-10-11\n"
_YAML_CYCLE = "configuration: &a\n  system:\n    x-acme: *a\n"
_YAML_DEEP = nested_yaml(62).replace("    x: ", "    x-acme: ")
_FAILED = ("Validation: FAILED (1 error(s))", "line 1")


def _cli_collision(anonymized: bool, tmp: Path) -> tuple[int | None, str, str]:
    return _cli(
        f"set system name-server {ADDRESS}\n",
        ["-i", "set", "-e", "set"],
        "--anonymize-preserve-prefixes",
        f"{_pseudonym()}/32",
    )(anonymized, tmp)


def _library_collision(anonymized: bool, tmp: Path) -> tuple[int | None, str, str]:
    return _library(
        f"set system name-server {ADDRESS}\n",
        Format.SET,
        preserve_prefixes=[f"{_pseudonym()}/32"],
    )(anonymized, tmp)


#: door id -> the door.
DOORS: dict[str, Door] = {
    # -- the library: ConversionResult.diagnostics, raised errors, warnings ---
    "field-validation-word": Door(_library(_ENUM_WORD, Format.SET), _ENUM_SHOWN, "v9-acme"),
    "field-validation-address": Door(_library(_ENUM_ADDRESS, Format.SET), _ENUM_SHOWN, ADDRESS),
    "field-validation-strict": Door(
        _library(_ENUM_WORD, Format.SET, strict=True), _ENUM_SHOWN, "v9-acme"
    ),
    "field-validation-unplaced": Door(
        _library(_UNKNOWN_KEY, Format.JSON), ("could not be placed",), "bogus-acme"
    ),
    "unplaced-strict": Door(
        _library(_UNKNOWN_KEY, Format.JSON, strict=True), ("could not be placed",), "bogus-acme"
    ),
    "anonymize-pattern-warning": Door(
        _library(_WILDCARD, Format.SET, groups=True), _WILDCARD_SHOWN, None
    ),
    "anonymize-apply-path-warning": Door(
        _library(_APPLY_PATH, Format.SET), _APPLY_PATH_SHOWN, None, ("EBGP",)
    ),
    "anonymize-apply-path-pattern-warning": Door(
        _library(_APPLY_PATH_WILDCARD, Format.SET, groups=True), _APPLY_PATH_WILDCARD_SHOWN, None
    ),
    "read-set-bracket": Door(_library(_BRACKET, Format.SET), (*_READ, "(line 1)"), "sw1-acme"),
    "read-structured": Door(
        _library(_NO_SEMICOLON, Format.STRUCTURED), (*_READ, "(line 2)"), "sw1-acme"
    ),
    "read-structured-tag": Door(
        _library(_TAG_INSIDE, Format.STRUCTURED), (*_READ, "(line 3)"), "sw1-acme"
    ),
    "read-structured-quote": Door(
        _library(_OPEN_QUOTE, Format.STRUCTURED), (*_READ, "(line 2)"), "sw1-acme"
    ),
    "read-yaml": Door(_library(_BROKEN_YAML, Format.YAML), (*_READ, "(line 3)"), "sw1-acme"),
    "read-yaml-new": Door(
        _library(_BROKEN_YAML, Format.YAML_NEW), (*_READ, "(line 3)"), "sw1-acme"
    ),
    "read-yaml-new-date": Door(
        _library(_YAML_DATE, Format.YAML_NEW, Format.JSON), _READ, "system.x-acme"
    ),
    "read-yaml-new-cycle": Door(
        _library(_YAML_CYCLE, Format.YAML_NEW, Format.JSON), _READ, "system.x-acme"
    ),
    "read-yaml-new-deep": Door(_library(_YAML_DEEP, Format.YAML_NEW), _READ, "system.x-acme"),
    "read-yaml-cycle": Door(
        _library(_YAML_CYCLE, Format.YAML, Format.JSON), _READ, "system.x-acme"
    ),
    "read-yaml-deep": Door(_library(_YAML_DEEP, Format.YAML), _READ, "system.x-acme"),
    "read-xml": Door(_library(_BROKEN_XML, Format.XML), (*_READ, "(line 1)"), "sys-acme"),
    "read-json": Door(_library(_BROKEN_JSON, Format.JSON), (*_READ, "(line 1)"), "Expecting"),
    "read-note": Door(_library(_EMPTY_BLOCK, Format.STRUCTURED), ("empty block",), "R-ACME"),
    "structured-writer-note": Door(
        _library(_FAMILY_TAG, Format.JSON, Format.STRUCTURED), ("1 tag(s) dropped",), "G-ACME"
    ),
    "pass-through-collision": Door(
        _library_collision,
        (f"RuntimeError: the conversion failed (PassThroughCollisionError){_WITHHELD}",),
        None,
    ),
    "unexpected-failure": Door(
        _library(_YAML_DATE, Format.YAML, Format.JSON),
        (f"RuntimeError: the conversion failed (TypeError){_WITHHELD}",),
        None,
    ),
    # -- the command line: stderr, stdout of a failed or validate-only run ----
    "cli-validate-set": Door(
        _cli(f"set system bogus-acme {ADDRESS}\n", ["-i", "set", "-v", "-e", "set"]),
        _FAILED,
        "bogus-acme",
    ),
    "cli-validate-only-set": Door(
        _cli(f"set system bogus-acme {ADDRESS}\n", ["-i", "set", "-v"]), _FAILED, "bogus-acme"
    ),
    "cli-validate-only-bracket": Door(_cli(_BRACKET, ["-i", "set", "-v"]), _FAILED, "sw1-acme"),
    "cli-validate-only-line": Door(
        _cli(f"bogus-acme {ADDRESS}\n", ["-i", "set", "-v"]),
        _FAILED,
        "Unsupported command in set input on line 1",
    ),
    "cli-validate-only-structured": Door(
        _cli(f"system {{\n    bogus-acme {ADDRESS};\n}}\n", ["-i", "structured", "-v"]),
        ("Validation: FAILED (1 error(s))", "line"),
        "bogus-acme",
    ),
    "cli-validate-only-structured-refusal": Door(
        _cli(_NO_SEMICOLON, ["-i", "structured", "-v"]),
        ("Validation: FAILED (1 error(s))",),
        "sw1-acme",
    ),
    "cli-validate-only-json": Door(
        _cli(_UNKNOWN_KEY, ["-i", "json", "-v"]),
        ("Validation: FAILED (1 error(s))",),
        "bogus-acme",
    ),
    "cli-validate-only-yaml": Door(
        _cli("configuration:\n  system:\n    bogus-acme: x\n", ["-i", "yaml", "-v"]),
        ("Validation: FAILED (1 error(s))",),
        "bogus-acme",
    ),
    "cli-validate-only-yaml-parse": Door(
        _cli(_BROKEN_YAML, ["-i", "yaml", "-v"]),
        ("Validation: FAILED (1 error(s))", "line"),
        "sw1-acme",
    ),
    "cli-validate-only-schema-load": Door(
        _cli(_XML_HOST, ["-i", "xml", "-v"]), ("XSD not found",), "XSD not found"
    ),
    "cli-validate-only-xml-xsd": Door(
        _cli(_XML_HOST, ["-i", "xml", "-v"], xsd=_XSD), _FAILED, "sw1-acme"
    ),
    "cli-validate-warning": Door(
        _cli(_EMPTY_BLOCK, ["-i", "structured", "-v"]), ("empty block",), "R-ACME"
    ),
    "cli-field-validation": Door(
        _cli(_ENUM_WORD, ["-i", "set", "-e", "set"]), _ENUM_SHOWN, "v9-acme"
    ),
    "cli-strict": Door(
        _cli(_ENUM_WORD, ["-i", "set", "-e", "set", "--strict"]),
        ("Field validation: FAILED (1 error(s))", *_ENUM_SHOWN),
        "v9-acme",
    ),
    "cli-read-bracket": Door(
        _cli(_BRACKET, ["-i", "set", "-e", "json"]), (*_READ, "(line 1)"), "sw1-acme"
    ),
    "cli-read-structured": Door(
        _cli(_NO_SEMICOLON, ["-i", "structured", "-e", "set"]), (*_READ, "(line 2)"), "sw1-acme"
    ),
    "cli-read-structured-tag": Door(
        _cli(_TAG_INSIDE, ["-i", "structured", "-e", "set"]), (*_READ, "(line 3)"), "sw1-acme"
    ),
    "cli-read-yaml": Door(
        _cli(_BROKEN_YAML, ["-i", "yaml", "-e", "set"]),
        ("Invalid YAML", *_READ, "(line 3)"),
        "sw1-acme",
    ),
    "cli-read-yaml-new-date": Door(
        _cli(_YAML_DATE, ["-i", "yaml-new", "-e", "json"]), _READ, "system.x-acme"
    ),
    "cli-read-yaml-new-deep": Door(
        _cli(_YAML_DEEP, ["-i", "yaml-new", "-e", "json"]), _READ, "system.x-acme"
    ),
    "cli-read-yaml-cycle": Door(
        _cli(_YAML_CYCLE, ["-i", "yaml", "-e", "json"]), _READ, "system.x-acme"
    ),
    "cli-read-yaml-new-cycle": Door(
        _cli(_YAML_CYCLE, ["-i", "yaml-new", "-e", "json"]), _READ, "system.x-acme"
    ),
    "cli-read-yaml-deep": Door(
        _cli(_YAML_DEEP, ["-i", "yaml", "-e", "json"]), _READ, "system.x-acme"
    ),
    # A meta key: the JSON schema yaml-new is judged by rejects it, the YAML one would not.
    "cli-validate-only-yaml-new": Door(
        _cli("configuration:\n  system:\n    _meta_acme: x\n", ["-i", "yaml-new", "-v"]),
        ("Validation: FAILED (1 error(s))",),
        "_meta_acme",
    ),
    "cli-read-xml": Door(
        _cli(_BROKEN_XML, ["-i", "xml", "-e", "set"]), (*_READ, "(line 1)"), "sys-acme"
    ),
    "cli-unexpected-failure": Door(
        _cli(_YAML_DATE, ["-i", "yaml", "-e", "json"]),
        (f"Error: the conversion failed (TypeError){_WITHHELD}\n",),
        None,
    ),
    "cli-structured-writer-note": Door(
        _cli(_FAMILY_TAG, ["-i", "json", "-e", "structured"]), ("1 tag(s) dropped",), "G-ACME"
    ),
    "cli-anonymize-warning": Door(
        _cli(_UNKNOWN_KEY, ["-i", "json", "-e", "set"]),
        ("anonymize: system: 1 statement(s)",),
        "bogus-acme",
    ),
    "cli-anonymize-pattern-warning": Door(
        _cli(_WILDCARD, ["-i", "set", "-e", "set"], "--anonymize-groups"), _WILDCARD_SHOWN, None
    ),
    "cli-anonymize-apply-path-warning": Door(
        _cli(_APPLY_PATH, ["-i", "set", "-e", "set"]),
        ("anonymize: policy-options.prefix-list.apply-path: 1 statement(s)",),
        None,
        ("EBGP",),
    ),
    "cli-anonymize-apply-path-pattern-warning": Door(
        _cli(_APPLY_PATH_WILDCARD, ["-i", "set", "-e", "set"], "--anonymize-groups"),
        _APPLY_PATH_WILDCARD_SHOWN,
        None,
    ),
    "cli-pass-through-collision": Door(
        _cli_collision,
        (f"Error: the conversion failed (PassThroughCollisionError){_WITHHELD}\n",),
        None,
    ),
    "cli-as-number-warning": Door(
        _cli(
            _AS_SOURCE,
            ["-i", "set", "-e", "set"],
            "--anonymize-as-numbers",
            ",".join(_AS_ORIGINALS),
        ),
        ("exceeds the RFC 5398 documentation range",),
        None,
        (*_AS_ORIGINALS, *_AS_REPLACEMENTS),
    ),
}

_KEPT = {name: door for name, door in DOORS.items() if door.kept is not None}


class TestAnAnonymizedRunQuotesNothingOfTheConfiguration:
    """Every door of an anonymized run names places by schema path, count and
    line, never by a word of the configuration, original or replaced."""

    @pytest.mark.parametrize("name", list(DOORS))
    def test_no_message_holds_a_word_of_it(self, name: str, tmp_path: Path) -> None:
        door = DOORS[name]
        code, said, text = door.run(True, tmp_path)
        for fragment in door.shown:
            assert fragment in said, f"{name}: {fragment!r} missing from {said!r}"
        assert MARKER not in text.casefold(), f"{name}: {text!r}"
        assert not DOTTED_QUAD.search(text), f"{name}: {text!r}"
        for word in (ADDRESS, _pseudonym(), *door.words):
            assert word not in text, f"{name}: {word!r} in {text!r}"
        if door.kept is not None:
            plain_code, _, _ = door.run(False, tmp_path)
            assert code == plain_code, f"{name}: anonymizing changed the exit code"


class TestARunThatDoesNotAnonymizeKeepsItsMessages:
    """Without anonymization every door prints its own message, the words included."""

    @pytest.mark.parametrize("name", list(_KEPT))
    def test_the_message_quotes_the_configuration(self, name: str, tmp_path: Path) -> None:
        door = _KEPT[name]
        _, _, text = door.run(False, tmp_path)
        assert door.kept is not None
        assert door.kept in text, f"{name}: {door.kept!r} not in {text!r}"


class TestAFailureNoHandlerExpectsNamesOnlyItsClass:
    """A failure of an anonymized run that no handler expects prints its class
    and no traceback: its message and chain may hold the configuration (ruling
    F2 on the Test/Challenge of change anonymized-run-messages). A run that
    does not anonymize keeps its traceback."""

    @staticmethod
    def _fail(*_: object, **__: object) -> None:
        try:
            raise KeyError(f"sw1-acme {ADDRESS}")
        except KeyError as error:
            raise RuntimeError("the walk lost its place") from error

    @pytest.mark.parametrize(
        ("target", "args"),
        [
            ("junoscfg.convert_config_result", ["-i", "set", "-e", "set"]),
            ("junoscfg.validate_config", ["-i", "set", "-v"]),
        ],
        ids=["convert", "validate"],
    )
    def test_the_details_are_withheld(
        self, monkeypatch: pytest.MonkeyPatch, target: str, args: list[str]
    ) -> None:
        monkeypatch.setattr(target, self._fail)
        anonymized = CliRunner().invoke(
            main,
            ["convert", *args, "--anonymize-ips"],
            input="set system host-name sw1-acme\n",
        )
        assert isinstance(anonymized.exception, SystemExit)
        assert anonymized.exit_code == 1
        assert anonymized.stderr == f"Error: the conversion failed (RuntimeError){_WITHHELD}\n"
        for word in (MARKER, ADDRESS, "KeyError", "lost its place"):
            assert word not in anonymized.output
        plain = CliRunner().invoke(main, ["convert", *args], input="set system host-name sw1\n")
        assert isinstance(plain.exception, RuntimeError)


class TestTheLibraryRaisesAFailureByItsClassOnly:
    """A failure of an anonymized conversion the library does not expect is a
    fresh `RuntimeError` naming its class, with no cause, context or notes:
    a `TypeError` from the JSON writer carried the note "when serializing
    dict item 'x-acme'" (Reviewer R1, ruling). A conversion that does not
    anonymize raises the original."""

    def test_nothing_of_the_original_travels_with_it(self) -> None:
        with pytest.raises(RuntimeError) as raised:
            convert_config_result(
                _YAML_DATE, from_format=Format.YAML, to_format=Format.JSON, anon_config=_config()
            )
        error = raised.value
        assert str(error) == f"the conversion failed (TypeError){_WITHHELD}"
        assert error.__cause__ is None
        assert error.__context__ is None
        assert not getattr(error, "__notes__", None)

    def test_a_refusal_to_read_carries_nothing_either(self) -> None:
        with pytest.raises(ValueError, match=r"\(line 1\)") as raised:
            convert_config_result(
                _BRACKET, from_format=Format.SET, to_format=Format.SET, anon_config=_config()
            )
        assert type(raised.value) is ValueError
        assert raised.value.__cause__ is None
        assert raised.value.__context__ is None

    def test_without_anonymization_the_original_is_raised(self) -> None:
        with pytest.raises(TypeError):
            convert_config_result(_YAML_DATE, from_format=Format.YAML, to_format=Format.JSON)


class TestOnlyTheDebugLevelPrintsOriginals:
    """`log_level="debug"` pairs each original with its replacement, by design
    and documented (CLI help, `AnonymizeConfig.log_level`, the CLI guide); no
    other level prints one."""

    def test_debug_pairs_each_original_with_its_replacement(self) -> None:
        result = convert_config_result(
            f"set system name-server {ADDRESS}\n",
            from_format=Format.SET,
            to_format=Format.SET,
            anon_config=_config(log_level="debug"),
        )
        debug = [d.render() for d in result.diagnostics if d.severity == "debug"]
        assert any(ADDRESS in line and _pseudonym() in line for line in debug), debug

    @pytest.mark.parametrize("level", ["quiet", "normal"])
    def test_no_other_level_does(self, level: str, capfd: pytest.CaptureFixture[str]) -> None:
        result = convert_config_result(
            f"set system name-server {ADDRESS}\n",
            from_format=Format.SET,
            to_format=Format.SET,
            anon_config=_config(log_level=level),
        )
        assert result.output.strip(), "the run converted"
        assert not any(ADDRESS in d.render() for d in result.diagnostics)
        captured = capfd.readouterr()
        assert ADDRESS not in captured.err + captured.out, "ipanon printed it"


class TestTheAuditHasNoAnonymizedRun:
    """`junoscfg audit` reads a configuration and never anonymizes it, so it
    opens no door of an anonymized run."""

    def test_it_takes_no_anonymize_option(self) -> None:
        result = CliRunner().invoke(
            main, ["audit", "unused", "--anonymize-ips"], input="set system host-name r1\n"
        )
        assert result.exit_code == 2
        assert "No such option" in result.output
