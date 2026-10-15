YAML input no longer guards against alias bombs: junoscfg assumes its YAML input is not
hostile, and a caller handling untrusted YAML bounds it before calling junoscfg. `yaml-new`
input reads a block shared through an alias however often and wherever it is reused (the
size and depth bounds of the previous release are gone), and refuses only a cycle and a value
nested deeper than 64 levels, which no Junos configuration approaches, with its path: in
conversion, in `validate_config`, and in the yaml-new writer, whatever the input format
(text nested past about 490 levels still fails inside PyYAML's loader, as before).
The `yaml` reader now refuses a cycle and such a value the same way (outside its
`_ansible_*` and `_meta_*` keys) where it crashed with `RecursionError`. Refusal messages say
"is nested deeper than 64 levels"; the kind `alias` is gone. `find_non_json_value` gains the
`scalars` and `unwalked` keywords and `NonJsonValue.where` and `read_refusal`.
