"""Junoscfg CLI: convert and validate Junos configurations."""

from __future__ import annotations

import contextlib
import sys
from typing import TYPE_CHECKING, Any

import click
import yaml

from junoscfg import Format, __version__
from junoscfg.audit.render import STYLE_CHOICES as _AUDIT_STYLE_CHOICES

if TYPE_CHECKING:
    from collections.abc import Iterator

_FORMAT_CHOICES = [f.value for f in Format] + ["conf"]

_CONTEXT_SETTINGS = {"help_option_names": ["-h", "--help", "-?"]}


class DefaultGroup(click.Group):
    """Click group that defaults to 'convert' subcommand for backward compat."""

    def parse_args(self, ctx: click.Context, args: list[str]) -> list[str]:
        """Insert the default ``convert`` subcommand when none was given."""
        # If first arg is not a known subcommand, prepend 'convert'
        if args and args[0] not in self.commands and not args[0].startswith("-"):
            args = ["convert"] + args
        # If no subcommand but has flags, default to convert
        # Don't redirect help or version flags to the convert subcommand
        help_names = set(ctx.help_option_names or ["--help"])
        skip_names = help_names | {"--version"}
        if args and args[0].startswith("-") and args[0] not in skip_names:
            args = ["convert"] + args
        return super().parse_args(ctx, args)


@click.group(cls=DefaultGroup, invoke_without_command=True, context_settings=_CONTEXT_SETTINGS)
@click.version_option(version=__version__, prog_name="junoscfg")
@click.pass_context
def main(ctx: click.Context) -> None:
    """Junoscfg: convert and validate Junos configurations.

    \b
    Quick start:
      junoscfg convert -i json -e set config.json       Convert JSON → set commands
      junoscfg convert -e set config.json               Auto-detect input format
      junoscfg convert -v -i json config.json           Validate only
      junoscfg edityaml addvars -r rules.yaml config.yaml
      junoscfg edityaml ansibilize -p "prefix:path" config.yaml
      junoscfg edityaml rename-root --from cfg --to junos config.yaml
    """
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


@main.command()
@click.option(
    "-i",
    "--import-format",
    "import_format",
    type=click.Choice(_FORMAT_CHOICES, case_sensitive=False),
    default=None,
    help="Input format (auto-detected if omitted).",
)
@click.option(
    "-e",
    "--export-format",
    "export_format",
    type=click.Choice(_FORMAT_CHOICES, case_sensitive=False),
    default=None,
    help="Output format.",
)
@click.option("-v", "--validate", is_flag=True, help="Validate configuration.")
@click.option(
    "--artifacts",
    type=click.Path(exists=True, file_okay=False),
    envvar="JUNOSCFG_ARTIFACTS",
    help="Path to validation artifacts directory.",
)
@click.option(
    "--path",
    "filter_path",
    default=None,
    help="Show only config under this path (dot-separated, e.g. 'system.syslog').",
)
@click.option(
    "--relative", is_flag=True, help="Show relative paths (omit --path prefix from output)."
)
@click.option(
    "--strict",
    "field_strict",
    is_flag=True,
    help="Fail on field-level validation errors (exit code 1).",
)
@click.option(
    "--no-field-validate",
    "no_field_validate",
    is_flag=True,
    help="Skip field-level value validation.",
)
@click.option("--anonymize-all", is_flag=True, help="Enable all anonymization rules.")
@click.option("--anonymize-ips", is_flag=True, help="Anonymize IP addresses.")
@click.option("--anonymize-passwords", is_flag=True, help="Anonymize passwords and secrets.")
@click.option("--anonymize-communities", is_flag=True, help="Anonymize SNMP community strings.")
@click.option("--anonymize-ssh-keys", is_flag=True, help="Anonymize SSH public keys.")
@click.option("--anonymize-identities", is_flag=True, help="Anonymize usernames and identities.")
@click.option("--anonymize-groups", is_flag=True, help="Anonymize group and view names.")
@click.option("--anonymize-descriptions", is_flag=True, help="Anonymize description fields.")
@click.option(
    "--anonymize-as-numbers",
    default=None,
    help="Comma-separated AS numbers to anonymize.",
)
@click.option(
    "--anonymize-sensitive-words",
    default=None,
    help="Comma-separated sensitive words.",
)
@click.option(
    "--anonymize-sensitive-patterns",
    multiple=True,
    help="Regex pattern for sensitive data (repeatable).",
)
@click.option("--anonymize-salt", default=None, help="Shared salt for deterministic output.")
@click.option(
    "--anonymize-dump-map",
    default=None,
    type=click.Path(),
    help="Write revert dictionary to file.",
)
@click.option(
    "--anonymize-revert-map",
    default=None,
    type=click.Path(exists=True),
    help="Apply revert dictionary (restore originals).",
)
@click.option(
    "--anonymize-include",
    multiple=True,
    help="Only anonymize within these paths (repeatable).",
)
@click.option(
    "--anonymize-exclude",
    multiple=True,
    help="Skip these paths (repeatable).",
)
@click.option(
    "--anonymize-preserve-prefixes",
    multiple=True,
    help="IP prefixes to pass through (repeatable).",
)
@click.option(
    "--anonymize-networks",
    multiple=True,
    help="Subnet specs for host-bit locking (CIDR, range, or 'auto'). Repeatable.",
)
@click.option(
    "--anonymize-network-file",
    default=None,
    type=click.Path(exists=True),
    help="File with one subnet spec per line (for host-bit locking).",
)
@click.option(
    "--anonymize-ignore-subnets", is_flag=True, help="Treat sub-/8 private ranges as public."
)
@click.option(
    "--anonymize-ignore-reserved", is_flag=True, help="Remove all reserved range handling."
)
@click.option(
    "--anonymize-ips-in-strings",
    is_flag=True,
    help="Also replace an address that is a whole value where the schema says syntax "
    "(an SNMP OID, an area reference); an address inside text is replaced without it.",
)
@click.option(
    "--anonymize-as-numbers-in-strings",
    is_flag=True,
    help="Also replace target AS numbers inside text (group names, communities, URLs), "
    "never inside an address.",
)
@click.option(
    "--anonymize-config",
    default=None,
    type=click.Path(exists=True),
    help="YAML config file with all anonymization options.",
)
@click.option(
    "--anonymize-log-level",
    type=click.Choice(["quiet", "normal", "debug"], case_sensitive=False),
    default="normal",
    help="Anonymization logging verbosity; debug prints each original value beside its "
    "replacement to stderr.",
)
@click.argument("file", required=False, type=click.Path(exists=True))
def convert(
    import_format: str | None,
    export_format: str | None,
    validate: bool,
    artifacts: str | None,
    filter_path: str | None,
    relative: bool,
    field_strict: bool,
    no_field_validate: bool,
    anonymize_all: bool,
    anonymize_ips: bool,
    anonymize_passwords: bool,
    anonymize_communities: bool,
    anonymize_ssh_keys: bool,
    anonymize_identities: bool,
    anonymize_groups: bool,
    anonymize_descriptions: bool,
    anonymize_as_numbers: str | None,
    anonymize_sensitive_words: str | None,
    anonymize_sensitive_patterns: tuple[str, ...],
    anonymize_salt: str | None,
    anonymize_dump_map: str | None,
    anonymize_revert_map: str | None,
    anonymize_include: tuple[str, ...],
    anonymize_exclude: tuple[str, ...],
    anonymize_preserve_prefixes: tuple[str, ...],
    anonymize_networks: tuple[str, ...],
    anonymize_network_file: str | None,
    anonymize_ignore_subnets: bool,
    anonymize_ignore_reserved: bool,
    anonymize_ips_in_strings: bool,
    anonymize_as_numbers_in_strings: bool,
    anonymize_config: str | None,
    anonymize_log_level: str,
    file: str | None,
) -> None:
    """Convert Junos configurations between formats.

    Reads from FILE or stdin.

    \b
    Formats:
      set          Flat "set" commands, one per line
      structured   Curly-brace hierarchical format (alias: conf)
      json         Junos native JSON
      yaml         YAML of junoscfg's IR; to be renamed yaml-old
      yaml-new     Junos native JSON written as YAML; to become yaml
      xml          Junos XML (input only)

    \b
    Examples — Conversion:
      junoscfg convert -i json -e set config.json       Convert JSON to set
      junoscfg convert -i structured -e set config.conf Convert structured to set
      junoscfg convert -e structured config.json        Auto-detect input format
      junoscfg convert -i conf -e set config.conf       "conf" alias for structured
      junoscfg convert -i json -e json config.json      Identity (normalize JSON)
      junoscfg convert -i set -e set config.set         Identity (normalize set)
      junoscfg convert -i yaml -e yaml-new old.yaml     Migrate YAML to yaml-new

    \b
    Examples — Validation:
      junoscfg convert -v -i json config.json             Validate only (no output)
      junoscfg convert --strict -i set -e json f.set      Fail on field errors
      junoscfg convert --no-field-validate -e json f.set  Skip field validation

    \b
    Examples — Anonymization:
      junoscfg convert -i json -e json --anonymize-all config.json
      junoscfg convert -e yaml --anonymize-ips --anonymize-salt s3cr3t config.json
      junoscfg convert -e set --anonymize-config anon.yaml config.json
      junoscfg convert -i json -e json --anonymize-revert-map revert.json anon.json
      junoscfg convert -e set --anonymize-sensitive-patterns 'LAX\\d+' config.json
      junoscfg convert -e set \\
        --anonymize-sensitive-patterns \\
        '([a-zA-Z0-9]([a-zA-Z0-9\\-]{0,61}[a-zA-Z0-9])?\\.)+example\\.com' \\
        config.json
    """
    # Normalize "conf" alias to "structured"
    if import_format == "conf":
        import_format = "structured"
    if export_format == "conf":
        export_format = "structured"

    # Validate --relative requires --path
    if relative and not filter_path:
        click.echo("Error: --relative requires --path.", err=True)
        sys.exit(2)

    # One flag, whole tool. `--artifacts` used to reach validation only, so a
    # user pointing at a schema they had generated got it for `-v` and the
    # bundled one for the conversion in the same command.
    #
    # Closed on the click context rather than left set: `CliRunner` runs this
    # in the test process and the Ansible collection imports the library into a
    # long-lived `ansible-playbook`, so an override with no matching reset
    # leaks one invocation's schema into every later one.
    if artifacts:
        from junoscfg.display import artifacts_dir as _artifacts_dir

        _stack = contextlib.ExitStack()
        _stack.enter_context(_artifacts_dir(artifacts))
        click.get_current_context().call_on_close(_stack.close)

    # If validate-only (no export format), just validate
    validate_only = validate and not export_format

    if not export_format and not validate:
        click.echo(
            "Error: specify -e/--export-format (set, structured, json, yaml, yaml-new).",
            err=True,
        )
        sys.exit(2)

    # Read input
    source = _read_input(file)
    if not source.strip():
        return

    # Auto-detect import format if not specified
    if not import_format:
        from junoscfg.display import CONVERSION_FORMATS, detect_format

        import_format = detect_format(source, accepted_formats=CONVERSION_FORMATS)

    # Build anonymization config if any anonymize flags are set
    from junoscfg.anonymize import build_config_from_cli

    anon_config = build_config_from_cli(
        anonymize_all=anonymize_all,
        anonymize_ips=anonymize_ips,
        anonymize_passwords=anonymize_passwords,
        anonymize_communities=anonymize_communities,
        anonymize_ssh_keys=anonymize_ssh_keys,
        anonymize_identities=anonymize_identities,
        anonymize_groups=anonymize_groups,
        anonymize_descriptions=anonymize_descriptions,
        anonymize_as_numbers=anonymize_as_numbers,
        anonymize_sensitive_words=anonymize_sensitive_words,
        anonymize_sensitive_patterns=anonymize_sensitive_patterns,
        anonymize_salt=anonymize_salt,
        anonymize_dump_map=anonymize_dump_map,
        anonymize_revert_map=anonymize_revert_map,
        anonymize_include=anonymize_include,
        anonymize_exclude=anonymize_exclude,
        anonymize_preserve_prefixes=anonymize_preserve_prefixes,
        anonymize_networks=anonymize_networks,
        anonymize_network_file=anonymize_network_file,
        anonymize_ignore_subnets=anonymize_ignore_subnets,
        anonymize_ignore_reserved=anonymize_ignore_reserved,
        anonymize_ips_in_strings=anonymize_ips_in_strings,
        anonymize_as_numbers_in_strings=anonymize_as_numbers_in_strings,
        anonymize_log_level=anonymize_log_level,
        anonymize_config=anonymize_config,
    )

    # Validate if requested. Validation reads the source before anonymization,
    # so what it prints must not show the source's values when the run
    # anonymizes.
    anonymizing = bool(anon_config is not None and anon_config.any_enabled)
    with _failure_withheld(anonymizing):
        _validate_and_convert(
            source,
            import_format,
            export_format,
            artifacts=artifacts,
            validate=validate or validate_only,
            validate_only=validate_only,
            field_validate=not no_field_validate,
            field_strict=field_strict,
            filter_path=filter_path,
            relative=relative,
            anon_config=anon_config,
            anonymizing=anonymizing,
        )


def _validate_and_convert(
    source: str,
    import_format: str,
    export_format: str | None,
    *,
    artifacts: str | None,
    validate: bool,
    validate_only: bool,
    field_validate: bool,
    field_strict: bool,
    filter_path: str | None,
    relative: bool,
    anon_config: Any,
    anonymizing: bool,
) -> None:
    """Validate *source* if asked, then convert it and print the result."""
    if validate:
        _run_validation(source, import_format, artifacts, anonymizing=anonymizing)
        if validate_only:
            return

    # For --anonymize-networks auto: stash source text so IpRule can scan it
    if anon_config and "auto" in (anon_config.networks or []):
        anon_config.source_text = source

    # Convert using the unified API
    from junoscfg import convert_config_result

    from_fmt = Format(import_format)
    to_fmt = Format(export_format)

    try:
        result = convert_config_result(
            source,
            from_format=from_fmt,
            to_format=to_fmt,
            validate=field_validate,
            strict=field_strict,
            path=filter_path,
            relative=relative,
            anon_config=anon_config,
        )
    except NotImplementedError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(2)
    except yaml.YAMLError as e:
        # Malformed YAML is a usage error, like malformed JSON and XML. JSON
        # reached the handler below only because `JSONDecodeError` happens to
        # subclass `ValueError`; `yaml.YAMLError` does not, so a bad document
        # printed a parser traceback where the other formats printed an error.
        click.echo(f"Error: Invalid YAML: {e}", err=True)
        sys.exit(2)
    except ValueError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(2)
    except Exception as e:
        from junoscfg import FieldValidationError

        if isinstance(e, FieldValidationError):
            click.echo(f"Field validation: FAILED ({len(e.result.errors)} error(s))", err=True)
            for err in e.result.errors[:10]:
                click.echo(f"  - {err.path}: {err.message}", err=True)
            if len(e.result.errors) > 10:
                click.echo(f"  ... and {len(e.result.errors) - 10} more errors", err=True)
            sys.exit(1)
        raise

    for diagnostic in result.diagnostics:
        click.echo(diagnostic.render(), err=True)
    if result.output:
        click.echo(result.output, nl=False)


@main.group()
def edityaml() -> None:
    """Transform YAML for Ansible consumption."""


@edityaml.command()
@click.option(
    "-r",
    "--rules",
    "rules_file",
    type=click.Path(exists=True),
    default=None,
    help="YAML file containing transform rules.",
)
@click.option(
    "--path",
    "inline_path",
    default=None,
    help=(
        "Path expression for inline --set transforms"
        " (e.g. 'groups[ansible-*].interfaces.interface[*].unit[*].family.inet*.address[*]')."
    ),
)
@click.option(
    "--set",
    "set_exprs",
    multiple=True,
    help="Inline transform expression (repeatable). Requires --path.",
)
@click.argument("file", required=False, type=click.Path(exists=True))
def addvars(
    rules_file: str | None,
    inline_path: str | None,
    set_exprs: tuple[str, ...],
    file: str | None,
) -> None:
    """Add derived keys to YAML using transform rules.

    Reads from FILE or stdin. Apply transforms via a rule file (-r) or
    inline expressions (--path + --set).

    \b
    Examples:
      junoscfg edityaml addvars -r rules.yaml config.yaml
      junoscfg edityaml addvars --path "a.b[*]" --set "_x=copy(name)" config.yaml
      cat config.yaml | junoscfg edityaml addvars -r rules.yaml

    \b
    Real-world pipeline — fetch BGP config, convert, and enrich:
      ssh router "show configuration protocols bgp group overlay
        | display json" \\
        | junoscfg convert -i json -e yaml \\
        | junoscfg edityaml addvars \\
            --path "configuration.protocols.bgp.group[*].neighbor[*]" \\
            --set "_peername=regex_extract(description, 'overlay: (\\w+)')" \\
            --set "_peer_ip=copy(name)" \\
            --set "_managed=static(true)"

    \b
    Sample input YAML (from junoscfg convert):
      configuration:
        protocols:
          bgp:
            group:
            - name: overlay
              neighbor:
              - name: 192.168.100.15
                description: 'overlay: switch02'
                peer-as: '4200000002'
              - name: 172.16.50.204
                description: 'overlay: switch03'
                peer-as: '4200000003'

    \b
    Output (each neighbor gets _peername, _peer_ip, _managed):
              - name: 192.168.100.15
                description: 'overlay: switch02'
                peer-as: '4200000002'
                _peername: switch02
                _peer_ip: 192.168.100.15
                _managed: true
    """
    import yaml

    from junoscfg.edityaml import apply_rules, load_rules_file, merge_rulesets, parse_inline_rules

    # Validate arguments
    if not rules_file and not set_exprs:
        click.echo("Error: specify -r/--rules or --path + --set.", err=True)
        sys.exit(2)

    if set_exprs and not inline_path:
        click.echo("Error: --set requires --path.", err=True)
        sys.exit(2)

    # Build ruleset
    rulesets: list[dict] = []
    if rules_file:
        rulesets.append(load_rules_file(rules_file))
    if set_exprs and inline_path:
        rulesets.append(parse_inline_rules(inline_path, list(set_exprs)))
    ruleset = merge_rulesets(*rulesets)

    # Read input YAML
    source = _read_input(file)
    if not source.strip():
        return

    data = yaml.safe_load(source)
    result = apply_rules(data, ruleset)
    click.echo(yaml.dump(result, default_flow_style=False, sort_keys=False), nl=False)


@edityaml.command()
@click.option(
    "-p",
    "--prefix_path",
    "prefix_paths",
    multiple=True,
    help="prefix:path pair for literal extraction (repeatable). Split on first ':'.",
)
@click.option(
    "-P",
    "--offset-prefix-path",
    "offset_prefix_paths",
    multiple=True,
    help="prefix:path pair for offset-mode extraction (repeatable). Split on first ':'.",
)
@click.option(
    "--offset-var",
    "offset_var",
    default="base_address_offset",
    help="Name of the per-host offset variable (default: base_address_offset).",
)
@click.option(
    "--root",
    "root_keys",
    multiple=True,
    help="Top-level key glob to descend into (repeatable). Overrides auto-descend.",
)
@click.argument("file", required=False, type=click.Path(exists=True))
def ansibilize(
    prefix_paths: tuple[str, ...],
    offset_prefix_paths: tuple[str, ...],
    offset_var: str,
    root_keys: tuple[str, ...],
    file: str | None,
) -> None:
    """Extract leaf values into Ansible host_vars and templatize group_vars.

    Each -p value is prefix:path for literal extraction.
    Each -P value is prefix:path for offset-mode extraction.

    \b
    Offset mode (-P) detects the value type and generates expressions:
      IP address     → {{ 'addr' | ansible.utils.ipmath(offset_var) }}/mask
      MAC address    → prefix:{{ '%02x' % (base + offset_var) }}
      Trailing digits → prefix{{ '%0Nd' % (num + offset_var) }}

    \b
    Outputs:
      With -p only: 2 YAML documents (host_vars, group_vars template)
      With -P:      3 YAML documents (host_vars, computed vars, group_vars template)

    \b
    Examples:
      junoscfg edityaml ansibilize -p "addr:items[*].name" f.yaml
      junoscfg edityaml ansibilize -P "addr:intf[*].addr[*].name" f.yaml
      junoscfg edityaml ansibilize --offset-var my_offset -P "a:path" f.yaml
      junoscfg edityaml ansibilize -p "host:system.host-name" -P "a:path" f.yaml
    """
    import yaml

    # Validate: at least one of -p or -P required
    if not prefix_paths and not offset_prefix_paths:
        click.echo("Error: specify at least one -p or -P option.", err=True)
        sys.exit(2)

    def _parse_prefix_path_pairs(raw: tuple[str, ...], flag: str) -> list[tuple[str, str]]:
        pairs: list[tuple[str, str]] = []
        for pp in raw:
            if ":" not in pp:
                click.echo(f"Error: {flag} value must contain ':' (got {pp!r}).", err=True)
                sys.exit(2)
            prefix, path = pp.split(":", 1)
            pairs.append((prefix, path))
        return pairs

    literal_pairs = _parse_prefix_path_pairs(prefix_paths, "-p")
    offset_pairs = _parse_prefix_path_pairs(offset_prefix_paths, "-P")

    source = _read_input(file)
    if not source.strip():
        return

    data = yaml.safe_load(source)
    rk = list(root_keys) if root_keys else None

    if offset_pairs:
        from junoscfg.edityaml import ansibilize_with_offset, format_output_with_offset

        try:
            host_vars, offset_vars, template = ansibilize_with_offset(
                data,
                literal_pairs=literal_pairs,
                offset_pairs=offset_pairs,
                root_keys=rk,
                offset_var=offset_var,
            )
        except ValueError as e:
            raise click.ClickException(str(e)) from None
        click.echo(format_output_with_offset(host_vars, offset_vars, template), nl=False)
    else:
        from junoscfg.edityaml import ansibilize_multi, format_output

        host_vars, group_vars = ansibilize_multi(data, literal_pairs, root_keys=rk)
        click.echo(format_output(host_vars, group_vars), nl=False)


@edityaml.command("rename-root")
@click.option(
    "--from",
    "from_key",
    default="configuration",
    help="Current top-level key or path expression"
    " (e.g. 'configuration.groups[ansible-managed].interfaces').",
)
@click.option("--to", "to_key", required=True, help="New top-level key name.")
@click.argument("file", required=False, type=click.Path(exists=True))
def rename_root(from_key: str, to_key: str, file: str | None) -> None:
    """Rename the top-level key or extract a subtree in a YAML document.

    \b
    When --from contains dots or brackets, uses path_walker syntax to extract
    a subtree (same syntax as ansibilize). The matched subtree becomes the
    value under the new --to key.

    \b
    Examples:
      junoscfg edityaml rename-root --to junos_config config.yaml
      junoscfg edityaml rename-root --from mykey --to newkey config.yaml
      junoscfg edityaml rename-root \\
        --from "configuration.groups[ansible-managed].interfaces" \\
        --to junos_interfaces config.yaml
    """
    import yaml

    source = _read_input(file)
    if not source.strip():
        return

    data = yaml.safe_load(source)

    # Detect path expression vs simple key
    if "." in from_key or "[" in from_key:
        from junoscfg.edityaml import resolve_path

        matches = resolve_path(data, from_key)
        if not matches:
            click.echo(f"Error: path '{from_key}' not found in input.", err=True)
            sys.exit(2)
        # Use first match; if it's a single value, use it directly
        extracted = matches[0] if len(matches) == 1 else matches
        out = {to_key: extracted}
    else:
        if from_key not in data:
            click.echo(f"Error: key '{from_key}' not found in input.", err=True)
            sys.exit(2)
        # Preserve key order by rebuilding dict
        out = {}
        for k, v in data.items():
            out[to_key if k == from_key else k] = v
    click.echo(yaml.dump(out, default_flow_style=False, sort_keys=False), nl=False)


@main.group()
def schema() -> None:
    """Build and inspect validation schema artifacts.

    \b
    Retrieve the NETCONF XSD dump from a router:
      echo "<rpc> <get-xnm-information> <type>xml-schema</type>
        <namespace>junos-configuration</namespace>
        </get-xnm-information> </rpc>" |
        ssh -Csp 830 router.example.com netconf > netconf.xml
    """


@schema.command()
@click.argument("xsd_source", type=click.Path(exists=True))
@click.option(
    "-o",
    "--output-dir",
    required=True,
    type=click.Path(file_okay=False),
    help="Output directory for artifacts.",
)
def generate(xsd_source: str, output_dir: str) -> None:
    """Generate validation artifacts from a NETCONF XSD dump.

    \b
    Retrieve the XSD dump from a router, then generate artifacts:
      echo "<rpc> <get-xnm-information> <type>xml-schema</type>
        <namespace>junos-configuration</namespace>
        </get-xnm-information> </rpc>" |
        ssh -Csp 830 router.example.com netconf > netconf.xml
      junoscfg schema generate netconf.xml -o ./artifacts/
    """
    from junoscfg.validate import ArtifactBuilder

    builder = ArtifactBuilder()
    try:
        artifacts = builder.build(xsd_source, output_dir)
        for name, path in artifacts.items():
            click.echo(f"  {name}: {path}")
        click.echo("Artifacts generated successfully.")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(3)


@schema.command()
@click.option(
    "--artifacts",
    type=click.Path(exists=True, file_okay=False),
    envvar="JUNOSCFG_ARTIFACTS",
    help="Path to artifacts directory.",
)
def info(artifacts: str | None) -> None:
    """Display schema artifact information.

    \b
    Examples:
      junoscfg schema info
      junoscfg schema info --artifacts ./my-artifacts/
    """
    from junoscfg.validate import JunosValidator

    try:
        v = JunosValidator(artifacts_dir=artifacts)
        click.echo(f"Schema version: {v.schema_version}")
        click.echo(f"Generated at:   {v.generated_at}")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(3)


@main.group()
def audit() -> None:
    """Audit configurations for unused or problematic objects."""


@audit.command()
@click.argument("file", required=False, type=click.Path(exists=True))
@click.option(
    "-i",
    "--import-format",
    "import_format",
    type=click.Choice(_FORMAT_CHOICES, case_sensitive=False),
    default=None,
    help="Input format (default: auto-detect).",
)
@click.option(
    "--types",
    "types_csv",
    default="all",
    help="Comma-separated registry types to audit, or 'all'.",
)
@click.option(
    "--match",
    "match_regex",
    default=None,
    help="Only check definitions whose name matches this regex (re.search).",
)
@click.option(
    "-o",
    "--output",
    "output_style",
    type=click.Choice(_AUDIT_STYLE_CHOICES, case_sensitive=False),
    default="pathname",
    help="Output style.",
)
@click.option(
    "--include-probably-unused",
    is_flag=True,
    help="Include probably-unused findings in delete/deactivate script output.",
)
@click.option(
    "--registry",
    "registry_path",
    type=click.Path(exists=True, dir_okay=False),
    envvar="JUNOSCFG_AUDIT_REGISTRY",
    default=None,
    help="Path to a custom type-registry YAML file.",
)
@click.option(
    "--fail-on",
    "fail_on",
    type=click.Choice(["unused", "probably-unused", "never"], case_sensitive=False),
    default="never",
    help="Exit with code 1 when findings at or above this confidence exist.",
)
def unused(
    file: str | None,
    import_format: str | None,
    types_csv: str,
    match_regex: str | None,
    output_style: str,
    include_probably_unused: bool,
    registry_path: str | None,
    fail_on: str,
) -> None:
    """Find config objects that are defined but never referenced.

    Findings are suggestions requiring human review. Strict `unused`
    findings have no potential reference anywhere; `probably-unused`
    findings have occurrences at positions the type registry does not
    know, listed in the verbose output styles.

    \b
    Examples:
      junoscfg audit unused config.conf
      junoscfg audit unused -o delete-script-verbose config.conf
      cat config.set | junoscfg audit unused --types policy-statement,prefix-list
      junoscfg audit unused --fail-on unused config.conf
    """
    import yaml

    from junoscfg.audit import AuditLoadError, find_unused, load_registry, render
    from junoscfg.convert import to_dict

    source = _read_input(file)
    if not source.strip():
        return

    if import_format:
        fmt = import_format.lower()
    else:
        from junoscfg.display import AUDIT_FORMATS, detect_format

        fmt = detect_format(source, accepted_formats=AUDIT_FORMATS)
    if fmt == "conf":
        fmt = "structured"

    try:
        registry = load_registry(registry_path)
    except AuditLoadError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(3)

    types = None
    if types_csv.strip().lower() != "all":
        types = [t.strip() for t in types_csv.split(",") if t.strip()]
        if not types:
            click.echo("Error: --types is empty; use 'all' or a comma-separated list.", err=True)
            sys.exit(2)

    try:
        ir = to_dict(
            source,
            fmt,
            diagnostic_sink=lambda where, what: click.echo(
                f"structured-input: {where}: {what}", err=True
            ),
        )
    except (ValueError, NotImplementedError, yaml.YAMLError) as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(2)

    try:
        result = find_unused(ir, types=types, match=match_regex, registry=registry)
    except AuditLoadError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(3)
    except ValueError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(2)

    output = render(result, output_style.lower(), include_probably_unused=include_probably_unused)
    if output:
        click.echo(output, nl=False)

    fail_on = fail_on.lower()
    if fail_on == "unused" and result.n_unused:
        sys.exit(1)
    if fail_on == "probably-unused" and result.findings:
        sys.exit(1)


@main.command()
@click.pass_context
def fullhelp(ctx: click.Context) -> None:
    """Show help for all commands."""
    separator = "\n" + "═" * 40

    sections: list[tuple[str, click.BaseCommand]] = [
        ("junoscfg", main),
        ("junoscfg convert", convert),
        ("junoscfg edityaml", edityaml),
        ("junoscfg edityaml addvars", addvars),
        ("junoscfg edityaml ansibilize", ansibilize),
        ("junoscfg edityaml rename-root", rename_root),
        ("junoscfg schema", schema),
        ("junoscfg schema generate", generate),
        ("junoscfg schema info", info),
        ("junoscfg audit", audit),
        ("junoscfg audit unused", unused),
    ]

    parts: list[str] = []
    for name, cmd in sections:
        header = f"{separator}\n  {name}\n{'═' * 40}\n"
        # Build a standalone context so Usage shows "junoscfg <sub>" not "junoscfg junoscfg <sub>"
        help_ctx = click.Context(cmd, info_name=name)
        parts.append(header + cmd.get_help(help_ctx))

    click.echo("\n".join(parts))


# ── Helper functions ──────────────────────────────────────────────────


def _read_input(file: str | None) -> str:
    """Read input from file or stdin."""
    if file:
        with open(file) as f:
            return f.read()
    return sys.stdin.read()


@contextlib.contextmanager
def _failure_withheld(anonymizing: bool) -> Iterator[None]:
    """In an anonymized run, an exception no handler expects prints its class only.

    Its message and its chain may hold the configuration (a pass-through
    collision named its original address; a crash's traceback quotes what it
    was handed), so the run says only that it failed, and exits 1. A run that
    does not anonymize keeps its traceback.
    """
    try:
        yield
    except Exception as error:
        if not anonymizing:
            raise
        text = str(error)
        if not (isinstance(error, RuntimeError) and text.startswith("the conversion failed (")):
            # The library withholds its own failures already, in this same wording
            # (`pipeline_result`), and names the original class, which this cannot.
            text = (
                f"the conversion failed ({type(error).__name__}); details withheld: "
                "the run anonymizes"
            )
        click.echo(f"Error: {text}", err=True)
        sys.exit(1)


def _run_validation(
    source: str, input_format: str | None, artifacts_dir: str | None, *, anonymizing: bool = False
) -> None:
    """Run validation and report results.

    When the run anonymizes, a warning about a path of the input is printed
    without that path, as the conversion's own warnings are, and each error
    by its line alone: its text and path quote the input.
    """
    from junoscfg import validate_config
    from junoscfg.validate import SchemaLoadError

    try:
        result = validate_config(source, format=input_format, artifacts_dir=artifacts_dir)
    except SchemaLoadError as e:
        click.echo(f"Error loading validation artifacts: {e}", err=True)
        sys.exit(3)

    for warning in result.warnings:
        message = warning.message
        if anonymizing and warning.path:
            message = message.removeprefix(f"{warning.path}: ")
            message += " (the block's path is withheld: the run anonymizes)"
        click.echo(f"Warning: {message}", err=True)
    if result.valid:
        click.echo("Validation: OK", err=True)
    else:
        click.echo(f"Validation: FAILED ({len(result.errors)} error(s))", err=True)
        for err in result.errors[:10]:
            line_info = f" (line {err.line})" if err.line else ""
            if anonymizing:
                click.echo(
                    f"  - an error{line_info}: its text and path are withheld: the run "
                    "anonymizes (validate without --anonymize-* to see them)",
                    err=True,
                )
                continue
            path_info = f" at {err.path}" if err.path else ""
            click.echo(f"  - {err.message}{line_info}{path_info}", err=True)
        if len(result.errors) > 10:
            click.echo(f"  ... and {len(result.errors) - 10} more errors", err=True)
        sys.exit(1)
