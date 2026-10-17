# Device captures

What Junos devices printed for configurations loaded on them: the oracle at
the top of the evidence hierarchy (`ARCHITECTURE.md`), above the schema model
and anything junoscfg generates. A test that disagrees with a capture is
wrong about Junos, never the capture.

## What a capture is

One configuration, loaded on a lab device in `configure private` with `load
override`, never committed there, and saved by the device with `show`, `show
| display xml`, `show | display json` and `show | display set`:
`<device>/<name>.{conf,xml,json,set}.gz`. Nothing is trimmed or re-rooted.
`manifest.json` lists every capture, every device's model and release (and
where the release was read), and the origin of every JVD configuration.

## What is here, and why so little

Few captures, each for something no other shows (`SELECTION` in
`tools/import_device_captures.py` gives the reason for each). `junoscfg-oracle`
is written for this: every construct the converters must carry, the routing
and system material the anonymizer needs, and an ELS switching section; the
vMX's renderings of it are `examples/`, the QFX5120's carry the switching
section on the release the shipped artifacts come from. Three JVD
configurations add what only real designs showed. The EX and QFX renderings
of the same configurations gave no junoscfg difference the vMX's did not, so
they, and the JVD configurations whose classes others already show, stay in
`private_test_data/`; the grammar corpus still draws on every line there.

`json-null-probes` asks the QFX5120 about junoscfg's own JSON rather than a
configuration: 15 statements the device prints as `{}`, 14 written as
junoscfg's `[null]` and the inactive leaf `l3vpn` written
`{"@": {"inactive": true}}`, where the device prints `"l3vpn": {}` beside
`"@l3vpn"`. Its source is JSON, loaded with `load override json`. A
`load merge json` of it (2026-10-16) loaded without error, and every
statement was then in the candidate, the leaf inactive. The capture of its
renderings awaits the device; until then the import keeps the source and
skips the capture (`CAPTURED` in the tool).

| Directory | Holds | Licence |
|---|---|---|
| `synthetic/sources/` | configurations written for these captures, following `AGENTS.md`'s test-data values | junoscfg's (MIT) |
| `synthetic/<device>/` | each device's renderings of them | junoscfg's (MIT) |
| `jvd/sources/` | three configurations from Juniper's Validated Designs, unmodified | Apache-2.0, `jvd/LICENSE`, `jvd/NOTICE` |
| `jvd/<device>/` | each device's renderings of them: derived works, see `jvd/NOTICE` | Apache-2.0 |
| `probes/<device>/<date>.json` | a device probe: the probe's own synthetic statements, the device's responses and renderings, sanitized (no host, user, prompt or time); not a capture | junoscfg's (MIT) |

Secrets in both sets are public: the synthetic ones are invented, and the JVD
ones are Juniper's published lab values. Each device re-encrypts them, so a
`$9$` value differs between devices, never between one capture's renderings.

A probe asks the device a few named questions instead of loading a whole
configuration (`docs/how-to/settle-a-schema-question.md`, rule 5). Its record
says what the device took and refused, with its response, and what it printed;
`tests/corpus/test_device_probes.py` holds junoscfg to it and checks that every
record is sanitized. The raw session stays in `private_test_data/`.

## What the tests read and ignore

`tests/support/devices.py` loads them; `tests/corpus/test_device_renderings.py`
holds junoscfg's set rendering of each format to the device's display set.
Comments are not statements and are ignored (`## Last changed`, `## Warning:
... unsupported platform`, `## SECRET-DATA`), as are the `junos:changed-*`
attributes, the XML `<cli>` banner and the release in the XML namespace.

`known-differences.json` records every line that differs today, with its
class: a junoscfg `defect`, an `equivalent` rendering the device loads alike,
an `open` question, or a `device-quirk` of the device's own renderings (the
curly `/* OMITTED */` of `apply-flags omit`, for one). A difference not
recorded fails, and so does a recorded one that is gone.
`grammar-corpus.json` holds the few device set lines that exercise every
grammar rule the many do, and every line the shipped grammar rejects.

## Adding or refreshing a capture

1. Capture on the device as above, into `private_test_data/<folder>/`; the
   capture log names lab devices and stays there.
2. `uv run python tools/import_device_captures.py` copies the renderings and
   sources here, gzipped reproducibly, and writes the manifest. A capture
   that awaited the device imports once its date is set in `CAPTURED`; for
   `json-null-probes` the renderings are `json-null-probes.{conf,xml,json,set}`
   in `private_test_data/qfx-null-probe/`, taken after `load override json`.
3. `uv run python tools/device_differences.py` rewrites the record; it stops
   on a line no class claims, which is classified before it is recorded.
4. After a grammar change or new set lines: `uv run python
   tools/device_grammar_corpus.py` (minutes).
