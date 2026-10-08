## Why

`junoscfg convert -i xml` printed a Python traceback on input it could not
parse. Malformed JSON reports `Error: Expecting ',' delimiter ...` and exits 2;
malformed XML reports a usage error and exits 2; XML whose namespace prefix is
undeclared raised `lxml.etree.XMLSyntaxError` straight through the CLI.

That shape is not exotic. A device renders `show configuration | display xml`
inside an `<rpc-reply>` carrying the `junos:` namespace declaration, and the
`<configuration>` element inside uses that prefix for its commit attributes.
Pasting the inner element on its own — the obvious thing to do when you want
the configuration and not the envelope — leaves the prefix undeclared.

Found while checking how junoscfg handles `<undocumented>`, the wrapper Junos
puts around statements it does not publish in its schema. That part was
already right: the wrapper is skipped and the output matches the device's own
JSON and set rendering exactly.

## What Changes

- `xml_to_yaml` catches `XMLSyntaxError` and raises a `ValueError` naming the
  parse failure, which the CLI already renders as an error with exit 2.

## Capabilities

### New Capabilities

None; this repairs an existing one.

### Modified Capabilities

No requirement changes, so `.openspec.yaml` sets `skip_specs: true`.

## Non-goals

- Accepting a `<configuration>` element whose namespace prefix is undeclared.
  It is not valid XML, and guessing a declaration would be inventing input.
- `set groups chassis-vMX chassis dump-on-panic` still failing validation.
  `dump-on-panic` sits inside `<undocumented>` and appears nowhere in any
  NETCONF XSD, so no schema will ever model it.

## Impact

`src/junoscfg/display/to_yaml.py`. The traceback becomes
`Error: Invalid XML: Namespace prefix junos for commit-seconds on
configuration is not defined, line 1, column 122`. Two tests, one of them seen
to fail with the catch removed.
