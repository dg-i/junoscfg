`yaml-new` input now accepts a block shared through a YAML anchor and alias, read as if
written out at each place (it was refused). A block that contains itself is still refused,
now as a `cycle`, and an alias is refused when, written out, the document would hold more
than twice its values or nest deeper than written, so alias bombs stay harmless. This only
loosens what is accepted; refusal messages now end with the reason (`has no JSON spelling`,
`expands the document past twice its size`, `nests the document deeper than it is
written`). `junoscfg.input.find_non_json_value` returns the new `NonJsonValue`.
