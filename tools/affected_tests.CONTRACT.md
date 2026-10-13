# affected_tests — contract

Choose pytest paths from changed repository paths without executing inspected code.
Source package selection follows reverse imports and always includes contract tests.
Existing tooling modules follow reverse Python imports across both tools and all
Python tests, transitively, including imports of test helpers. Shared support or
root fixtures select the full suite. Nested fixtures select their directory.

Static absolute/relative imports and literal dynamic imports are understood.
File loaders in the selector and device-comparison tests are explicit audited AST
exceptions. Worker subprocess paths in the root fixture and schema verification
adapter are explicit edges. Changes to these mechanisms require re-auditing the
exception; a changed audited shape or an unknown loader selects the full suite.
Syntax/read failures also select the full suite because hidden consumers may live
outside tooling. Discovery is rebuilt for each selection, with no persistent cache.

Deleted/unmapped tooling modules and non-Markdown tooling configuration select all
tooling tests. Shared test data, project configuration, lock and shipped artifacts
select the full suite. Package data selects like its package's source; a non-Python
file at the package root selects the full suite. Test deletion/conftest rules retain
their containing scope; other non-Python test inputs select their directory.

A file outside `src/`, `tests/` and `tools/` is a dependency of every tools/tests
module that names it, or a directory above it, as a constant path from the
project root (`PROJECT_ROOT`, an alias, or `Path(__file__).resolve().parents[N]`
landing on the root). Consumers follow the import graph above, except that a path
named only inside a `test_*` function reaches that module alone. A computed root
path outside tooling raises, selecting the full suite; tooling's own computed
reads are covered because unclassified configuration also selects the tooling
suite. Documents (`.md`, `.rst`, `.txt`) and change records (`openspec/`,
`changelog.d/`, `.agent-ready/`, `.agents/`, `.claude/`, `.github/`, `docs/`) add
nothing beyond their named readers. Selected ancestors subsume their descendants.
This tool does not replace the full review checkpoint or schema tier.

With Strategy A enabled, ordinary execution uses the shared verification.execute
authority for the exact selected pytest command and current Python runtime. It
keeps full native input, base, environment and root identity; no local receipt store
or exemption is added. Missing/unavailable identity runs the selected tests normally;
a failed executed command returns failure without retry. Disabled policy executes
tests directly. Successful focused/no-coverage evidence is never full-suite coverage.

Private capture/schema directories, pytest/Junoscfg environment overrides, alternate
pytest configuration and unclassified configured options force direct execution.
The ordinary evidence authority cannot prove changing ignored/external input bytes
from their unchanged pathname. This deliberately broad refusal does not remove
options or tests; it returns the real pytest status. Schema qualification keeps its
separate declared-input evidence protocol.
