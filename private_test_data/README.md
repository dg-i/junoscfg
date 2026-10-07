# Private Test Data

Place private/real-world router configurations here for integration testing.
All files in this directory (except this README) are gitignored.

## Device XSD for `--regen-schema`

`pytest --regen-schema` regenerates the bundled schema artifacts from a NETCONF
XSD dump. Put the dump here as `*.xsd` and it is found automatically; the
newest by name wins. `JUNOSCFG_XSD_SOURCE` overrides the location.

Capture one with:

```bash
echo "<rpc> <get-xnm-information> <type>xml-schema</type> <namespace>junos-configuration</namespace> </get-xnm-information> </rpc>" \
  | ssh -Csp 830 router.example.com netconf > config-24.4.xsd
```

Without it the suite still runs in full against the committed artifacts and
warns that it could not regenerate.
