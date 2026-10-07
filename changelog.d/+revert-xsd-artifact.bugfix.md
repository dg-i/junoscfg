Revert the `junos-validated.xsd` artifact added in 0.6.4. A raw NETCONF dump does not compile as an XSD, so the file was unusable — and `--regen-schema` would have put 156 MB of it into the wheel.
