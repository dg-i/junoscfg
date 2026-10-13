"""Isolated pure schema checks; imports only stdlib and declared distributions."""

from __future__ import annotations

import json
import sys
from pathlib import Path


def main() -> None:
    """Keep checker defaults explicit and bind changes through this file's hash."""
    operation, filename = sys.argv[1:]
    raw = Path(filename).read_bytes()
    if operation == "json-schema-draft202012":
        import jsonschema

        jsonschema.Draft202012Validator.check_schema(json.loads(raw))
    elif operation == "lark-grammar":
        import lark

        lark.Lark(raw.decode("utf-8"), start="start")
    else:
        raise ValueError("unknown schema content operation")


if __name__ == "__main__":
    main()
