"""How a synced device dump gets its name.

These need no dump of their own, so they are not marked ``schema``: they build
a few bytes of XML in a temp directory and check the naming rule.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from . import schema_data

if TYPE_CHECKING:
    from pathlib import Path


class TestPlatformInTheName:
    """The platform is recorded at capture time, never read from the dump.

    A NETCONF XSD is release-wide: every dump names every platform as enum
    values for hardware-specific configuration, and feature depth tracks the
    release rather than the hardware — `unified-edge` is 1,771 nodes in both a
    vMX's 23.2R2 dump and the bundled 24.4R0. So `show version` is the only
    source, and it has to be written down beside the file.
    """

    def test_a_recorded_platform_reaches_the_name(self, tmp_path: Path) -> None:
        (tmp_path / schema_data.STAGING_NAME).write_text(
            '<x xmlns:junos="http://xml.juniper.net/junos/23.2R2-S7.5/junos"/>'
        )
        (tmp_path / schema_data.STAGING_PLATFORM).write_text("Model: vmx\n")
        assert schema_data.promote_staged(tmp_path).name == "23.2R2-S7.5-vmx.xsd"

    def test_the_marker_is_consumed(self, tmp_path: Path) -> None:
        (tmp_path / schema_data.STAGING_NAME).write_text(
            '<x xmlns:junos="http://xml.juniper.net/junos/23.2R2/junos"/>'
        )
        (tmp_path / schema_data.STAGING_PLATFORM).write_text("vmx")
        schema_data.promote_staged(tmp_path)
        assert not (tmp_path / schema_data.STAGING_PLATFORM).exists()

    def test_without_a_marker_the_release_stands_alone(self, tmp_path: Path) -> None:
        (tmp_path / schema_data.STAGING_NAME).write_text(
            '<x xmlns:junos="http://xml.juniper.net/junos/24.4R0/junos"/>'
        )
        assert schema_data.promote_staged(tmp_path).name == "24.4R0.xsd"

    def test_an_explicit_platform_beats_the_marker(self, tmp_path: Path) -> None:
        (tmp_path / schema_data.STAGING_NAME).write_text(
            '<x xmlns:junos="http://xml.juniper.net/junos/23.4R2/junos"/>'
        )
        (tmp_path / schema_data.STAGING_PLATFORM).write_text("vmx")
        assert schema_data.promote_staged(tmp_path, platform="qfx5120").name == (
            "23.4R2-qfx5120.xsd"
        )
