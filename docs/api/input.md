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
- `find_non_json_value(data)` returns the `(kind, path)` of the first value of a
  loaded document that JSON cannot hold (a timestamp, a non-string key, binary
  data, a set), or `None`. yaml-new conversion and validation refuse such a
  document; the path never holds the value.

Raw set readers apply bracket and command checks before normalization. The
checks classify lexical syntax; they do not validate configuration paths.

::: junoscfg.input
