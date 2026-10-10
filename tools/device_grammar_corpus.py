"""Choose the grammar corpus: few device set lines that exercise every rule the many do.

Every `set` line a device printed in `tests/data/device/` is valid Junos. All of
them through the shipped Earley grammar take minutes, too long for the suite,
so this tool parses each once, collects the grammar rules each line's parse
uses, and picks lines greedily until every rule any device line uses is used
by one picked line. Lines the grammar rejects are false rejections of valid
configuration: every one is kept, so none is lost from sight.

The result, `tests/data/device/grammar-corpus.json`, is what
`tests/corpus/test_set_corpus.py` checks in every run; `--device-grammar`
checks every device line by hand. Rerun after a grammar change or a new
capture: ``uv run python tools/device_grammar_corpus.py`` (several minutes).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from lark import Lark, Tree
from lark.exceptions import UnexpectedInput

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from junoscfg.display import find_artifact, read_artifact_text  # noqa: E402
from tests.support.devices import DEVICE_DATA, captures  # noqa: E402
from tests.support.paths import ARTIFACT_DIR, PRIVATE_DATA  # noqa: E402

CORPUS = DEVICE_DATA / "grammar-corpus.json"


def device_set_lines() -> dict[str, str]:
    """Every distinct `set` line a device printed, with where it was first seen.

    Drawn from every capture under private_test_data/ where it exists, the
    devices and configurations the repository does not carry included, so the
    corpus covers what they exercise; from the committed captures otherwise.
    """
    found: dict[str, str] = {}
    folders = sorted(PRIVATE_DATA.glob("jvd_derived_data*"))
    if folders:
        for folder in folders:
            for path in sorted(folder.glob("*.set")):
                if ".device." in path.name:
                    continue
                for line in path.read_text(encoding="utf-8").splitlines():
                    if line.startswith("set "):
                        found.setdefault(line, f"{folder.name}/{path.stem}")
    else:
        for capture in captures():
            for line in capture.device_set():
                if line.startswith("set "):
                    found.setdefault(line, capture.key)
    return dict(sorted(found.items()))


def _rules(tree: Tree) -> frozenset[str]:
    return frozenset(str(sub.data) for sub in tree.iter_subtrees())


def main() -> int:
    """Parse every device line, pick a covering subset, write the corpus."""
    grammar = read_artifact_text(find_artifact(ARTIFACT_DIR, "junos-set.lark"))
    parser = Lark(grammar, parser="earley")
    lines = device_set_lines()
    used: dict[str, frozenset[str]] = {}
    rejected = []
    for n, line in enumerate(sorted(lines), 1):
        try:
            used[line] = _rules(parser.parse(line))
        except UnexpectedInput:
            rejected.append(line)
        if n % 1000 == 0:
            print(f"{n}/{len(lines)}", file=sys.stderr)
    needed = frozenset().union(*used.values())
    picked, covered = [], frozenset()
    while covered != needed:
        line = max(sorted(used), key=lambda candidate: len(used[candidate] - covered))
        picked.append(line)
        covered |= used[line]
    corpus = {
        "about": (
            "Device set lines covering every grammar rule the captured devices' lines use "
            "(tools/device_grammar_corpus.py), and every device line the shipped grammar "
            "rejects. A rejection is a false rejection of valid configuration. Each line "
            "names the capture it was first seen in."
        ),
        "device_lines": len(lines),
        "rules": len(needed),
        "accepted": {line: lines[line] for line in sorted(picked)},
        "rejected": {line: lines[line] for line in rejected},
    }
    CORPUS.write_text(json.dumps(corpus, indent=1) + "\n", encoding="utf-8")
    print(
        f"{len(picked)} lines cover {len(needed)} rules of {len(lines)}; {len(rejected)} rejected"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
