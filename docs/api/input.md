# junoscfg.input

Shared lexical checks and normalization for configuration readers.

- `InputError` is a `ValueError` with an optional one-based `lineno`.
- `find_unsupported_set_brackets(source)` returns `(line, message)` findings
  for unquoted brackets; its messages include the original offending line.
- `find_unsupported_set_commands(source)` returns `(line, message)` findings
  for unsupported command spellings or commands without a path. Messages
  contain only the physical line number, without source values.
- `iter_visible_set_lines(source)` yields physical line number, original line
  and visible content after leading comments.
- `normalize(source)` reads text or a text stream, removes ignored comments
  and blank lines, normalizes carriage returns and joins bracket continuations.
- `find_non_json_value(data, *, scalars=True, unwalked=())` returns a
  `NonJsonValue(kind, path, reason)` for the first place a loaded document stops
  being a JSON document junoscfg can walk, or `None`: a `cycle`, a `value`
  nested more than 64 levels deep, a mapping key that is not a string (`int
  key`, `date key`, at its mapping's path), and with `scalars` a value JSON
  cannot hold (a timestamp, binary data, a set). Values under a mapping key
  starting with a prefix in `unwalked` are not walked. A mapping or list
  shared through an alias is walked at every place, however often, as JSON
  would write it out; configuration input is trusted (decision
  2026-10-15-configuration-input-is-trusted), so an alias bomb costs its
  expansion. `NonJsonValue.where` is `at <path>` or `at the top level`, and
  `read_refusal(label)` the message a reader of `YAML` or `JSON` text raises.
  The yaml-new reader, writer and validation share it, the `json` reader, and
  the `yaml` reader and validation with `scalars=False` and `META_KEY_PREFIXES`;
  the path never holds the offending value or key.
- `META_KEY_PREFIXES` are the key prefixes of the Ansible inventory artefacts
  the `yaml` format leaves unread (`_ansible`, `_meta_`).

Raw set readers apply bracket and command checks before normalization. The
checks classify lexical syntax; they do not validate configuration paths.

::: junoscfg.input
