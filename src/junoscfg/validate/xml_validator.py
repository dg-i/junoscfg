"""XML configuration validation via lxml XSD.

Validates Junos XML configurations against the cleaned XSD schema.
"""

from __future__ import annotations

from pathlib import Path

from lxml import etree

from junoscfg.validate import SchemaLoadError, ValidationError, ValidationResult

# Namespaces to strip before validation
_JUNOS_NS = "http://xml.juniper.net/junos/"
_INACTIVE_ATTR = "inactive"


class XmlValidator:
    """Validates Junos XML configurations against XSD."""

    def __init__(self, xsd_path: str | Path) -> None:
        """Load the XSD schema.

        Args:
            xsd_path: Path to the cleaned XSD file.

        Raises:
            SchemaLoadError: If the XSD cannot be loaded.
        """
        try:
            xsd_path = Path(xsd_path)
            schema_doc = etree.parse(str(xsd_path))
            self._schema = etree.XMLSchema(schema_doc)
        except Exception as e:
            raise SchemaLoadError(f"Failed to load XSD: {e}") from e

    def validate(self, xml_source: str) -> ValidationResult:
        """Validate XML configuration.

        Args:
            xml_source: XML configuration as a string.

        Returns:
            ValidationResult with errors if invalid.
        """
        try:
            doc = etree.fromstring(xml_source.encode("utf-8"))
        except etree.XMLSyntaxError as e:
            return ValidationResult(
                valid=False,
                errors=(ValidationError(message=f"XML syntax error: {e}", line=e.lineno),),
            )

        # Unwrap rpc-reply wrapper if present
        doc = _unwrap_rpc_reply(doc)

        # Strip Junos-specific attributes before validation
        _strip_junos_attrs(doc)

        is_valid = self._schema.validate(doc)

        if is_valid:
            return ValidationResult(valid=True)

        errors = tuple(
            ValidationError(
                message=str(err.message),
                line=err.line,
                path=err.path,
            )
            for err in self._schema.error_log
        )
        return ValidationResult(valid=False, errors=errors)


def _unwrap_rpc_reply(doc: etree._Element) -> etree._Element:
    """Unwrap <rpc-reply> wrapper if present, returning the configuration element."""
    local_name = etree.QName(doc.tag).localname if isinstance(doc.tag, str) else doc.tag

    if local_name == "rpc-reply":
        # Find <configuration> inside
        for child in doc:
            child_local = etree.QName(child.tag).localname if isinstance(child.tag, str) else ""
            if child_local == "configuration":
                return child
    return doc


def _strip_junos_attrs(element: etree._Element) -> None:
    """Remove inactive and junos:* attributes from all elements."""
    for el in element.iter():
        # Remove inactive attribute
        for attr in list(el.attrib):
            if attr == _INACTIVE_ATTR or (isinstance(attr, str) and _JUNOS_NS in attr):
                del el.attrib[attr]
