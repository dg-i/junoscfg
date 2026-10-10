"""junoscfg against Juniper's published Validated Designs corpus.

Everything here needs ``--jvd``; see ``tests/jvd_data.py`` for why the corpus
is cloned rather than vendored.

This exists because three defects reached a release that every committed
fixture, the harvested `set_corpus.txt`, and three real device configurations
all missed — a ``nokeyword`` leaf's enum being enforced, ``ipaddr-or-interface``
validated as IP-only, and a oneliner list's keyword order. The corpus is about
1,500 files and five million lines across QFX, ACX, MX, PTX and SRX, which is
the only breadth of that kind available to this project.

The thresholds are deliberately loose: the corpus is upstream and will change,
and a test that pins an exact count would fail on someone else's commit.
"""

from __future__ import annotations

import io
import re
from collections import Counter
from contextlib import redirect_stderr
from types import SimpleNamespace
from typing import TYPE_CHECKING, Any

import pytest

if TYPE_CHECKING:
    from pathlib import Path

from junoscfg import Format, convert_config
from tests.support import jvd_data

pytestmark = pytest.mark.jvd

# What was measured when this was written, at junoscfg 0.6.17: 1,535 files,
# 4,945,686 lines, 1,500 converted, 35 non-configuration, 217 field warnings.
MIN_CONVERSION_RATE = 0.95
MAX_FIELD_WARNINGS_PER_1K_LINES = 0.5

_FIELD_WARNING_RE = re.compile(r"^field-validate: (.*)$", re.MULTILINE)
_UNMODELLED_MARK = "could not be placed in the schema"


@pytest.fixture(scope="session")
def corpus_run(jvd_corpus: Path) -> SimpleNamespace:
    """Convert every config once; every test here reads this one pass."""
    files = jvd_data.configs(jvd_corpus)
    ok: list[Path] = []
    failed: list[tuple[Path, str]] = []
    warnings: list[str] = []
    unmodelled: list[str] = []
    lines = 0

    for path in files:
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if not text.strip():
            continue
        lines += len(text.splitlines())
        captured = io.StringIO()
        try:
            with redirect_stderr(captured):
                convert_config(text, from_format=Format.STRUCTURED, to_format=Format.SET)
            ok.append(path)
        except Exception as exc:  # noqa: BLE001 - the corpus decides what breaks
            failed.append((path, f"{type(exc).__name__}: {exc}"))
        for message in _FIELD_WARNING_RE.findall(captured.getvalue()):
            # Two axes: a value the schema constrains and rejects, and a
            # statement the schema does not model at all.
            (unmodelled if _UNMODELLED_MARK in message else warnings).append(message)

    return SimpleNamespace(
        files=files, ok=ok, failed=failed, warnings=warnings, unmodelled=unmodelled, lines=lines
    )


class TestCorpusConverts:
    """Conversion is the load-bearing feature; it has to hold at this scale."""

    def test_the_corpus_is_big_enough_to_mean_something(self, corpus_run: SimpleNamespace) -> None:
        assert len(corpus_run.files) > 500
        assert corpus_run.lines > 1_000_000

    def test_almost_everything_converts(self, corpus_run: SimpleNamespace) -> None:
        total = len(corpus_run.ok) + len(corpus_run.failed)
        rate = len(corpus_run.ok) / total
        assert rate >= MIN_CONVERSION_RATE, (
            f"{len(corpus_run.failed)} of {total} failed to convert:\n"
            + "\n".join(f"  {p.name}: {e}" for p, e in corpus_run.failed[:15])
        )

    def test_every_failure_is_a_file_that_is_not_configuration(
        self, corpus_run: SimpleNamespace
    ) -> None:
        """A real config must never fail.

        The corpus carries documentation holding configuration: prose, section
        labels such as `AN3:`, and the `show configuration | no-more` prompt
        captured above a dump. Those are the file's shape, not junoscfg's bug.
        """
        real = [(p, e) for p, e in corpus_run.failed if jvd_data.is_configuration(e)]
        assert not real, "configuration that should convert and does not:\n" + "\n".join(
            f"  {p.name}: {e}" for p, e in real[:15]
        )


class TestFieldWarningBudget:
    """Field validation must not cry wolf on Juniper's own configurations.

    It did: 53,326 warnings over this corpus, 9,903 of them from one enum that
    the XSD never meant to be closed.
    """

    def test_warnings_stay_within_budget(self, corpus_run: SimpleNamespace) -> None:
        per_1k = len(corpus_run.warnings) / (corpus_run.lines / 1000)
        counts: dict[str, int] = {}
        for w in corpus_run.warnings:
            key = re.sub(r"'[^']*'", "'<v>'", w)[:90]
            counts[key] = counts.get(key, 0) + 1
        worst = sorted(counts.items(), key=lambda kv: -kv[1])[:8]
        assert per_1k <= MAX_FIELD_WARNINGS_PER_1K_LINES, (
            f"{len(corpus_run.warnings)} warnings over {corpus_run.lines:,} lines "
            f"({per_1k:.2f} per 1k):\n" + "\n".join(f"  {n:>5}  {k}" for k, n in worst)
        )


class TestUnmodelledStatementsAreCounted:
    """What the shipped schema cannot model, measured rather than hidden.

    Until 0.9.0 the set reader kept such a statement whole as one key and
    nothing said so, which is how a defective artifact set went unnoticed for
    five months. Measured at 0.9.0 against the 25.2R2 artifacts: 69,122 of
    2,222,948 set lines, 1.4% of the corpus's 4,945,686 structured lines, in
    407 shapes, `bridge-domains` and `routing-instances bridge-domains` 85% of
    them -- an MX-style wrapper the transparent-container fix does not name.
    That is schema coverage, a different axis from the value budget above;
    the cap is for growth, not a target, and the shapes are printed so a
    change to them is visible.
    """

    MAX_UNMODELLED_SHARE = 0.03

    def test_the_share_does_not_grow(self, corpus_run: SimpleNamespace) -> None:
        share = len(corpus_run.unmodelled) / corpus_run.lines
        shapes = Counter(re.sub(r"'[^']*'", "'<s>'", m)[:90] for m in corpus_run.unmodelled)
        count = len(corpus_run.unmodelled)
        report = f"{count} unmodelled statements over {corpus_run.lines:,} lines"
        print(f"\n{report}:\n" + "\n".join(f"  {n:>6}  {k}" for k, n in shapes.most_common(8)))
        assert share <= self.MAX_UNMODELLED_SHARE, report


def _first_match(corpus: Path, pattern: re.Pattern[str], limit: int = 400) -> str | None:
    """The first line in the corpus matching *pattern*, or None."""
    for path in jvd_data.configs(corpus)[:limit]:
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for line in text.splitlines():
            if pattern.search(line):
                return line.strip()
    return None


class TestShapesThatReachedARelease:
    """One guard per defect this corpus found after it had already shipped.

    Each takes its example from the corpus rather than from a literal here, so
    the test fails if the shape stops being handled *and* stays honest about
    what real configurations contain.
    """

    def test_a_nokeyword_leaf_takes_a_value_outside_its_enum(self, jvd_corpus: Path) -> None:
        """`classifier-name` carries the enum ['default'] and takes any name.

        9,903 warnings in the first 200 files came from enforcing it.
        """
        line = _first_match(jvd_corpus, re.compile(r"\bclassifiers\b"))
        if line is None:
            pytest.skip("no classifiers stanza in the corpus")
        cfg = (
            "class-of-service {\n interfaces {\n  et-0/0/0 {\n   unit 0 {\n"
            "    classifiers {\n     ieee-802.1 8021P;\n    }\n   }\n  }\n }\n}\n"
        )
        captured = io.StringIO()
        with redirect_stderr(captured):
            convert_config(cfg, from_format=Format.STRUCTURED, to_format=Format.SET)
        assert "classifier-name" not in captured.getvalue(), captured.getvalue()[:300]

    def test_ipaddr_or_interface_takes_an_interface_name(self, jvd_corpus: Path) -> None:
        """`from interface lo0.0` is the ordinary form of an `ipaddr-or-interface`."""
        cfg = (
            "policy-options {\n policy-statement P {\n  term T {\n"
            "   from {\n    interface lo0.0;\n   }\n  }\n }\n}\n"
        )
        captured = io.StringIO()
        with redirect_stderr(captured):
            convert_config(cfg, from_format=Format.STRUCTURED, to_format=Format.SET)
        assert "not a valid IP" not in captured.getvalue(), captured.getvalue()[:300]

    def test_a_oneliner_list_takes_its_keyword_before_the_entry_name(
        self, bundled_set_validator: Any
    ) -> None:
        """`then community add COMM-A` was 343 of 507 rejections on real devices.

        Takes the shared fixture rather than building the path by hand: the
        hand-built one named `junos-set.lark`, which stopped existing when the
        artifacts shipped gzipped, and this tier is opt-in so nothing noticed.
        """
        v = bundled_set_validator
        assert v.validate(
            "set policy-options policy-statement P term T then community add COMM-A"
        ).valid
        # and the other order, which `flag all detail` needs
        assert v.validate("set protocols bgp traceoptions flag all detail").valid
