`yaml-new` input now accepts a block shared through a YAML anchor and alias, read as if
written out at each place (it was refused). A block that contains itself is still refused,
now as a `cycle` with its path (`has no JSON spelling`). The interim alias bounds this
change introduced are replaced by a fixed 64-level ceiling (see the yaml-depth-ceiling
entry). `junoscfg.input.find_non_json_value` returns the new `NonJsonValue`.
