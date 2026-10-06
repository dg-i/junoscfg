## Terms

<!-- agent-ready:retires:begin -->
<!-- agent-ready:retires:end -->

No vocabulary is retired. `crypt` survives legitimately in prose: the module
docstring still explains what a `$6$` SHA-512 crypt hash is, which is a Junos
format and not the Python module.

## Symbols

None removed. `_make_crypt_hash` keeps its name and signature; only its body
changes.

## Dependencies

- The stdlib `crypt` module, which was never a declared dependency and is gone
  from Python 3.13. The `deptry` DEP001 ignore that covered it goes too.

## Requirements

None; `skip_specs: true`.

## Tests and fixtures

None retired. The six previously-failing tests now pass unchanged.

## Docs

None. No document described the crypt branch.
