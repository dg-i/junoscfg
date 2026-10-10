"""Junoscfg validation: validate Junos configurations against the Junos XSD schema.

Provides data types for validation results and errors, used by all
format-specific validators and the unified ``JunosValidator`` facade.

The door also names the stages of the build-time pipeline that
``ArtifactBuilder`` composes and ``junoscfg schema generate`` runs: extract the
XSD from a NETCONF dump, parse it into a ``SchemaNode`` tree, apply the
registered fixes, and write the grammar, the JSON and YAML schemas and the
structure tree; and the format validators ``JunosValidator`` builds from those
artifacts. A caller can run one stage on its own, as the tests do.
"""

from __future__ import annotations

from dataclasses import dataclass
from importlib import import_module
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # the heavy modules stay lazy; see __getattr__ below
    from junoscfg.validate.artifact_builder import (
        ArtifactBuilder,
        read_structure_tree,
        write_structure_tree,
    )
    from junoscfg.validate.grammar_generator import generate_lark_grammar, write_lark_grammar
    from junoscfg.validate.json_yaml_validator import JsonYamlValidator
    from junoscfg.validate.schema_generator import generate_json_schema, write_json_schema
    from junoscfg.validate.schema_node import Combinator, SchemaNode, find_all, navigate, walk
    from junoscfg.validate.set_validator import SetValidator
    from junoscfg.validate.structured_validator import StructuredValidator
    from junoscfg.validate.validator import JunosValidator
    from junoscfg.validate.xml_validator import XmlValidator
    from junoscfg.validate.xsd_extractor import extract_xsd
    from junoscfg.validate.xsd_fixes import ALL_FIXES, XsdFix, apply_all_fixes, get_fix_count
    from junoscfg.validate.xsd_parser import parse_xsd

__all__ = [
    "ALL_FIXES",
    "ArtifactBuilder",
    "Combinator",
    "JsonYamlValidator",
    "JunosValidator",
    "SchemaLoadError",
    "SchemaNode",
    "SetValidator",
    "StructuredValidator",
    "ValidationError",
    "ValidationResult",
    "XmlValidator",
    "XsdFix",
    "apply_all_fixes",
    "extract_xsd",
    "find_all",
    "generate_json_schema",
    "generate_lark_grammar",
    "get_fix_count",
    "navigate",
    "parse_xsd",
    "read_structure_tree",
    "walk",
    "write_json_schema",
    "write_lark_grammar",
    "write_structure_tree",
]

#: Every name this door resolves lazily, and the submodule that defines it.
_LAZY: dict[str, str] = {
    "ArtifactBuilder": "artifact_builder",
    "read_structure_tree": "artifact_builder",
    "write_structure_tree": "artifact_builder",
    "generate_lark_grammar": "grammar_generator",
    "write_lark_grammar": "grammar_generator",
    "JsonYamlValidator": "json_yaml_validator",
    "generate_json_schema": "schema_generator",
    "write_json_schema": "schema_generator",
    "Combinator": "schema_node",
    "SchemaNode": "schema_node",
    "find_all": "schema_node",
    "navigate": "schema_node",
    "walk": "schema_node",
    "SetValidator": "set_validator",
    "StructuredValidator": "structured_validator",
    "JunosValidator": "validator",
    "XmlValidator": "xml_validator",
    "extract_xsd": "xsd_extractor",
    "ALL_FIXES": "xsd_fixes",
    "XsdFix": "xsd_fixes",
    "apply_all_fixes": "xsd_fixes",
    "get_fix_count": "xsd_fixes",
    "parse_xsd": "xsd_parser",
}


@dataclass(frozen=True, slots=True)
class ValidationError:
    """A single validation error with optional location info.

    Attributes:
        message: Human-readable error description.
        line: Line number where the error was found, if available.
        path: Configuration path where the error was found, if available.
    """

    message: str
    line: int | None = None
    path: str | None = None


@dataclass(frozen=True, slots=True)
class ValidationResult:
    """Result of validating a configuration.

    Attributes:
        valid: ``True`` if the configuration passed validation.
        errors: Tuple of validation errors found.
        warnings: Tuple of non-fatal validation warnings.
    """

    valid: bool
    errors: tuple[ValidationError, ...] = ()
    warnings: tuple[ValidationError, ...] = ()


class SchemaLoadError(Exception):
    """Raised when validation artifacts cannot be loaded.

    This typically occurs when the artifacts directory does not exist
    or is missing required files (XSD, JSON Schema, Lark grammar).
    """


def __getattr__(name: str) -> object:
    """Resolve the heavy re-exports on first use.

    The pipeline and the validators pull in lxml, Lark, jsonschema and the
    schema artifacts; importing them eagerly would make ``junoscfg.validate``
    costly for callers that only want ``ValidationResult``.
    """
    module = _LAZY.get(name)
    if module is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    value = getattr(import_module(f"{__name__}.{module}"), name)
    globals()[name] = value
    return value
