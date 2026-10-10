"""``--regen-schema`` rebuilds from the shipped release's dump, never another.

``find_xsd_source`` used to take whichever dump sorted newest under
``private_test_data/schemas/``, so the documented pre-commit step would have
replaced the shipped 25.2R2 artifacts with whatever a developer had synced
last, as a side effect of a file name. The release is an explicit choice now:
the one dump whose release train matches the bundled metadata's, or
``JUNOSCFG_XSD_SOURCE``, and an error naming both when neither is there.
"""

from __future__ import annotations

import subprocess
import sys
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from pathlib import Path

from tests.conftest import (
    REGEN_SOURCE_EXIT,
    XsdSourceError,
    find_xsd_source,
    shipped_release_train,
)


def _dump(directory: Path, name: str, release: str) -> Path:
    """A file that ``schema_data.read_version`` reads as *release*."""
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / name
    path.write_text(f'<xsd:schema xmlns:junos="http://xml.juniper.net/junos/{release}/junos"/>\n')
    return path


class TestTheShippedTrain:
    def test_it_comes_from_the_bundled_metadata(self) -> None:
        assert shipped_release_train() == "25.2"


class TestFindXsdSource:
    def test_the_shipped_train_is_chosen_over_a_newer_dump(self, tmp_path: Path) -> None:
        """The regression: newest sorted first, and 26.1 would have shipped."""
        wanted = _dump(tmp_path / "schemas", "25.2R2-S1.5_qfx5120.xsd", "25.2R2-S1.5")
        _dump(tmp_path / "schemas", "26.1R1_mx.xsd", "26.1R1")
        assert find_xsd_source(train="25.2", schemas_dir=tmp_path / "schemas") == wanted

    def test_no_matching_dump_names_the_train_and_the_override(self, tmp_path: Path) -> None:
        _dump(tmp_path / "schemas", "23.2R2-S7.5_vmx.xsd", "23.2R2-S7.5")
        with pytest.raises(XsdSourceError, match=r"25\.2.*JUNOSCFG_XSD_SOURCE"):
            find_xsd_source(train="25.2", schemas_dir=tmp_path / "schemas")

    def test_two_matching_dumps_are_an_error_listing_both(self, tmp_path: Path) -> None:
        _dump(tmp_path / "schemas", "25.2R2-S1.5_qfx5120.xsd", "25.2R2-S1.5")
        _dump(tmp_path / "schemas", "25.2R1_ex4100.xsd", "25.2R1")
        with pytest.raises(XsdSourceError, match=r"qfx5120.*ex4100|ex4100.*qfx5120"):
            find_xsd_source(train="25.2", schemas_dir=tmp_path / "schemas")

    def test_a_train_does_not_match_its_own_prefix(self, tmp_path: Path) -> None:
        _dump(tmp_path / "schemas", "25.20R1.xsd", "25.20R1")
        with pytest.raises(XsdSourceError):
            find_xsd_source(train="25.2", schemas_dir=tmp_path / "schemas")

    def test_the_override_wins_whatever_its_release(self, tmp_path: Path) -> None:
        """Moving the shipped release is a choice, made by naming the dump."""
        other = _dump(tmp_path, "23.2R2-S7.5_vmx.xsd", "23.2R2-S7.5")
        _dump(tmp_path / "schemas", "25.2R2-S1.5_qfx5120.xsd", "25.2R2-S1.5")
        assert (
            find_xsd_source(train="25.2", schemas_dir=tmp_path / "schemas", override=str(other))
            == other
        )

    def test_a_missing_override_is_an_error(self, tmp_path: Path) -> None:
        with pytest.raises(XsdSourceError, match="JUNOSCFG_XSD_SOURCE"):
            find_xsd_source(
                train="25.2", schemas_dir=tmp_path / "schemas", override=str(tmp_path / "gone.xsd")
            )

    def test_a_legacy_dump_beside_the_directory_still_counts(self, tmp_path: Path) -> None:
        legacy = _dump(tmp_path, "config.xsd", "25.2R2")
        assert (
            find_xsd_source(train="25.2", schemas_dir=tmp_path / "schemas", legacy_dir=tmp_path)
            == legacy
        )

    def test_an_empty_directory_is_an_error(self, tmp_path: Path) -> None:
        with pytest.raises(XsdSourceError, match="no dump of the shipped release 25.2"):
            find_xsd_source(
                train="25.2", schemas_dir=tmp_path / "schemas", legacy_dir=tmp_path / "none"
            )

    def test_a_service_train_of_the_release_counts(self, tmp_path: Path) -> None:
        """`25.2X75-D10` is 25.2 as much as `25.2R2-S1.5-EVO` is."""
        wanted = _dump(tmp_path / "schemas", "25.2X75-D10.xsd", "25.2X75-D10")
        assert find_xsd_source(train="25.2", schemas_dir=tmp_path / "schemas") == wanted

    def test_an_empty_override_is_an_error_not_a_fallback(self, tmp_path: Path) -> None:
        """`export JUNOSCFG_XSD_SOURCE=$UNSET` must not rebuild from the default."""
        _dump(tmp_path / "schemas", "25.2R2-S1.5_qfx5120.xsd", "25.2R2-S1.5")
        with pytest.raises(XsdSourceError, match="is not a file"):
            find_xsd_source(train="25.2", schemas_dir=tmp_path / "schemas", override="")

    def test_an_override_without_a_release_in_its_header_is_an_error(self, tmp_path: Path) -> None:
        """Artifacts built from it would say `unknown` and match no dump again."""
        bare = tmp_path / "bare.xsd"
        bare.write_text("<xsd:schema/>\n")
        with pytest.raises(XsdSourceError, match="declares no Junos release"):
            find_xsd_source(train="25.2", schemas_dir=tmp_path / "schemas", override=str(bare))

    def test_a_lookup_renames_nothing(self, tmp_path: Path) -> None:
        """A staged `new.xsd` is read by its header and left where it is, even
        when the lookup only raises; promotion belongs to the schema tier."""
        staged = _dump(tmp_path / "schemas", "new.xsd", "26.1R1")
        with pytest.raises(XsdSourceError):
            find_xsd_source(train="25.2", schemas_dir=tmp_path / "schemas")
        assert staged.is_file() and sorted(p.name for p in (tmp_path / "schemas").iterdir()) == [
            "new.xsd"
        ]
        wanted = _dump(tmp_path / "schemas", "new.xsd", "25.2R2-S1.5")
        assert find_xsd_source(train="25.2", schemas_dir=tmp_path / "schemas") == wanted
        assert wanted.is_file()

    def test_a_directory_named_like_a_dump_is_ignored(self, tmp_path: Path) -> None:
        (tmp_path / "schemas" / "odd.xsd").mkdir(parents=True)
        wanted = _dump(tmp_path / "schemas", "25.2R2-S1.5_qfx5120.xsd", "25.2R2-S1.5")
        assert find_xsd_source(train="25.2", schemas_dir=tmp_path / "schemas") == wanted

    def test_the_error_names_each_dump_with_its_release(self, tmp_path: Path) -> None:
        _dump(tmp_path / "schemas", "a.xsd", "23.2R2-S7.5")
        _dump(tmp_path, "legacy.xsd", "21.4R0")
        with pytest.raises(
            XsdSourceError, match=r"a\.xsd \(23\.2R2-S7\.5\).*legacy\.xsd \(21\.4R0\)"
        ):
            find_xsd_source(train="25.2", schemas_dir=tmp_path / "schemas", legacy_dir=tmp_path)


class TestTheRunStops:
    def test_before_collection_with_its_own_exit_code(self, tmp_path: Path) -> None:
        """`--collect-only` and a `-k` that matches nothing used to skip the
        check entirely; pytest keeps 0 to 5, so the code is its own."""
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "pytest",
                "tests/unit/cli/test_cli.py",
                "-q",
                "--collect-only",
                "--regen-schema",
                "-p",
                "no:cacheprovider",
            ],
            env={"PATH": "/usr/bin:/bin", "JUNOSCFG_XSD_SOURCE": str(tmp_path / "gone.xsd")},
            capture_output=True,
            text=True,
            timeout=120,
        )
        assert result.returncode == REGEN_SOURCE_EXIT, result.stdout + result.stderr
        assert "gone.xsd" in result.stdout + result.stderr
        assert "collected" not in result.stdout
