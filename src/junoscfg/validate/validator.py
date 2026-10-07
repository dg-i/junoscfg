"""JunosValidator: unified facade for all validation formats.

Lazy-loads format-specific validators on first use. Supports custom artifacts
directory via constructor arg, JUNOSCFG_ARTIFACTS env var, or bundled defaults.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from junoscfg.display import find_artifact, read_artifact_text, resolve_artifacts_dir
from junoscfg.validate import SchemaLoadError, ValidationResult

if TYPE_CHECKING:
    from pathlib import Path


class JunosValidator:
    """Unified validation facade for all Junos configuration formats."""

    def __init__(self, artifacts_dir: str | Path | None = None) -> None:
        """Initialize the validator.

        Artifacts are resolved by `display.resolve_artifacts_dir`, the one
        rule the whole package uses: explicit argument, then a process
        override, then JUNOSCFG_ARTIFACTS, then the bundled directory.

        Args:
            artifacts_dir: Path to directory containing validation artifacts.

        Raises:
            SchemaLoadError: If artifacts directory does not exist.
        """

        # One resolver for the package; see display.constants. This used to be
        # a second, independent if/elif here, and conversion had a third rule
        # that honoured neither the argument nor the environment variable.
        self._artifacts_dir = resolve_artifacts_dir(artifacts_dir)

        if not self._artifacts_dir.exists():
            raise SchemaLoadError(f"Artifacts directory not found: {self._artifacts_dir}")

        # Lazy-loaded validators
        self._xml_validator = None
        self._json_yaml_validator = None
        self._set_validator = None
        self._structured_validator = None
        self._metadata: dict | None = None

    @property
    def schema_version(self) -> str:
        """Junos version the schema was generated from."""
        return self._load_metadata().get("junos_version", "unknown")

    @property
    def generated_at(self) -> str:
        """Timestamp when artifacts were generated."""
        return self._load_metadata().get("generated_at", "unknown")

    def validate_xml(self, source: str) -> ValidationResult:
        """Validate XML configuration.

        Args:
            source: XML configuration as a string.

        Returns:
            ValidationResult with errors if invalid.
        """
        if self._xml_validator is None:
            from junoscfg.validate.xml_validator import XmlValidator

            xsd_path = find_artifact(self._artifacts_dir, "junos-validated.xsd")
            if xsd_path is None:
                raise SchemaLoadError(
                    f"XSD not found: {xsd_path}. XML validation requires a cleaned XSD artifact."
                )
            self._xml_validator = XmlValidator(xsd_path)
        return self._xml_validator.validate(source)

    def validate_json(self, source: str) -> ValidationResult:
        """Validate JSON configuration.

        Args:
            source: JSON configuration as a string.

        Returns:
            ValidationResult with errors if invalid.
        """
        self._ensure_json_yaml_validator()
        return self._json_yaml_validator.validate_json(source)  # type: ignore[union-attr]

    def validate_yaml(self, source: str) -> ValidationResult:
        """Validate YAML configuration.

        Args:
            source: YAML configuration as a string.

        Returns:
            ValidationResult with errors if invalid.
        """
        self._ensure_json_yaml_validator()
        return self._json_yaml_validator.validate_yaml(source)  # type: ignore[union-attr]

    def validate_set(self, source: str) -> ValidationResult:
        """Validate set commands.

        Args:
            source: Set commands as a string (one per line).

        Returns:
            ValidationResult with errors if invalid.
        """
        if self._set_validator is None:
            from junoscfg.validate.set_validator import SetValidator

            grammar_path = find_artifact(self._artifacts_dir, "junos-set.lark")
            if grammar_path is None:
                raise SchemaLoadError(f"Lark grammar not found: {grammar_path}")
            self._set_validator = SetValidator(grammar_path)
        return self._set_validator.validate(source)

    def validate_structured(self, source: str) -> ValidationResult:
        """Validate structured (curly-brace) configuration.

        Converts to set commands first, then validates.

        Args:
            source: Structured configuration as a string.

        Returns:
            ValidationResult with errors if invalid.
        """
        if self._structured_validator is None:
            from junoscfg.validate.structured_validator import StructuredValidator

            # Ensure set validator is loaded
            if self._set_validator is None:
                from junoscfg.validate.set_validator import SetValidator

                grammar_path = find_artifact(self._artifacts_dir, "junos-set.lark")
                if grammar_path is None:
                    raise SchemaLoadError(f"Lark grammar not found: {grammar_path}")
                self._set_validator = SetValidator(grammar_path)
            self._structured_validator = StructuredValidator(self._set_validator)
        return self._structured_validator.validate(source)

    def _ensure_json_yaml_validator(self) -> None:
        """Lazy-load JSON/YAML validator."""
        if self._json_yaml_validator is None:
            from junoscfg.validate.json_yaml_validator import JsonYamlValidator

            json_path = find_artifact(self._artifacts_dir, "junos-json-schema.json")
            yaml_path = find_artifact(self._artifacts_dir, "junos-yaml-schema.json")

            self._json_yaml_validator = JsonYamlValidator(
                json_schema_path=json_path,
                yaml_schema_path=yaml_path,
            )

    def _load_metadata(self) -> dict:
        """Load and cache schema metadata."""
        if self._metadata is None:
            meta_path = find_artifact(self._artifacts_dir, "junos-schema-meta.json")
            if meta_path is not None:
                self._metadata = json.loads(read_artifact_text(meta_path))
            else:
                self._metadata = {}
        return self._metadata
