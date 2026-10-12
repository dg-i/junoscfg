"""Field-level validation for Junos configuration values.

Validates leaf values in the JSON dict IR against schema constraints:
enums, patterns, XSD types, IP addresses, and mandatory fields.
"""

from __future__ import annotations

import ipaddress
import re
from dataclasses import dataclass, field
from typing import Any

from junoscfg.display import (
    INTEGER_TYPES,
    UNPLACED_STATEMENTS,
    entry_key_names,
    entry_keys,
    enum_is_fragment,
    holds_tag,
    passes_tag_to_child,
    schema_child,
    statement_name_spellings,
    strip_type_prefix,
    unplaced_record_problem,
)


@dataclass(frozen=True, slots=True)
class FieldError:
    """A single field validation error or warning."""

    path: str
    message: str
    value: Any = None
    expected: str = ""


@dataclass
class FieldValidationResult:
    """Result of field-level validation."""

    errors: list[FieldError] = field(default_factory=list)
    warnings: list[FieldError] = field(default_factory=list)

    @property
    def valid(self) -> bool:
        """True when no field errors were recorded."""
        return len(self.errors) == 0


class FieldValidationError(Exception):
    """Raised when field validation fails in strict mode."""

    def __init__(self, result: FieldValidationResult) -> None:
        """Build the error from *result*, summarising its first few messages."""
        self.result = result
        msgs = [e.message for e in result.errors[:5]]
        detail = "; ".join(msgs)
        if len(result.errors) > 5:
            detail += f" ... and {len(result.errors) - 5} more"
        super().__init__(f"Field validation failed ({len(result.errors)} error(s)): {detail}")


# XSD type names that indicate IP address fields
_IPV4_TYPES = frozenset({"ipv4addr", "ipv4address", "ipv4prefix"})
_IPV6_TYPES = frozenset({"ipv6addr", "ipv6address", "ipv6prefix"})
_IP_ANY_TYPES = frozenset({"ipaddr", "ipprefix", "ipprefix-optional"})

# Union types that take an IP address *or* a name. The XSD says so in the type
# name, and `policy-options policy-statement <p> term <t> from interface lo0.0`
# is the ordinary form. Validating these as IP-only raised 215 of the 557 field
# warnings left over Juniper's own validated-design configurations.
_IP_OR_NAME_TYPES = frozenset({"ipaddr-or-interface"})

# Patterns that look like IP address regex patterns
_IPV4_PATTERN_HINT = re.compile(r"\d.*\\d.*\\\.")
_IPV6_PATTERN_HINT = re.compile(r"[0-9a-fA-F].*:")

_BOOLEAN_TYPES = frozenset({"boolean"})

# Bounds for unsigned integer types
_UNSIGNED_BOUNDS: dict[str, tuple[int, int]] = {
    "uint8": (0, 255),
    "unsignedByte": (0, 255),
    "uint16": (0, 65535),
    "unsignedShort": (0, 65535),
    "uint32": (0, 4294967295),
    "unsignedInt": (0, 4294967295),
    "uint64": (0, 18446744073709551615),
    "unsignedLong": (0, 18446744073709551615),
}

# Bounds for signed integer types
_SIGNED_BOUNDS: dict[str, tuple[int, int]] = {
    "int8": (-128, 127),
    "byte": (-128, 127),
    "int16": (-32768, 32767),
    "short": (-32768, 32767),
    "int32": (-2147483648, 2147483647),
    "integer": (-2147483648, 2147483647),
    "int64": (-9223372036854775808, 9223372036854775807),
    "long": (-9223372036854775808, 9223372036854775807),
}


# POSIX character class → Python regex equivalents
_POSIX_CLASSES: dict[str, str] = {
    "[:alnum:]": r"a-zA-Z0-9",
    "[:alpha:]": r"a-zA-Z",
    "[:digit:]": r"0-9",
    "[:lower:]": r"a-z",
    "[:upper:]": r"A-Z",
    "[:space:]": r"\s",
    "[:blank:]": r" \t",
    "[:print:]": r"\x20-\x7E",
    "[:graph:]": r"\x21-\x7E",
    "[:punct:]": r"!-/:-@[-`{-~",
    "[:xdigit:]": r"0-9a-fA-F",
    "[:cntrl:]": r"\x00-\x1F\x7F",
    "[:ascii:]": r"\x00-\x7F",
}


#: An escape, or a bracket expression (body: group 1); in a body, a class, an escape or `[`.
_BRACKET = re.compile(r"\\.|\[(\^?\]?(?:\[:[a-z]+:\]|\\.|[^\]])*)\]", re.DOTALL)
_IN_BRACKET = re.compile(r"\[:[a-z]+:\]|\\.|\[", re.DOTALL)
_IN_BRACKET_SPELLING = {**_POSIX_CLASSES, "[": r"\["}


def _posix_to_python_re(pattern: str) -> str:
    """Python's spelling of *pattern*'s POSIX bracket expressions; a literal `[` is escaped."""

    def bracket(m: re.Match[str]) -> str:
        if m[1] is None:  # an escape outside a bracket expression
            return m[0]
        return f"[{_IN_BRACKET.sub(lambda t: _IN_BRACKET_SPELLING.get(t[0], t[0]), m[1])}]"

    return _BRACKET.sub(bracket, pattern)


_NUMERIC_OR_RANGE_RE = re.compile(r"^[0-9]+(-[0-9]+)?$")


def _is_numeric_or_range(value: str) -> bool:
    """Check if value is a number or numeric range like '33434-33464'.

    Junos XSD types frequently use unions of enums and numeric values,
    but the schema only captures the enum portion.  Accept numeric
    values as valid when the enum check alone fails.
    """
    return _NUMERIC_OR_RANGE_RE.match(value) is not None


def _has_enum_placeholder(allowed: list[str]) -> bool:
    """Check if an enum list contains XSD union placeholders.

    Junos XSD union types combine literal keywords with type placeholders
    that accept arbitrary values.  The schema only captures the enum
    portion, so these placeholders appear as enum values:

    - ``"name"`` / ``"value"`` — generic string/numeric placeholders
    - values ending in ``-name`` — instance name references
      (e.g. ``routing-instance-name``, ``logical-system-name``)
    - values ending in ``-id`` — identifier references
      (e.g. ``vlan-id``, ``port-id``)
    """
    for v in allowed:
        if v in ("name", "value"):
            return True
        if v.endswith("-name") or v.endswith("-id"):
            return True
    return False


#: The ``expected`` of an error for a statement the schema could not place;
#: the pipeline filters on it, since anonymization cannot see such a statement.
UNPLACED = "a statement the schema places"


class FieldValidator:
    """Validates leaf values in the JSON dict IR against schema constraints."""

    def __init__(self, *, withhold_values: bool = False) -> None:
        """Build the validator against the structure tree the artifacts resolve to.

        It took a ``schema`` argument too, which only tests passed; they now
        select a tree the way a caller does, with ``display.artifacts_dir``.

        With *withhold_values* (an anonymized conversion's report) no message
        quotes a word of the configuration: each keeps its path, its reason
        and what was expected, `FieldError.value` is ``""``, and an `UNPLACED`
        report's text is withheld (spec anonymization/placed-values).
        """
        from junoscfg.display import load_schema_tree

        schema = load_schema_tree()
        self._schema = schema
        self._enums: list[list[str]] = []
        self._patterns: list[str] = []
        self._compiled: dict[int, re.Pattern[str]] = {}
        self._withhold = withhold_values

        if schema:
            self._enums = schema.get("_enums", [])
            self._patterns = schema.get("_patterns", [])

    def _get_pattern(self, idx: int) -> tuple[re.Pattern[str], bool]:
        """Get compiled pattern and negated flag by index."""
        if idx not in self._compiled:
            raw = self._patterns[idx]
            negated = raw.startswith("!")
            pat = raw[1:] if negated else raw
            pat = _posix_to_python_re(pat)
            try:
                self._compiled[idx] = re.compile(pat)
            except re.error:
                # Invalid regex — store a pattern that never matches
                self._compiled[idx] = re.compile(r"\A$(?!.)")
        raw = self._patterns[idx]
        negated = raw.startswith("!")
        return self._compiled[idx], negated

    def validate(self, config: dict[str, Any]) -> FieldValidationResult:
        """Validate all leaf values in *config* against schema constraints.

        Args:
            config: The IR dict (content inside ``{"configuration": ...}``).

        Returns:
            Validation result with errors and warnings.
        """
        result = FieldValidationResult()
        if not self._schema:
            return result
        if isinstance(config, dict) and "configuration" in config:
            # The wrapper `find_configuration` strips; passed whole it used to
            # validate nothing and say so with silence.
            config = config["configuration"]

        # Navigate to configuration node in schema
        schema_root = self._schema.get("c", {}).get("configuration", self._schema)
        self._walk(config, schema_root, [], result)
        if self._withhold:
            result.errors = [
                FieldError(
                    path=error.path,
                    message="a statement could not be placed in the schema: kept as written, "
                    "not validated (its text is withheld: the conversion anonymizes)",
                    value="",
                    expected=UNPLACED,
                )
                if error.expected == UNPLACED
                else error
                for error in result.errors
            ]
        return result

    def _quoted(self, value: str) -> str:
        """*value* as a message quotes it, or the withholding when the run anonymizes."""
        return "(withheld: the conversion anonymizes)" if self._withhold else repr(value)

    def _kept(self, value: Any) -> Any:
        """*value* as a report carries it: ``""`` when the run anonymizes."""
        return "" if self._withhold else value

    def _walk(
        self,
        obj: Any,
        schema_node: dict[str, Any] | None,
        path: list[str],
        result: FieldValidationResult,
    ) -> None:
        """Recursively walk the IR dict, validating leaves."""
        if obj is None or schema_node is None:
            return

        if isinstance(obj, dict):
            children = schema_node.get("c", {})
            # Check mandatory fields
            self._check_mandatory(obj, children, path, result, schema_node)

            for key, value in obj.items():
                # Skip attribute keys (@ prefix)
                if key.startswith("@"):
                    continue

                if key == UNPLACED_STATEMENTS:
                    self._report_unplaced(value, schema_node, obj, path, result)
                    continue

                # A universal statement below the root resolves to the
                # root's node, as in every walker of the tree (ARCH-C06).
                child_schema = schema_child(schema_node, key, self._schema)

                # A universal statement with nothing in it -- a bare `set
                # system apply-flags`, or one holding only a tag -- names no
                # flag, group or macro, as a leaf without its value names
                # nothing.
                if (
                    child_schema is not None
                    and child_schema.get("u")
                    and not child_schema.get("l")
                    and (
                        value in (None, True, [None], [])
                        or (isinstance(value, dict) and all(k.startswith("@") for k in value))
                    )
                ):
                    self._unplaced(
                        f"'{key}' without its value", schema_node, obj, path, result, value=key
                    )
                    continue

                # A transparent container: its transparent child's entries
                # against the child, its other children (`interface-range`
                # beside `interface`) against the container itself. Replaced
                # by its child, the container hid every sibling, or walked
                # them as an entry when the child was absent (NEW-A-S2).
                if child_schema and child_schema.get("t") and isinstance(value, dict | list):
                    transparent_child = child_schema["t"]
                    inner_schema = child_schema.get("c", {}).get(transparent_child)
                    if inner_schema is not None:
                        entries = value.get(transparent_child) if isinstance(value, dict) else value
                        path.append(key)
                        for item in entries if isinstance(entries, list) else [entries]:
                            if isinstance(item, dict):
                                if isinstance(entries, list):
                                    self._check_key_fields(item, inner_schema, path, result)
                                self._walk(item, inner_schema, path, result)
                        if isinstance(value, dict):
                            siblings = {k: v for k, v in value.items() if k != transparent_child}
                            if siblings:
                                self._walk(siblings, child_schema, path, result)
                        path.pop()
                        continue

                # A keyed list holding something other than entries: its
                # keyword was written with no key value, as JSON or YAML may
                # hold it (`[null]`); the set reader keeps it in the record.
                items = value if isinstance(value, list) else [value]
                incomplete = (
                    child_schema is not None
                    and entry_keys(child_schema) != ("name",)
                    and not all(isinstance(item, dict) for item in items)
                )
                if child_schema is None or incomplete:
                    # A key the schema does not name and no reader writes by
                    # rule is configuration junoscfg could not model, from
                    # JSON, YAML or XML (the set reader keeps it in the
                    # record); it used to pass here without a word, which is
                    # how a defective artifact set went unnoticed for months.
                    if not self._is_structural_key(key, schema_node):
                        self._unplaced(f"'{key}'", schema_node, obj, path, result, value=key)
                    continue

                # Named list (L flag)
                if child_schema.get("L"):
                    if isinstance(value, list):
                        for item in value:
                            path.append(key)
                            self._check_key_fields(item, child_schema, path, result)
                            self._walk(item, child_schema, path, result)
                            path.pop()
                        continue
                    elif isinstance(value, dict):
                        path.append(key)
                        self._check_key_fields(value, child_schema, path, result)
                        self._walk(value, child_schema, path, result)
                        path.pop()
                        continue

                # Leaf node — validate the value
                if child_schema.get("l"):
                    if not (schema_node.get("L") and key in entry_key_names(schema_node)) and (
                        value is None or value is True or value == [] or value == [None]
                    ):
                        # A leaf written without its value, from JSON, YAML
                        # or XML (`"host-name": null`): a line the device
                        # rejects, written back as it stands (NEW-C1).
                        self._unplaced(
                            f"'{key}' without its value", schema_node, obj, path, result, value=key
                        )
                        continue
                    path.append(key)
                    # A key value takes its own leaf's type. A key field the
                    # tree names in `k` is closed to its enum, as the grammar
                    # renders it: the device rejects `as-path-neighbors 1 ...`
                    # although the XSD's union for `list-type` also names a
                    # number. A `name` key's enum is a fragment and open, as
                    # it was before `name` became a tree child: `classifiers
                    # dscp SAMPLE-DSCP` carries `['default']` and is valid.
                    closed: bool | None = None
                    if schema_node.get("L") and key in entry_key_names(schema_node):
                        closed = entry_keys(schema_node) != ("name",)
                    self._validate_leaf(value, path, child_schema, result, closed=closed)
                    path.pop()
                # Container — recurse
                elif isinstance(value, dict):
                    if passes_tag_to_child(child_schema) and (
                        holds_tag(value.get("@")) or holds_tag(obj.get(f"@{key}"))
                    ):
                        # `deactivate … family`: the device rejects it
                        # ("missing argument"); it tags the family inside.
                        entry = self._entry_label(schema_node, obj)
                        where = f" under {path[-1]} {entry}" if entry and path else ""
                        result.errors.append(
                            FieldError(
                                path=".".join(path),
                                message=(
                                    f"a tag on '{key}'{where} could not be placed in the "
                                    f"schema: Junos tags what '{key}' holds, never '{key}' "
                                    "itself; kept as written"
                                ),
                                value=key,
                                expected=UNPLACED,
                            )
                        )
                    path.append(key)
                    self._walk(value, child_schema, path, result)
                    path.pop()
                elif isinstance(value, list) and any(isinstance(item, dict) for item in value):
                    # A list a container holds -- the port-mirroring
                    # `routing-instance`, a list of one in JSON: each entry
                    # is validated against the container.
                    path.append(key)
                    for item in value:
                        if isinstance(item, dict):
                            self._walk(item, child_schema, path, result)
                    path.pop()
                elif (
                    isinstance(value, str | int | float)
                    and not isinstance(value, bool)
                    and child_schema.get("c")
                    and not child_schema.get("p")
                    and not child_schema.get("L")
                ):
                    # A value where the tree has a container: `"apply-flags":
                    # "omit"`, the spelling 0.17.0 wrote for the top level's
                    # flag. Writers keep it as it stands; it is not validated.
                    self._unplaced(
                        f"'{key}' holding a value", schema_node, obj, path, result, value=key
                    )

        elif isinstance(obj, list):
            for item in obj:
                self._walk(item, schema_node, path, result)

    def _report_unplaced(
        self,
        record: Any,
        schema_node: dict[str, Any],
        obj: dict[str, Any],
        path: list[str],
        result: FieldValidationResult,
    ) -> None:
        """Report each statement a level keeps whole (`UNPLACED_STATEMENTS`).

        A statement is reported once; a meta command kept beside it, or beside
        a statement below it, adds no report, and one with neither is reported
        on its own. A record no writer could print is one report, its reason
        naming no statement.
        """
        problem = unplaced_record_problem(record)
        if problem is not None:
            result.errors.append(
                FieldError(path=".".join(path), message=problem, value="", expected=UNPLACED)
            )
            return
        texts = [key for key in record if not key.startswith("@")]
        for key in record:
            text = key[1:] if key.startswith("@") else key
            if key.startswith("@") and any(t == text or t.startswith(f"{text} ") for t in texts):
                continue
            self._unplaced(f"'{text}'", schema_node, obj, path, result, value=text)

    def _unplaced(
        self,
        what: str,
        schema_node: dict[str, Any],
        obj: dict[str, Any],
        path: list[str],
        result: FieldValidationResult,
        *,
        value: str,
    ) -> None:
        """Report *what* as a statement the schema could not place, kept as written."""
        entry = self._entry_label(schema_node, obj)
        where = f" under {path[-1]} {entry}" if entry and path else ""
        result.errors.append(
            FieldError(
                path=".".join(path),
                message=f"{what}{where} could not be placed in the schema: kept as written, "
                "not validated",
                value=value,
                expected=UNPLACED,
            )
        )

    @staticmethod
    def _check_key_fields(
        entry: Any, list_schema: dict[str, Any], path: list[str], result: FieldValidationResult
    ) -> None:
        """Report an entry that lacks one of its key fields.

        JSON, YAML and XML can hold one; written out it is a line the device
        rejects -- `{"list-name": "X"}` as `as-path-neighbors X`. It is the
        statement a set reader cannot complete, reported the same way.
        """
        if not (isinstance(entry, dict) and list_schema.get("L")):
            return
        for key_field in entry_keys(list_schema):
            names = key_field if isinstance(key_field, tuple) else (key_field,)
            if not any(name in entry for name in names):
                missing = " or ".join(names)
                result.errors.append(
                    FieldError(
                        path=".".join(path),
                        message=(
                            f"'{path[-1]}' entry without its key field '{missing}' could not "
                            "be placed in the schema: kept as written, not validated"
                        ),
                        value=path[-1],
                        expected=UNPLACED,
                    )
                )
                return

    def _is_structural_key(self, key: str, schema_node: dict[str, Any]) -> bool:
        """Whether *key* is one the readers write by rule rather than as a child.

        A list entry carries its key fields, which the tree keeps as children;
        a list built by a fix, `groups`' `group` among them, has no `name`
        child and is keyed `name` all the same. The spelling of a folded on/off
        switch, ``disable`` for ``enable-disable``, is written in place of the
        node, by `statement_name_spellings`.
        """
        if schema_node.get("L") and key in entry_key_names(schema_node):
            return True
        for cname, cnode in schema_node.get("c", {}).items():
            if key in self._switch_spellings(cname, cnode):
                return True
        return False

    @staticmethod
    def _entry_label(schema_node: dict[str, Any], entry: dict[str, Any]) -> str:
        """The key an entry is written with, for a message; empty for a container."""
        if not schema_node.get("L"):
            return ""
        parts: list[str] = []
        for key_field in entry_keys(schema_node):
            for name in key_field if isinstance(key_field, tuple) else (key_field,):
                value = entry.get(name)
                if value is None:
                    continue
                if isinstance(key_field, tuple):
                    parts.append(name)
                if not isinstance(value, list):
                    parts.append(str(value))
                break
        return " ".join(parts)

    def _switch_spellings(self, name: str, node: Any) -> tuple[str, ...]:
        """The spellings a folded on/off switch node is written as, or ``()``."""
        if not (isinstance(node, dict) and node.get("nk") and node.get("l") and "e" in node):
            return ()
        index = node["e"]
        if not (isinstance(index, int) and index < len(self._enums)):
            return ()
        return statement_name_spellings(name, self._enums[index])

    def _validate_leaf(
        self,
        value: Any,
        path: list[str],
        schema_node: dict[str, Any],
        result: FieldValidationResult,
        *,
        closed: bool | None = None,
    ) -> None:
        """Validate a leaf value against enum, pattern, and type constraints.

        *closed* is None for a leaf that is no key field. True holds a key
        field the tree names in `k` to its enum where the enum is not a
        fragment of a wider union; False takes a `name` key's enum as a
        fragment, so a value outside it passes the enum check.
        """
        # Presence flags carry no value. An empty value is checked like any
        # other: the device writes `description ""` (a string leaf, which
        # takes it), and `""` on an enum, an integer or a pattern it fails is
        # a value the device rejects -- an empty XML element read so, too.
        if value is None or value is True:
            return

        # List values: validate each element individually
        if isinstance(value, list):
            for item in value:
                self._validate_leaf(item, path, schema_node, result, closed=closed)
            return

        # Leaf-as-object form: annotation keys carry no value to validate
        # (e.g. {"host-name": {"@": {"operation": "delete"}}})
        if isinstance(value, dict):
            for k, v in value.items():
                if not k.startswith("@"):
                    self._validate_leaf(v, path, schema_node, result, closed=closed)
            return

        str_value = str(value)
        quoted = self._quoted(str_value)
        dot_path = ".".join(path)

        # 1. Enum check
        has_fallback = schema_node.get("r") is not None or schema_node.get("tr") is not None
        enum_idx = schema_node.get("e")
        if enum_idx is not None and enum_idx < len(self._enums):
            allowed = self._enums[enum_idx]
            if str_value not in allowed:
                if closed is False:
                    return  # A `name` key: its enum is a fragment
                closed = closed and not enum_is_fragment(path[-1] if path else "", allowed)
                if closed:
                    pass  # A key field's closed enum: the mismatch is reported below
                elif has_fallback:
                    pass  # Fall through to pattern/type checks
                elif _is_numeric_or_range(str_value):
                    return  # Accept numeric values — XSD union types often allow them
                elif _has_enum_placeholder(allowed):
                    return  # XSD union with placeholder for arbitrary values
                elif schema_node.get("nk") and enum_is_fragment(path[-1] if path else "", allowed):
                    # A nokeyword leaf is positional: the value stands where
                    # the element name would, and the XSD models it as a union
                    # of an enum with a freeform type, of which extraction keeps
                    # only the enum. `classifier-name` carries `['default']` and
                    # takes any classifier name; `vlan-id` carries
                    # `['none', 'vlan-id']` and takes any VLAN number. Enforcing
                    # these produced 9,903 of the 10,021 field warnings raised
                    # over 200 of Juniper's own validated-design configurations.
                    return
                if closed or not has_fallback:
                    # Enum-only field, non-numeric — mismatch is definitive
                    names = allowed[:5]
                    suffix = f" ... ({len(allowed)} total)" if len(allowed) > 5 else ""
                    result.errors.append(
                        FieldError(
                            path=dot_path,
                            message=(
                                f"Invalid value {quoted}: "
                                f"must be one of [{', '.join(names)}{suffix}]"
                            ),
                            value=self._kept(value),
                            expected=f"one of {allowed}",
                        )
                    )
                    return
            else:
                return  # Value matched enum — valid

        # 2. Pattern check
        pat_idx = schema_node.get("r")
        if pat_idx is not None and pat_idx < len(self._patterns):
            compiled, negated = self._get_pattern(pat_idx)
            matches = compiled.search(str_value) is not None
            if negated:
                if matches:
                    result.errors.append(
                        FieldError(
                            path=dot_path,
                            message=(
                                f"Invalid value {quoted}: "
                                f"must not match pattern {self._patterns[pat_idx][1:]!r}"
                            ),
                            value=self._kept(value),
                            expected=f"value not matching {self._patterns[pat_idx][1:]!r}",
                        )
                    )
                    return
            else:
                if matches:
                    return  # Pattern matched — value is valid
                # Pattern didn't match — fall through to type check if available
                type_ref = schema_node.get("tr")
                if not type_ref:
                    result.errors.append(
                        FieldError(
                            path=dot_path,
                            message=(
                                f"Invalid value {quoted}: "
                                f"must match pattern {self._patterns[pat_idx]!r}"
                            ),
                            value=self._kept(value),
                            expected=f"value matching {self._patterns[pat_idx]!r}",
                        )
                    )
                    return

        # 3. Type-based checks
        type_ref = schema_node.get("tr")
        if type_ref:
            self._validate_type(str_value, value, dot_path, type_ref, result)

    def _validate_type(
        self,
        str_value: str,
        value: Any,
        dot_path: str,
        type_ref: str,
        result: FieldValidationResult,
    ) -> None:
        """Validate value against its XSD type reference."""
        quoted = self._quoted(str_value)
        tr_lower = type_ref.lower()
        # The tree stores XSD built-ins prefixed -- `xsd:unsignedShort`. The
        # table holds bare names, so every integer leaf typed by an XSD
        # built-in went unchecked: `set interfaces ge-0/0/0 mtu notanumber`
        # converted without a warning.
        bare = strip_type_prefix(type_ref)

        # IP address validation
        if tr_lower in _IP_OR_NAME_TYPES:
            return  # an IP or a name; both are valid, so there is nothing to check
        if tr_lower in _IPV4_TYPES or tr_lower in _IPV6_TYPES or tr_lower in _IP_ANY_TYPES:
            self._validate_ip(str_value, dot_path, tr_lower, result)
            return

        # Integer validation
        if bare in INTEGER_TYPES:
            self._validate_integer(str_value, dot_path, bare, result)
            return

        # Boolean validation
        if bare in _BOOLEAN_TYPES and str_value.lower() not in ("true", "false", "1", "0"):
            result.errors.append(
                FieldError(
                    path=dot_path,
                    message=f"Invalid value {quoted}: must be a boolean (true/false)",
                    value=self._kept(value),
                    expected="true or false",
                )
            )

    def _validate_ip(
        self,
        str_value: str,
        dot_path: str,
        type_lower: str,
        result: FieldValidationResult,
    ) -> None:
        """Validate an IP address or prefix value."""
        quoted = self._quoted(str_value)
        is_ipv4_type = type_lower in _IPV4_TYPES
        is_ipv6_type = type_lower in _IPV6_TYPES
        is_prefix = "prefix" in type_lower

        # Try parsing as network/prefix first
        if is_prefix or "/" in str_value:
            try:
                net = ipaddress.ip_network(str_value, strict=False)
                if is_ipv4_type and net.version != 4:
                    result.errors.append(
                        FieldError(
                            path=dot_path,
                            message=f"Invalid value {quoted}: expected IPv4 prefix, got IPv6",
                            value=self._kept(str_value),
                            expected="valid IPv4 prefix",
                        )
                    )
                elif is_ipv6_type and net.version != 6:
                    result.errors.append(
                        FieldError(
                            path=dot_path,
                            message=f"Invalid value {quoted}: expected IPv6 prefix, got IPv4",
                            value=self._kept(str_value),
                            expected="valid IPv6 prefix",
                        )
                    )
                return
            except ValueError:
                expected = (
                    "valid IPv4 prefix"
                    if is_ipv4_type
                    else ("valid IPv6 prefix" if is_ipv6_type else "valid IP prefix")
                )
                result.errors.append(
                    FieldError(
                        path=dot_path,
                        message=f"Invalid value {quoted}: not a {expected}",
                        value=self._kept(str_value),
                        expected=expected,
                    )
                )
                return

        # Try parsing as plain address
        try:
            addr = ipaddress.ip_address(str_value)
            if is_ipv4_type and addr.version != 4:
                result.errors.append(
                    FieldError(
                        path=dot_path,
                        message=f"Invalid value {quoted}: expected IPv4 address, got IPv6",
                        value=self._kept(str_value),
                        expected="valid IPv4 address",
                    )
                )
            elif is_ipv6_type and addr.version != 6:
                result.errors.append(
                    FieldError(
                        path=dot_path,
                        message=f"Invalid value {quoted}: expected IPv6 address, got IPv4",
                        value=self._kept(str_value),
                        expected="valid IPv6 address",
                    )
                )
        except ValueError:
            expected = (
                "valid IPv4 address"
                if is_ipv4_type
                else ("valid IPv6 address" if is_ipv6_type else "valid IP address")
            )
            result.errors.append(
                FieldError(
                    path=dot_path,
                    message=f"Invalid value {quoted}: not a {expected}",
                    value=self._kept(str_value),
                    expected=expected,
                )
            )

    def _validate_integer(
        self,
        str_value: str,
        dot_path: str,
        type_ref: str,
        result: FieldValidationResult,
    ) -> None:
        """Validate an integer value against its XSD type bounds."""
        quoted = self._quoted(str_value)
        try:
            num = int(str_value)
        except ValueError:
            result.errors.append(
                FieldError(
                    path=dot_path,
                    message=f"Invalid value {quoted}: must be an integer ({type_ref})",
                    value=self._kept(str_value),
                    expected=f"integer ({type_ref})",
                )
            )
            return

        # Check bounds for unsigned types
        bounds = _UNSIGNED_BOUNDS.get(type_ref) or _SIGNED_BOUNDS.get(type_ref)
        if bounds:
            lo, hi = bounds
            if num < lo or num > hi:
                result.errors.append(
                    FieldError(
                        path=dot_path,
                        message=(
                            f"Invalid value {quoted}: out of range for {type_ref} ({lo}..{hi})"
                        ),
                        value=self._kept(str_value),
                        expected=f"{type_ref} ({lo}..{hi})",
                    )
                )

    def _check_mandatory(
        self,
        obj: dict[str, Any],
        children_schema: dict[str, Any],
        path: list[str],
        result: FieldValidationResult,
        parent_schema: dict[str, Any] | None = None,
    ) -> None:
        """Check for missing mandatory fields (warnings, not errors)."""
        # Skip mandatory checks for flat-dict elements — their children
        # are combined into a single command line and are functionally optional
        if parent_schema and parent_schema.get("fd"):
            return

        for child_name, child_schema in children_schema.items():
            if child_schema.get("m") and child_name not in obj:
                # A folded switch is written by its spelling: `enable` or
                # `disable` in the IR satisfies the node `enable-disable`.
                spellings = self._switch_spellings(child_name, child_schema)
                if any(spelling in obj for spelling in spellings):
                    continue
                dot_path = ".".join([*path, child_name])
                result.warnings.append(
                    FieldError(
                        path=dot_path,
                        message=(
                            f"Missing mandatory field {child_name!r}: "
                            "may be required at commit; the configuration loads without it"
                        ),
                        value=None,
                        expected=f"required field {child_name!r}",
                    )
                )
