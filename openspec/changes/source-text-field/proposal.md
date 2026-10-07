## Why

`networks=["auto"]` asks the IP rule to scan the configuration text for subnets
and preserve their structure. It read that text from `config._source_text`, an
attribute no dataclass declared: `cli.py` attached it dynamically behind a
`# type: ignore[attr-defined]`, and `rules/ip.py` read it back through
`hasattr`.

So the feature worked from the CLI and silently did nothing through the
documented Python API. A caller asked for auto-detection, got no error, no
warning, and no auto-detection. Onboarding phase 3 pinned it as a defect.

## What Changes

- `source_text` is a declared field on `AnonymizeConfig`, so it type-checks and
  anyone reading the dataclass can see it exists.
- `networks=["auto"]` without it raises `ValueError` naming the field, instead
  of quietly producing nothing.
- `cli.py` assigns the declared field and drops its `type: ignore`.
- The characterization pin is rewritten: it recorded the silent no-op and now
  records the error and the working path.

## Capabilities

### New Capabilities

None; this makes an existing option work where it previously did nothing.

### Modified Capabilities

No requirement changes, so `.openspec.yaml` sets `skip_specs: true`.

## Non-goals

- Making `auto` fall back to scanning the IR instead of the source text. The
  IR has already been parsed, and reconstructing the text to scan it would be a
  second way to do the same thing.

## Impact

`src/junoscfg/anonymize/config.py` and `rules/ip.py` (red zone), and `cli.py`.
A Python caller passing `networks=["auto"]` without `source_text` now gets a
`ValueError` where it previously got silently unanonymized networks — louder,
and the old behaviour was the dangerous one. The CLI is unaffected: it has
always supplied the text, verified end to end.
