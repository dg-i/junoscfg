"""Before/after comparison over the committed device captures.

Run from the tree being recorded (base worktree or change worktree), with
PYTHONDONTWRITEBYTECODE=1:

    uv run --locked python <path>/tools/compare_device_outputs.py record OUT.json [--anonymize]
    uv run --locked python <path>/tools/compare_device_outputs.py diff BASE.json HEAD.json

`record` converts every rendering in tests/data/device/manifest.json to set,
structured, json and yaml through junoscfg.convert_config_result and stores
output, diagnostics (source, severity, path), field-validation messages and
any exception class. With --anonymize it repeats each conversion with each
rule alone and with all rules on. Captures are read gunzipped in memory and
never written. `diff` compares two results by key and prints the counts.
"""

from __future__ import annotations

import difflib
import gzip
import json
import sys
from pathlib import Path

INPUTS = {"conf": "STRUCTURED", "set": "SET", "json": "JSON", "xml": "XML"}
OUTPUTS = ("SET", "STRUCTURED", "JSON", "YAML")
SALT = "compare-salt"
AS_NUMBERS = [64496, 64497, 64498, 64499, 64511]


def _rules(anonymize_config: type) -> dict[str, object]:
    single = {
        "ips": {"ips": True},
        "passwords": {"passwords": True},
        "communities": {"communities": True},
        "ssh_keys": {"ssh_keys": True},
        "identities": {"identities": True},
        "groups": {"groups": True},
        "descriptions": {"descriptions": True},
        "as_numbers": {"as_numbers": AS_NUMBERS},
        "sensitive_words": {"sensitive_words": ["customer"]},
        "sensitive_patterns": {"sensitive_patterns": [r"LAX\d+"]},
    }
    every: dict[str, object] = {}
    for options in single.values():
        every.update(options)
    rules = {name: anonymize_config(salt=SALT, **opts) for name, opts in single.items()}
    rules["all"] = anonymize_config(salt=SALT, **every)
    return rules


def _renderings(root: Path) -> list[tuple[str, Path]]:
    manifest = json.loads((root / "tests/data/device/manifest.json").read_text())
    found = []
    for capture in manifest["captures"]:
        folder = root / "tests/data/device" / capture["source"] / capture["device"]
        for suffix in INPUTS:
            path = folder / f"{capture['name']}.{suffix}.gz"
            if path.is_file():
                key = f"{capture['source']}/{capture['device']}/{capture['name']}.{suffix}"
                found.append((key, path))
    return found


def _one(convert, fmt, text: str, src: str, dst: str, anon) -> dict[str, object]:
    try:
        result = convert(text, from_format=fmt[src], to_format=fmt[dst], anon_config=anon)
    except Exception as exc:  # noqa: BLE001 - the class is the record
        return {"exception": type(exc).__name__}
    return {
        "output": result.output,
        "diagnostics": sorted({(d.source, d.severity, d.path or "") for d in result.diagnostics}),
        "field_validation": sorted(
            d.message for d in result.diagnostics if d.source.startswith("field")
        ),
    }


def record(out: Path, anonymize: bool) -> None:
    """Record the current tree's available capture conversions as sorted JSON."""
    import junoscfg
    from junoscfg.anonymize import AnonymizeConfig

    fmt = {f.name: f for f in junoscfg.Format}
    runs: dict[str, object] = {"plain": None}
    if anonymize:
        runs.update(_rules(AnonymizeConfig))
    results: dict[str, object] = {}
    for key, path in _renderings(Path.cwd()):
        text = gzip.decompress(path.read_bytes()).decode("utf-8")
        src = INPUTS[key.rsplit(".", 1)[1]]
        for dst in OUTPUTS:
            for rule, anon in runs.items():
                results[f"{key} -> {dst.lower()} [{rule}]"] = _one(
                    junoscfg.convert_config_result, fmt, text, src, dst, anon
                )
    out.write_text(json.dumps(results, indent=1, sort_keys=True, default=list))
    print(f"{len(results)} conversions recorded in {out}")


def diff(base: Path, head: Path) -> None:
    """Print every changed conversion field over the union of record keys."""
    a, b = json.loads(base.read_text()), json.loads(head.read_text())
    keys = sorted(set(a) | set(b))
    changed = [k for k in keys if a.get(k) != b.get(k)]
    print(f"{len(changed)} of {len(keys)} conversions differ")
    for key in changed:
        print(f"\n=== {key}")
        left, right = a.get(key) or {}, b.get(key) or {}
        for field in sorted(set(left) | set(right)):
            if left.get(field) == right.get(field):
                continue
            if field == "output":
                lines = difflib.unified_diff(
                    str(left.get(field, "")).splitlines(),
                    str(right.get(field, "")).splitlines(),
                    "base",
                    "head",
                    n=0,
                    lineterm="",
                )
                print("\n".join(lines))
            else:
                print(f"{field}: base {left.get(field)!r}\n{field}: head {right.get(field)!r}")


if __name__ == "__main__":
    if sys.argv[1:2] == ["record"]:
        record(Path(sys.argv[2]), "--anonymize" in sys.argv[3:])
    elif sys.argv[1:2] == ["diff"]:
        diff(Path(sys.argv[2]), Path(sys.argv[3]))
    else:
        sys.exit(__doc__)
