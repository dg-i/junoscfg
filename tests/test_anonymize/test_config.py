"""Tests for AnonymizeConfig dataclass and builders."""

from __future__ import annotations

from junoscfg.anonymize.config import AnonymizeConfig, build_config_from_cli, load_config_file


class TestAnonymizeConfig:
    def test_defaults_all_disabled(self) -> None:
        cfg = AnonymizeConfig()
        assert not cfg.any_enabled
        assert not cfg.ips
        assert not cfg.passwords
        assert cfg.salt is None
        assert cfg.log_level == "normal"
        assert cfg.include == []
        assert cfg.exclude == []

    def test_single_rule_enabled(self) -> None:
        cfg = AnonymizeConfig(ips=True)
        assert cfg.any_enabled
        assert cfg.ips
        assert not cfg.passwords

    def test_expand_all_enables_all_boolean_rules(self) -> None:
        cfg = AnonymizeConfig()
        cfg.expand_all()
        assert cfg.ips
        assert cfg.passwords
        assert cfg.communities
        assert cfg.ssh_keys
        assert cfg.identities
        assert cfg.groups
        assert cfg.descriptions
        assert cfg.ips_in_strings
        assert cfg.as_numbers_in_strings
        # as_numbers and sensitive_words are NOT expanded by all
        assert cfg.as_numbers == []
        assert cfg.sensitive_words == []

    def test_as_numbers_in_strings_default_false(self) -> None:
        cfg = AnonymizeConfig()
        assert not cfg.as_numbers_in_strings

    def test_any_enabled_with_as_numbers(self) -> None:
        cfg = AnonymizeConfig(as_numbers=[65001])
        assert cfg.any_enabled

    def test_any_enabled_with_sensitive_words(self) -> None:
        cfg = AnonymizeConfig(sensitive_words=["acme"])
        assert cfg.any_enabled

    def test_salt_and_options(self) -> None:
        cfg = AnonymizeConfig(
            ips=True,
            salt="my-salt",
            preserve_prefixes=["10.0.0.0/8"],
            ignore_subnets=True,
        )
        assert cfg.salt == "my-salt"
        assert cfg.preserve_prefixes == ["10.0.0.0/8"]
        assert cfg.ignore_subnets


class TestBuildConfigFromCli:
    def test_no_flags_returns_none(self) -> None:
        result = build_config_from_cli()
        assert result is None

    def test_anonymize_ips_flag(self) -> None:
        cfg = build_config_from_cli(anonymize_ips=True)
        assert cfg is not None
        assert cfg.ips
        assert not cfg.passwords

    def test_anonymize_all_flag(self) -> None:
        cfg = build_config_from_cli(anonymize_all=True)
        assert cfg is not None
        assert cfg.ips
        assert cfg.passwords
        assert cfg.communities
        assert cfg.ssh_keys
        assert cfg.identities
        assert cfg.groups
        assert cfg.descriptions

    def test_salt_and_include(self) -> None:
        cfg = build_config_from_cli(
            anonymize_ips=True,
            anonymize_salt="s3cr3t",
            anonymize_include=("system", "interfaces"),
        )
        assert cfg is not None
        assert cfg.salt == "s3cr3t"
        assert cfg.include == ["system", "interfaces"]

    def test_as_numbers_parsing(self) -> None:
        cfg = build_config_from_cli(anonymize_as_numbers="65001, 65002, 65003")
        assert cfg is not None
        assert cfg.as_numbers == [65001, 65002, 65003]

    def test_sensitive_words_parsing(self) -> None:
        cfg = build_config_from_cli(anonymize_sensitive_words="acme, newyork")
        assert cfg is not None
        assert cfg.sensitive_words == ["acme", "newyork"]

    def test_preserve_prefixes(self) -> None:
        cfg = build_config_from_cli(
            anonymize_ips=True,
            anonymize_preserve_prefixes=("10.0.0.0/8", "172.16.0.0/12"),
        )
        assert cfg is not None
        assert cfg.preserve_prefixes == ["10.0.0.0/8", "172.16.0.0/12"]

    def test_ignore_subnets_and_reserved(self) -> None:
        cfg = build_config_from_cli(
            anonymize_ips=True,
            anonymize_ignore_subnets=True,
            anonymize_ignore_reserved=True,
        )
        assert cfg is not None
        assert cfg.ignore_subnets
        assert cfg.ignore_reserved

    def test_as_numbers_in_strings_flag(self) -> None:
        cfg = build_config_from_cli(
            anonymize_as_numbers="65001",
            anonymize_as_numbers_in_strings=True,
        )
        assert cfg is not None
        assert cfg.as_numbers_in_strings

    def test_anonymize_all_sets_as_numbers_in_strings(self) -> None:
        cfg = build_config_from_cli(anonymize_all=True)
        assert cfg is not None
        assert cfg.as_numbers_in_strings

    def test_log_level(self) -> None:
        cfg = build_config_from_cli(anonymize_ips=True, anonymize_log_level="debug")
        assert cfg is not None
        assert cfg.log_level == "debug"


class TestLoadConfigFile:
    def test_load_basic_yaml(self, tmp_path) -> None:
        config_file = tmp_path / "anon.yaml"
        config_file.write_text(
            "anonymize:\n"
            "  ips: true\n"
            "  salt: test-salt\n"
            "  include:\n"
            "    - system\n"
            "    - interfaces\n"
        )
        cfg = load_config_file(str(config_file))
        assert cfg.ips
        assert cfg.salt == "test-salt"
        assert cfg.include == ["system", "interfaces"]

    def test_load_all_shorthand(self, tmp_path) -> None:
        config_file = tmp_path / "anon.yaml"
        config_file.write_text("anonymize:\n  all: true\n")
        cfg = load_config_file(str(config_file))
        assert cfg.ips
        assert cfg.passwords
        assert cfg.communities

    def test_load_with_lists(self, tmp_path) -> None:
        config_file = tmp_path / "anon.yaml"
        config_file.write_text(
            "anonymize:\n"
            "  as_numbers:\n"
            "    - 65001\n"
            "    - 65002\n"
            "  sensitive_words:\n"
            "    - acme\n"
            "    - corp\n"
        )
        cfg = load_config_file(str(config_file))
        assert cfg.as_numbers == [65001, 65002]
        assert cfg.sensitive_words == ["acme", "corp"]

    def test_cli_overrides_config_file(self, tmp_path) -> None:
        config_file = tmp_path / "anon.yaml"
        config_file.write_text("anonymize:\n  ips: true\n  salt: file-salt\n")
        cfg = build_config_from_cli(
            anonymize_config=str(config_file),
            anonymize_salt="cli-salt",
            anonymize_passwords=True,
        )
        assert cfg is not None
        assert cfg.ips  # From config file
        assert cfg.passwords  # From CLI
        assert cfg.salt == "cli-salt"  # CLI overrides file

    def test_empty_file_returns_defaults(self, tmp_path) -> None:
        config_file = tmp_path / "empty.yaml"
        config_file.write_text("")
        cfg = load_config_file(str(config_file))
        assert not cfg.any_enabled

    def test_flat_format_without_anonymize_key(self, tmp_path) -> None:
        """Config without an 'anonymize' wrapper should still work."""
        config_file = tmp_path / "flat.yaml"
        config_file.write_text("ips: true\nsalt: flat-salt\n")
        cfg = load_config_file(str(config_file))
        assert cfg.ips
        assert cfg.salt == "flat-salt"

    def test_invalid_string_content(self, tmp_path) -> None:
        config_file = tmp_path / "bad.yaml"
        config_file.write_text("just a string")
        cfg = load_config_file(str(config_file))
        assert not cfg.any_enabled

    def test_load_dump_map(self, tmp_path) -> None:
        config_file = tmp_path / "anon.yaml"
        config_file.write_text("anonymize:\n  ips: true\n  dump_map: revert.json\n")
        cfg = load_config_file(str(config_file))
        assert cfg.dump_map == "revert.json"

    def test_load_ip_options(self, tmp_path) -> None:
        config_file = tmp_path / "anon.yaml"
        config_file.write_text(
            "anonymize:\n"
            "  ips: true\n"
            "  preserve_prefixes:\n"
            "    - 10.0.0.0/8\n"
            "  ignore_subnets: true\n"
            "  ignore_reserved: true\n"
            "  ips_in_strings: true\n"
        )
        cfg = load_config_file(str(config_file))
        assert cfg.preserve_prefixes == ["10.0.0.0/8"]
        assert cfg.ignore_subnets is True
        assert cfg.ignore_reserved is True
        assert cfg.ips_in_strings is True

    def test_load_as_numbers_in_strings(self, tmp_path) -> None:
        config_file = tmp_path / "anon.yaml"
        config_file.write_text(
            "anonymize:\n  as_numbers:\n    - 65001\n  as_numbers_in_strings: true\n"
        )
        cfg = load_config_file(str(config_file))
        assert cfg.as_numbers_in_strings
        assert cfg.as_numbers == [65001]

    def test_load_log_level(self, tmp_path) -> None:
        config_file = tmp_path / "anon.yaml"
        config_file.write_text("anonymize:\n  ips: true\n  log_level: debug\n")
        cfg = load_config_file(str(config_file))
        assert cfg.log_level == "debug"


class TestBuildConfigRevertOnly:
    """Tests for revert-map-only mode (no anonymization rules)."""

    def test_revert_map_only_returns_config(self) -> None:
        cfg = build_config_from_cli(anonymize_revert_map="/tmp/map.json")
        assert cfg is not None
        assert cfg.revert_map == "/tmp/map.json"
        assert not cfg.any_enabled

    def test_revert_map_with_rules_returns_config(self) -> None:
        cfg = build_config_from_cli(anonymize_ips=True, anonymize_revert_map="/tmp/map.json")
        assert cfg is not None
        assert cfg.revert_map == "/tmp/map.json"
        assert cfg.ips is True

    def test_dump_map_flag(self) -> None:
        cfg = build_config_from_cli(anonymize_ips=True, anonymize_dump_map="/tmp/out.json")
        assert cfg is not None
        assert cfg.dump_map == "/tmp/out.json"

    def test_config_file_with_revert(self, tmp_path) -> None:
        config_file = tmp_path / "anon.yaml"
        config_file.write_text("anonymize:\n  all: true\n  dump_map: revert.json\n")
        cfg = build_config_from_cli(anonymize_config=str(config_file))
        assert cfg is not None
        assert cfg.dump_map == "revert.json"
        assert cfg.ips is True
