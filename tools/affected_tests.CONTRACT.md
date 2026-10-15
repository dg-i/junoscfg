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
select the full suite. Package data (anything but Markdown) selects like its
package's source; a non-Python file at the package root selects the full suite.
A changed test module selects itself and the test modules that import it,
transitively, under the same fixture and uncertainty rules as a tool.
Test deletion/conftest rules retain their containing scope; other non-Markdown
test inputs select their directory. Changed paths come from Git without rename
detection, so a moved file also lists its old path.

A tools/tests module reads a repository path when an expression it evaluates is
anchored there: the project root (`Path(__file__)` with `.resolve()`, `.parent`,
`.parents[N]`), or a module-level name assigned such a path, including names
imported from another module or reached through a module alias, extended by `/`,
`joinpath`, `glob`/`rglob` (up to the first wildcard), `resolve` or `absolute`.
Assigning one to a name is not a read; its uses are, except in shared support,
where declaring a directory makes it shared test input. A file outside `src/`,
`tests/` and `tools/` selects the consumers of each module reading it or a
directory above it; consumers follow the import graph above, except that a path
read only inside a `test_*` function reaches that module alone unless another
module imports its tests. Outside tooling, a read of the root itself or a path
computed directly below it (passing the root anywhere, a computed `/` part) makes
the module a reader of every outside file. Tooling's own computed reads are taken
to read tooling inputs: unclassified configuration also selects the tooling suite,
while documents (`.md`, `.rst`, `.txt`), change records (`openspec/`,
`changelog.d/`, `.agent-ready/`, `.agents/`, `.claude/`, `.github/`, `docs/`,
`mkdocs.yml`, `LICENSE`, `.copier-answers.yml`) and the gitignored
`private_test_data/` add nothing beyond their readers. A module that cannot be
parsed or whose imports cannot be followed reads every outside file; only a tool
change escalates it to the full suite. A changed reader, or a deleted tests/tools
module, also selects the selector's own repository-reader assertions.
Selected ancestors subsume their descendants and node IDs below them. This tool
does not replace the full review checkpoint or schema tier.

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
