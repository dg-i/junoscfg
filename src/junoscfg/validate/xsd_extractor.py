"""Extract XSD schema from a NETCONF dump file.

Efficiently scans large files line-by-line looking for <xsd:schema> ... </xsd:schema>.
"""

from __future__ import annotations

from pathlib import Path


def extract_xsd(source: str | Path) -> str:
    """Extract the XSD schema text from a NETCONF dump.

    Args:
        source: Path to NETCONF dump file, or the XML string itself.

    Returns:
        The extracted XSD schema as a string.

    Raises:
        ValueError: If no XSD schema is found.
    """
    if isinstance(source, Path) or (
        isinstance(source, str) and "\n" not in source[:200] and Path(source).exists()
    ):
        return _extract_from_file(Path(source))
    return _extract_from_string(source)


def _extract_from_file(path: Path) -> str:
    """Line-by-line scan for efficiency on large files."""
    lines: list[str] = []
    inside = False

    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            if not inside:
                if "<xsd:schema" in line:
                    inside = True
                    lines.append(line)
            else:
                lines.append(line)
                if "</xsd:schema>" in line:
                    break

    if not lines:
        raise ValueError(f"No <xsd:schema> found in {path}")

    return "".join(lines)


def _extract_from_string(text: str) -> str:
    """Extract from an in-memory string."""
    start = text.find("<xsd:schema")
    if start == -1:
        raise ValueError("No <xsd:schema> found in input")

    end = text.find("</xsd:schema>", start)
    if end == -1:
        raise ValueError("No closing </xsd:schema> found in input")

    return text[start : end + len("</xsd:schema>")]
