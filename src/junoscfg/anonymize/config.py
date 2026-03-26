"""Anonymization configuration dataclass and builders."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class AnonymizeConfig:
    """Configuration for the anonymization pipeline.

    Each boolean flag enables one anonymization rule category.
    ``all`` is a shorthand that enables the 8 boolean rules
    (ips, passwords, communities, ssh_keys, identities, groups,
    descriptions, ips_in_strings) but NOT as_numbers or
    sensitive_words (those require user-provided lists).
    """

    # Rule toggles
    ips: bool = False
    passwords: bool = False
    communities: bool = False
    ssh_keys: bool = False
    identities: bool = False
    groups: bool = False
    descriptions: bool = False

    # List-based rules
    as_numbers: list[int] = field(default_factory=list)
    as_number_map: dict[int, int] = field(default_factory=dict)
    sensitive_words: list[str] = field(default_factory=list)
    sensitive_patterns: list[str] = field(default_factory=list)

    # Shared options
    salt: str | None = None
    dump_map: str | None = None
    revert_map: str | None = None

    # Path filters
    include: list[str] = field(default_factory=list)
    exclude: list[str] = field(default_factory=list)

    # IP-specific options
    preserve_prefixes: list[str] = field(default_factory=list)
    networks: list[str] = field(default_factory=list)
    network_file: str | None = None
    ignore_subnets: bool = False
    ignore_reserved: bool = False
    ips_in_strings: bool = False

    # AS-number-specific options
    as_numbers_in_strings: bool = False

    # Logging
    log_level: str = "normal"

    @property
    def any_enabled(self) -> bool:
        """Return True if at least one anonymization rule is enabled."""
        return (
            self.ips
            or self.passwords
            or self.communities
            or self.ssh_keys
            or self.identities
            or self.groups
            or self.descriptions
            or bool(self.as_numbers)
            or bool(self.sensitive_words)
            or bool(self.sensitive_patterns)
        )

    def expand_all(self) -> None:
        """Enable all boolean rules (called when ``--anonymize-all`` is used)."""
        self.ips = True
        self.passwords = True
        self.communities = True
        self.ssh_keys = True
        self.identities = True
        self.groups = True
        self.descriptions = True
        self.ips_in_strings = True
        self.as_numbers_in_strings = True


def build_config_from_cli(
    *,
    anonymize_all: bool = False,
    anonymize_ips: bool = False,
    anonymize_passwords: bool = False,
    anonymize_communities: bool = False,
    anonymize_ssh_keys: bool = False,
    anonymize_identities: bool = False,
    anonymize_groups: bool = False,
    anonymize_descriptions: bool = False,
    anonymize_as_numbers: str | None = None,
    anonymize_sensitive_words: str | None = None,
    anonymize_sensitive_patterns: tuple[str, ...] = (),
    anonymize_salt: str | None = None,
    anonymize_dump_map: str | None = None,
    anonymize_revert_map: str | None = None,
    anonymize_include: tuple[str, ...] = (),
    anonymize_exclude: tuple[str, ...] = (),
    anonymize_preserve_prefixes: tuple[str, ...] = (),
    anonymize_networks: tuple[str, ...] = (),
    anonymize_network_file: str | None = None,
    anonymize_ignore_subnets: bool = False,
    anonymize_ignore_reserved: bool = False,
    anonymize_ips_in_strings: bool = False,
    anonymize_as_numbers_in_strings: bool = False,
    anonymize_log_level: str = "normal",
    anonymize_config: str | None = None,
) -> AnonymizeConfig | None:
    """Build an AnonymizeConfig from CLI flags.

    Returns None if no anonymization options were specified.
    """
    # Start from config file if provided, otherwise defaults
    cfg = load_config_file(anonymize_config) if anonymize_config else AnonymizeConfig()

    # CLI flags override config file values
    if anonymize_all:
        cfg.expand_all()
    if anonymize_ips:
        cfg.ips = True
    if anonymize_passwords:
        cfg.passwords = True
    if anonymize_communities:
        cfg.communities = True
    if anonymize_ssh_keys:
        cfg.ssh_keys = True
    if anonymize_identities:
        cfg.identities = True
    if anonymize_groups:
        cfg.groups = True
    if anonymize_descriptions:
        cfg.descriptions = True

    if anonymize_as_numbers:
        cfg.as_numbers, cfg.as_number_map = _parse_as_numbers(anonymize_as_numbers)
    if anonymize_sensitive_words:
        cfg.sensitive_words = [w.strip() for w in anonymize_sensitive_words.split(",") if w.strip()]
    if anonymize_sensitive_patterns:
        cfg.sensitive_patterns = list(anonymize_sensitive_patterns)

    if anonymize_salt:
        cfg.salt = anonymize_salt
    if anonymize_dump_map:
        cfg.dump_map = anonymize_dump_map
    if anonymize_revert_map:
        cfg.revert_map = anonymize_revert_map
    if anonymize_include:
        cfg.include = list(anonymize_include)
    if anonymize_exclude:
        cfg.exclude = list(anonymize_exclude)
    if anonymize_preserve_prefixes:
        cfg.preserve_prefixes = list(anonymize_preserve_prefixes)
    if anonymize_networks:
        cfg.networks = list(anonymize_networks)
    if anonymize_network_file:
        cfg.network_file = anonymize_network_file
    if anonymize_ignore_subnets:
        cfg.ignore_subnets = True
    if anonymize_ignore_reserved:
        cfg.ignore_reserved = True
    if anonymize_ips_in_strings:
        cfg.ips_in_strings = True
    if anonymize_as_numbers_in_strings:
        cfg.as_numbers_in_strings = True
    if anonymize_log_level != "normal":
        cfg.log_level = anonymize_log_level

    if not cfg.any_enabled and not cfg.revert_map and not anonymize_config:
        return None

    return cfg


def _parse_as_numbers(raw: str) -> tuple[list[int], dict[int, int]]:
    """Parse the ``--anonymize-as-numbers`` string.

    Supports two formats:

    - Plain: ``"64497,64498"`` — ASNs to anonymize with auto-sequential replacement
    - Mapped: ``"64497:100,64498:101"`` — explicit original→replacement pairs

    Returns:
        A tuple of (target_list, explicit_map).
    """
    targets: list[int] = []
    explicit: dict[int, int] = {}
    for part in raw.split(","):
        part = part.strip()
        if not part:
            continue
        if ":" in part:
            orig_s, repl_s = part.split(":", 1)
            orig, repl = int(orig_s.strip()), int(repl_s.strip())
            targets.append(orig)
            explicit[orig] = repl
        else:
            targets.append(int(part))
    return targets, explicit


def load_config_file(path: str) -> AnonymizeConfig:
    """Load an AnonymizeConfig from a YAML file."""
    import yaml

    with open(path) as f:
        raw = yaml.safe_load(f)

    if not isinstance(raw, dict):
        return AnonymizeConfig()

    data = raw.get("anonymize", raw)
    if not isinstance(data, dict):
        return AnonymizeConfig()

    cfg = AnonymizeConfig()

    if data.get("all"):
        cfg.expand_all()

    for flag in (
        "ips",
        "passwords",
        "communities",
        "ssh_keys",
        "identities",
        "groups",
        "descriptions",
    ):
        if data.get(flag):
            setattr(cfg, flag, True)

    if "as_numbers" in data and isinstance(data["as_numbers"], list):
        cfg.as_numbers = [int(x) for x in data["as_numbers"]]
    if "as_number_map" in data and isinstance(data["as_number_map"], dict):
        cfg.as_number_map = {int(k): int(v) for k, v in data["as_number_map"].items()}
    if "sensitive_words" in data and isinstance(data["sensitive_words"], list):
        cfg.sensitive_words = [str(w) for w in data["sensitive_words"]]
    if "sensitive_patterns" in data and isinstance(data["sensitive_patterns"], list):
        cfg.sensitive_patterns = [str(p) for p in data["sensitive_patterns"]]
    if "salt" in data:
        cfg.salt = str(data["salt"])
    if "dump_map" in data:
        cfg.dump_map = str(data["dump_map"])
    if "include" in data and isinstance(data["include"], list):
        cfg.include = [str(p) for p in data["include"]]
    if "exclude" in data and isinstance(data["exclude"], list):
        cfg.exclude = [str(p) for p in data["exclude"]]
    if "preserve_prefixes" in data and isinstance(data["preserve_prefixes"], list):
        cfg.preserve_prefixes = [str(p) for p in data["preserve_prefixes"]]
    if "networks" in data and isinstance(data["networks"], list):
        cfg.networks = [str(n) for n in data["networks"]]
    if "network_file" in data:
        cfg.network_file = str(data["network_file"])
    if data.get("ignore_subnets"):
        cfg.ignore_subnets = True
    if data.get("ignore_reserved"):
        cfg.ignore_reserved = True
    if data.get("ips_in_strings"):
        cfg.ips_in_strings = True
    if data.get("as_numbers_in_strings"):
        cfg.as_numbers_in_strings = True
    if "log_level" in data:
        cfg.log_level = str(data["log_level"])

    return cfg
