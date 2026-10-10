"""Prove that no case of the suite was lost in the restructuring.

``ledger-before.txt`` is every node id on master before this change.
``moves.tsv`` is the pure-rename commit's path map. Each row of
``ledger/*.tsv`` is ``<id after the move>\\t<new id | dropped>\\t<note>``; an
id without ``[...]`` stands for all of its parametrisations, and so does a new
id. A node is accounted for when its moved id still exists, or a row maps it
to an id that exists, or a row drops it with a note.

Run from the repository root: ``uv run python openspec/changes/test-architecture/check_ledger.py``.
With ``--rewrite FILE...`` it also rewrites the test ids named in those files.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def _base(node: str) -> str:
    return node.split("[", 1)[0]


def collected() -> set[str]:
    """Every node id the suite collects now."""
    out = subprocess.run(
        [sys.executable, "-m", "pytest", "--co", "-q", "-p", "no:cacheprovider", "tests"],
        capture_output=True,
        text=True,
        check=False,
    ).stdout
    return {line for line in out.splitlines() if "::" in line}


def moves() -> dict[str, str]:
    """The pure-rename commit's path map, old to new."""
    pairs = (line.split("\t") for line in (HERE / "moves.tsv").read_text().splitlines() if line)
    return dict(pairs)


def rows() -> dict[str, tuple[str, str, str]]:
    """The ledger rows: moved id -> (new id or dropped, note, where)."""
    found: dict[str, tuple[str, str, str]] = {}
    for sheet in sorted((HERE / "ledger").glob("*.tsv")):
        for n, line in enumerate(sheet.read_text().splitlines(), 1):
            if not line.strip() or line.startswith("#"):
                continue
            old, new, *note = line.split("\t")
            if old in found:
                raise SystemExit(f"{sheet.name}:{n}: {old} is mapped twice")
            found[old] = (new, note[0] if note else "", f"{sheet.name}:{n}")
    return found


def moved(node: str, path_map: dict[str, str]) -> str:
    """*node* with its file path moved."""
    path, sep, rest = node.partition("::")
    return path_map.get(path, path) + sep + rest


def _exists(new: str, now: set[str], bases: set[str]) -> bool:
    return new in now or new in bases


def check() -> int:
    """Account for every baseline node; 1 if any is unaccounted for."""
    path_map = moves()
    sheet = rows()
    now = collected()
    bases = {_base(n) for n in now}
    before = [line for line in (HERE / "ledger-before.txt").read_text().splitlines() if line]
    kept = mapped = dropped = 0
    problems = []
    used = set()
    for node in before:
        node_moved = moved(node, path_map)
        row_key = node_moved if node_moved in sheet else _base(node_moved)
        if row_key in sheet:
            new, note, where = sheet[row_key]
            # A function-level row beside per-parametrisation rows is what the
            # document rewrite reads; it is used whenever one of them is.
            used.update({row_key, _base(row_key)})
            if new == "dropped":
                if not note:
                    problems.append(f"{where}: {node_moved} dropped without a reason")
                dropped += 1
            elif _exists(new, now, bases):
                mapped += 1
            else:
                problems.append(f"{where}: {node_moved} -> {new}, which does not exist")
        elif node_moved in now:
            kept += 1
        else:
            problems.append(f"unaccounted: {node_moved}")
    for key in sorted(set(sheet) - used):
        problems.append(f"{sheet[key][2]}: row for {key} matches no node of the baseline")
    for line in problems:
        print(line)
    print(
        f"\nbaseline {len(before)}: kept {kept}, mapped {mapped}, dropped {dropped}, "
        f"problems {len(problems)}; collected now {len(now)}"
    )
    return 1 if problems else 0


def rewrite(files: list[str]) -> None:
    """Rewrite the test ids named in documents by the sheet.

    A parametrised new id is kept as it is, being one node; a function-level one
    stands for the catalogue rows its note names, which the sheet keeps. On a
    ``Tests:`` line an id named twice is named once.
    """
    sheet = {
        _base(old): (new if "[" in new else _base(new))
        for old, (new, _, _) in rows().items()
        if new != "dropped"
    }
    if not sheet:
        return
    keys = sorted(sheet, key=len, reverse=True)
    pattern = re.compile("`(" + "|".join(re.escape(k) for k in keys) + r")`")
    for name in files:
        path = Path(name)
        text = path.read_text(encoding="utf-8")
        lines = []
        for line in text.split("\n"):
            line = pattern.sub(lambda m: f"`{sheet[m.group(1)]}`", line)
            if line.startswith("Tests:"):
                cited = dict.fromkeys(re.findall(r"`[^`]+`", line))
                line = "Tests: " + ", ".join(cited)
            lines.append(line)
        new_text = "\n".join(lines)
        if new_text != text:
            path.write_text(new_text, encoding="utf-8")
            print(f"rewrote {name}")


if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[1] == "--rewrite":
        rewrite(sys.argv[2:])
    sys.exit(check())
