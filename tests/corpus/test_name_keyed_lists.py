"""`name`-keyed lists render byte for byte as they did on 0.14.0.

A declared byte-identity requirement (spec conversion/entry-keys), so the
comparison is of bytes, not of meaning. Pinned before identifier-key-fields
and expected to pass on both sides of it: the guard against that change moving
what it does not name. Digests of every output format from every input format
of `examples/router1.*`, and of the committed set corpus less the lines the
change rekeys.
"""

from __future__ import annotations

import hashlib

from junoscfg import Format, convert_config
from tests.support.paths import EXAMPLES, TEST_DATA

OUTPUTS = (Format.SET, Format.STRUCTURED, Format.JSON, Format.YAML)
#: The statements identifier-key-fields rekeyed: their lines are left out.
REKEYED = (
    "route-filter",
    "prefix-list-filter",
    "source-address-filter",
    "attributes-match",
    "as-path-neighbors",
    "as-path-origins",
    "as-path-transits",
    " then community ",
    "apply-groups",
)


def _render(source: str, fmt: Format) -> str:
    """Every output of *source*, or the name of the error each raised, joined."""
    parts = []
    for out in OUTPUTS:
        try:
            parts.append(convert_config(source, from_format=fmt, to_format=out, validate=False))
        except Exception as exc:  # noqa: BLE001 -- the failure itself is pinned
            parts.append(f"ERROR {type(exc).__name__}")
    return "\x00".join(parts)


class TestNameKeyedListsAreUnchanged:
    """Every output of every committed `name`-keyed input is the bytes 0.14.0 wrote."""

    def test_corpus_output_is_byte_identical(self) -> None:
        examples = {
            "set": (Format.SET, "d09d9e47f09a48acf36e61ea48942e09a3d206d21aa32d763bfb9c1510e4de3a"),
            "conf": (
                Format.STRUCTURED,
                "d09d9e47f09a48acf36e61ea48942e09a3d206d21aa32d763bfb9c1510e4de3a",
            ),
            "json": (
                Format.JSON,
                "da3e1e578f8ec992f13d10a657745078d36f110e12639828b2f24bc435d30097",
            ),
            "xml": (Format.XML, "da3e1e578f8ec992f13d10a657745078d36f110e12639828b2f24bc435d30097"),
        }
        for suffix, (fmt, digest) in examples.items():
            source = (EXAMPLES / f"router1.{suffix}").read_text(encoding="utf-8")
            rendered = _render(source, fmt)
            assert hashlib.sha256(rendered.encode()).hexdigest() == digest, suffix

        lines = [
            line.strip()
            for line in (TEST_DATA / "set_corpus.txt").read_text(encoding="utf-8").splitlines()
            if line.startswith("set ")
        ]
        kept = [line for line in lines if not any(k in line + " " for k in REKEYED)]
        assert (len(lines), len(kept)) == (117, 105)
        rendered = "\x01".join(_render(line, Format.SET) for line in kept)
        assert (
            hashlib.sha256(rendered.encode()).hexdigest()
            == "dcbaa53f5b228b48f2855dcc4b1b8b0c94a09289ba48df59c26c812988e22c2c"
        )
