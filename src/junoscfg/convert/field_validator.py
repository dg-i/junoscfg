"""Field-level validation for Junos configuration values.

Validates leaf values in the JSON dict IR against schema constraints:
enums, patterns, XSD types, IP addresses, and mandatory fields.
"""

from __future__ import annotations

import ipaddress
import re
from dataclasses import dataclass, field
from typing import Any


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
        return len(self.errors) == 0


class FieldValidationError(Exception):
    """Raised when field validation fails in strict mode."""

    def __init__(self, result: FieldValidationResult) -> None:
        self.result = result
        msgs = [e.message for e in result.errors[:5]]
        detail = "; ".join(msgs)
        if len(result.errors) > 5:
            detail += f" ... and {len(result.errors) - 5} more"
        super().__init__(f"Field validation failed ({len(result.errors)} error(s)): {detail}")


# XSD type names that indicate IP address fields
_IPV4_TYPES = frozenset({"ipv4addr", "ipv4address", "ipv4prefix"})
_IPV6_TYPES = frozenset({"ipv6addr", "ipv6address", "ipv6prefix"})
_IP_ANY_TYPES = frozenset({"ipaddr", "ipprefix", "ipaddr-or-interface", "ipprefix-optional"})

# Patterns that look like IP address regex patterns
_IPV4_PATTERN_HINT = re.compile(r"\d.*\\d.*\\\.")
_IPV6_PATTERN_HINT = re.compile(r"[0-9a-fA-F].*:")

# XSD types mapped to Python validation
_INTEGER_TYPES = frozenset(
    {
        "int8",
        "int16",
        "int32",
        "int64",
        "uint8",
        "uint16",
        "uint32",
        "uint64",
        "integer",
        "unsignedInt",
        "unsignedShort",
        "unsignedByte",
        "unsignedLong",
        "short",
        "long",
        "byte",
        "positiveInteger",
        "nonNegativeInteger",
        "negativeInteger",
        "nonPositiveInteger",
    }
)
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


class FieldValidator:
    """Validates leaf values in the JSON dict IR against schema constraints."""

    def __init__(self, schema: dict[str, Any] | None = None) -> None:
        if schema is None:
            from junoscfg.display.constants import load_schema_tree

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

                if child_schema is None:
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
                    self._validate_leaf(value, path, child_schema, result)
                    path.pop()
                # Container — recurse
                elif isinstance(value, dict):
                    path.append(key)
                    self._walk(value, child_schema, path, result)
                    path.pop()

        elif isinstance(obj, list):
            for item in obj:
                self._walk(item, schema_node, path, result)

    def _validate_leaf(
        self,
        value: Any,
        path: list[str],
        schema_node: dict[str, Any],
        result: FieldValidationResult,
    ) -> None:
        """Validate a leaf value against enum, pattern, and type constraints."""
        # Presence flags or empty values — skip
        if value is None or value is True or value == "":
            return

        # List values: validate each element individually
        if isinstance(value, list):
            for item in value:
                self._validate_leaf(item, path, schema_node, result)
            return

        str_value = str(value)
        dot_path = ".".join(path)

        # 1. Enum check
        has_fallback = schema_node.get("r") is not None or schema_node.get("tr") is not None
        enum_idx = schema_node.get("e")
        if enum_idx is not None and enum_idx < len(self._enums):
            allowed = self._enums[enum_idx]
            if str_value not in allowed:
                if has_fallback:
                    pass  # Fall through to pattern/type checks
                elif _is_numeric_or_range(str_value):
                    return  # Accept numeric values — XSD union types often allow them
                elif _has_enum_placeholder(allowed):
                    return  # XSD union with placeholder for arbitrary values
                else:
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

        # IP address validation
        if tr_lower in _IPV4_TYPES or tr_lower in _IPV6_TYPES or tr_lower in _IP_ANY_TYPES:
            self._validate_ip(str_value, dot_path, tr_lower, result)
            return

        # Integer validation
        if type_ref in _INTEGER_TYPES:
            self._validate_integer(str_value, dot_path, type_ref, result)
            return

        # Boolean validation
        if type_ref in _BOOLEAN_TYPES and str_value.lower() not in ("true", "false", "1", "0"):
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
                dot_path = ".".join([*path, child_name])
                result.warnings.append(
                    FieldError(
                        path=dot_path,
                        message=f"Missing mandatory field {child_name!r}",
                        value=None,
                        expected=f"required field {child_name!r}",
                    )
                )
