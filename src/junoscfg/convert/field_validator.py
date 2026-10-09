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
    UNIVERSAL_STATEMENTS,
    entry_key_names,
    entry_keys,
    enum_is_fragment,
    statement_name_spellings,
    strip_type_prefix,
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


def _posix_to_python_re(pattern: str) -> str:
    """Convert POSIX character classes in a regex to Python equivalents."""
    for posix, python in _POSIX_CLASSES.items():
        pattern = pattern.replace(posix, python)
    return pattern


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

    def __init__(self, schema: dict[str, Any] | None = None) -> None:
        """Build the validator against *schema*, or the bundled schema tree."""
        if schema is None:
            from junoscfg.display import load_schema_tree

            schema = load_schema_tree()
        self._schema = schema
        self._enums: list[list[str]] = []
        self._patterns: list[str] = []
        self._compiled: dict[int, re.Pattern[str]] = {}

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
        return result

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

                # Valid at every level; the reader shapes them, not the tree.
                if key in UNIVERSAL_STATEMENTS:
                    continue

                child_schema = children.get(key)

                # Handle transparent containers
                if child_schema and child_schema.get("t"):
                    transparent_child = child_schema["t"]
                    tc_children = child_schema.get("c", {})
                    inner_schema = tc_children.get(transparent_child)
                    if isinstance(value, dict) and transparent_child in value:
                        value = value[transparent_child]
                    if isinstance(value, list) and inner_schema:
                        for item in value:
                            path.append(key)
                            self._walk(item, inner_schema, path, result)
                            path.pop()
                        continue
                    elif isinstance(value, dict) and inner_schema:
                        path.append(key)
                        self._walk(value, inner_schema, path, result)
                        path.pop()
                        continue

                # A keyed list holding something other than entries: its
                # keyword was written with no key value, a statement the set
                # reader keeps whole (`true`, or `[null]` once through JSON).
                items = value if isinstance(value, list) else [value]
                incomplete = (
                    child_schema is not None
                    and "k" in child_schema
                    and not all(isinstance(item, dict) for item in items)
                )
                if child_schema is None or incomplete:
                    # A key the schema does not name and no reader writes by
                    # rule is configuration junoscfg could not model. The set
                    # reader keeps such a statement whole as one key; it used
                    # to pass here without a word, which is how a defective
                    # artifact set went unnoticed for five months.
                    if not self._is_structural_key(key, schema_node):
                        entry = self._entry_label(schema_node, obj)
                        where = f" under {path[-1]} {entry}" if entry and path else ""
                        message = (
                            f"'{key}'{where} could not be placed in the schema: "
                            "kept as written, not validated"
                        )
                        result.errors.append(
                            FieldError(
                                path=".".join(path), message=message, value=key, expected=UNPLACED
                            )
                        )
                    continue

                # Named list (L flag)
                if child_schema.get("L"):
                    if isinstance(value, list):
                        for item in value:
                            path.append(key)
                            self._walk(item, child_schema, path, result)
                            path.pop()
                        continue
                    elif isinstance(value, dict):
                        path.append(key)
                        self._walk(value, child_schema, path, result)
                        path.pop()
                        continue

                # Leaf node — validate the value
                if child_schema.get("l"):
                    path.append(key)
                    # A key value takes its own leaf's type, as the grammar
                    # renders it: a closed enum is closed. The device rejects
                    # `as-path-neighbors 1 ...` although the XSD's union for
                    # `list-type` also names a number.
                    is_key = "k" in schema_node and key in entry_key_names(schema_node)
                    self._validate_leaf(value, path, child_schema, result, closed=is_key)
                    path.pop()
                # Container — recurse
                elif isinstance(value, dict):
                    path.append(key)
                    self._walk(value, child_schema, path, result)
                    path.pop()

        elif isinstance(obj, list):
            for item in obj:
                self._walk(item, schema_node, path, result)

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
        closed: bool = False,
    ) -> None:
        """Validate a leaf value against enum, pattern, and type constraints.

        *closed* holds a key field to its enum where the enum is not a
        fragment of a wider union.
        """
        # Presence flags or empty values — skip
        if value is None or value is True or value == "":
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
        dot_path = ".".join(path)

        # 1. Enum check
        has_fallback = schema_node.get("r") is not None or schema_node.get("tr") is not None
        enum_idx = schema_node.get("e")
        if enum_idx is not None and enum_idx < len(self._enums):
            allowed = self._enums[enum_idx]
            if str_value not in allowed:
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
                    shown = allowed[:5]
                    suffix = f" ... ({len(allowed)} total)" if len(allowed) > 5 else ""
                    result.errors.append(
                        FieldError(
                            path=dot_path,
                            message=(
                                f"Invalid value {str_value!r}: "
                                f"must be one of [{', '.join(shown)}{suffix}]"
                            ),
                            value=value,
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
                                f"Invalid value {str_value!r}: "
                                f"must not match pattern {self._patterns[pat_idx][1:]!r}"
                            ),
                            value=value,
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
                                f"Invalid value {str_value!r}: "
                                f"must match pattern {self._patterns[pat_idx]!r}"
                            ),
                            value=value,
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
                    message=f"Invalid value {str_value!r}: must be a boolean (true/false)",
                    value=value,
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
                            message=f"Invalid value {str_value!r}: expected IPv4 prefix, got IPv6",
                            value=str_value,
                            expected="valid IPv4 prefix",
                        )
                    )
                elif is_ipv6_type and net.version != 6:
                    result.errors.append(
                        FieldError(
                            path=dot_path,
                            message=f"Invalid value {str_value!r}: expected IPv6 prefix, got IPv4",
                            value=str_value,
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
                        message=f"Invalid value {str_value!r}: not a {expected}",
                        value=str_value,
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
                        message=f"Invalid value {str_value!r}: expected IPv4 address, got IPv6",
                        value=str_value,
                        expected="valid IPv4 address",
                    )
                )
            elif is_ipv6_type and addr.version != 6:
                result.errors.append(
                    FieldError(
                        path=dot_path,
                        message=f"Invalid value {str_value!r}: expected IPv6 address, got IPv4",
                        value=str_value,
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
                    message=f"Invalid value {str_value!r}: not a {expected}",
                    value=str_value,
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
        try:
            num = int(str_value)
        except ValueError:
            result.errors.append(
                FieldError(
                    path=dot_path,
                    message=f"Invalid value {str_value!r}: must be an integer ({type_ref})",
                    value=str_value,
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
                            f"Invalid value {str_value!r}: out of range for {type_ref} ({lo}..{hi})"
                        ),
                        value=str_value,
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
                        message=f"Missing mandatory field {child_name!r}",
                        value=None,
                        expected=f"required field {child_name!r}",
                    )
                )
