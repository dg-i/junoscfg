"""Junoscfg CLI: convert and validate Junos configurations."""

from __future__ import annotations

import sys

import click

from junoscfg import Format, __version__

_FORMAT_CHOICES = [f.value for f in Format] + ["conf"]

_CONTEXT_SETTINGS = {"help_option_names": ["-h", "--help", "-?"]}


class DefaultGroup(click.Group):
    """Click group that defaults to 'convert' subcommand for backward compat."""

    def parse_args(self, ctx: click.Context, args: list[str]) -> list[str]:
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
    "--anonymize-ignore-subnets", is_flag=True, help="Treat sub-/8 private ranges as public."
)
@click.option(
    "--anonymize-ignore-reserved", is_flag=True, help="Remove all reserved range handling."
)
@click.option(
    "--anonymize-ips-in-strings",
    is_flag=True,
    help="Also replace IPs embedded in larger strings (URLs, host+IP combos).",
)
@click.option(
    "--anonymize-as-numbers-in-strings",
    is_flag=True,
    help="Also replace target AS numbers embedded in larger strings (group names, communities).",
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
    help="Anonymization logging verbosity.",
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
      yaml         Standard YAML (1:1 mapping of Junos JSON)

    \b
    Examples — Conversion:
      junoscfg convert -i json -e set config.json       Convert JSON to set
      junoscfg convert -i structured -e set config.conf Convert structured to set
      junoscfg convert -e structured config.json        Auto-detect input format
      junoscfg convert -i conf -e set config.conf       "conf" alias for structured
      junoscfg convert -i json -e json config.json      Identity (normalize JSON)
      junoscfg convert -i set -e set config.set         Identity (normalize set)

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

    # If validate-only (no export format), just validate
    validate_only = validate and not export_format

    if not export_format and not validate:
        click.echo(
            "Error: specify -e/--export-format (set, structured, json, yaml).",
            err=True,
        )
        sys.exit(2)

    # Read input
    source = _read_input(file)
    if not source.strip():
        return

    # Auto-detect import format if not specified
    if not import_format:
        import_format = _detect_format(source)

    # Validate if requested
    if validate or validate_only:
        _run_validation(source, import_format, artifacts)
        if validate_only:
            return

    # Build anonymization config if any anonymize flags are set
    from junoscfg.anonymize.config import build_config_from_cli

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
        anonymize_ignore_subnets=anonymize_ignore_subnets,
        anonymize_ignore_reserved=anonymize_ignore_reserved,
        anonymize_ips_in_strings=anonymize_ips_in_strings,
        anonymize_as_numbers_in_strings=anonymize_as_numbers_in_strings,
        anonymize_log_level=anonymize_log_level,
        anonymize_config=anonymize_config,
    )

    # Convert using the unified API
    from junoscfg import convert_config

    from_fmt = Format(import_format)
    to_fmt = Format(export_format)

    field_validate = not no_field_validate

    try:
        result = convert_config(
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

    if result:
        click.echo(result, nl=False)


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

    from junoscfg.edityaml import apply_rules
    from junoscfg.edityaml.rules import load_rules_file, merge_rulesets, parse_inline_rules

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
    click.echo(yaml.dump(result, default_flow_style=False), nl=False)


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
        from junoscfg.edityaml.ansibilize import (
            ansibilize_with_offset,
            format_output_with_offset,
        )

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
        from junoscfg.edityaml.ansibilize import ansibilize_multi, format_output

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
        from junoscfg.edityaml.path_walker import resolve_path

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
    click.echo(yaml.dump(out, default_flow_style=False), nl=False)


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
    from junoscfg.validate.artifact_builder import ArtifactBuilder

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
@click.argument("xsd_source", type=click.Path(exists=True))
@click.option("-o", "--output", "output_file", type=click.Path(), default=None, help="Output file.")
@click.option("--max-depth", type=int, default=0, help="Maximum nesting depth (0 = unlimited).")
@click.option(
    "--section", default=None, help="Only show this section (e.g. 'system' or 'system syslog')."
)
@click.option("--no-enums", is_flag=True, help="Omit enum value listings.")
@click.option("--no-deprecated", is_flag=True, help="Omit deprecated elements.")
@click.option("--compact", is_flag=True, help="Omit descriptions, show only structure.")
def makedoc(
    xsd_source: str,
    output_file: str | None,
    max_depth: int,
    section: str | None,
    no_enums: bool,
    no_deprecated: bool,
    compact: bool,
) -> None:
    """Generate a YAML-like configuration reference from XSD.

    \b
    Examples:
      junoscfg schema makedoc netconf.xml -o reference.yaml
      junoscfg schema makedoc netconf.xml --section "system" --compact
      junoscfg schema makedoc netconf.xml --max-depth 3 --no-deprecated
    """
    from junoscfg.validate.schema_doc import generate_doc

    try:
        result = generate_doc(
            xsd_source,
            max_depth=max_depth,
            section=section,
            no_enums=no_enums,
            no_deprecated=no_deprecated,
            compact=compact,
        )
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(3)

    if output_file:
        with open(output_file, "w") as f:
            f.write(result)
        click.echo(f"Written to {output_file}", err=True)
    else:
        click.echo(result, nl=False)


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
    from junoscfg.validate.validator import JunosValidator

    try:
        v = JunosValidator(artifacts_dir=artifacts)
        click.echo(f"Schema version: {v.schema_version}")
        click.echo(f"Generated at:   {v.generated_at}")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(3)


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
        ("junoscfg schema makedoc", makedoc),
        ("junoscfg schema info", info),
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


def _detect_format(source: str) -> str:
    """Auto-detect input format from content."""
    stripped = source.strip()
    if stripped.startswith("{") or stripped.startswith("["):
        return "json"
    if stripped.startswith("<"):
        return "xml"
    from junoscfg.display import is_display_set

    if is_display_set(stripped):
        return "set"
    return "structured"


def _run_validation(source: str, input_format: str | None, artifacts_dir: str | None) -> None:
    """Run validation and report results."""
    from junoscfg import validate_config
    from junoscfg.validate import SchemaLoadError

    try:
        result = validate_config(source, format=input_format, artifacts_dir=artifacts_dir)
    except SchemaLoadError as e:
        click.echo(f"Error loading validation artifacts: {e}", err=True)
        sys.exit(3)

    if result.valid:
        click.echo("Validation: OK", err=True)
    else:
        click.echo(f"Validation: FAILED ({len(result.errors)} error(s))", err=True)
        for err in result.errors[:10]:
            line_info = f" (line {err.line})" if err.line else ""
            path_info = f" at {err.path}" if err.path else ""
            click.echo(f"  - {err.message}{line_info}{path_info}", err=True)
        if len(result.errors) > 10:
            click.echo(f"  ... and {len(result.errors) - 10} more errors", err=True)
        sys.exit(1)
