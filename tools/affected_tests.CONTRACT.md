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
select the full suite. Test deletion/conftest rules retain their containing scope.
Unrelated documents/bookkeeping select nothing. Selected ancestors subsume their
descendants. This tool does not replace the full review checkpoint or schema tier.

With Strategy A enabled, ordinary execution uses the shared verification.execute
authority for the exact selected pytest command and current Python runtime. It
keeps full native input, base, environment and root identity; no local receipt store
or exemption is added. Missing/unavailable identity runs the selected tests normally;
a failed executed command returns failure without retry. Disabled policy executes
tests directly. Successful focused/no-coverage evidence is never full-suite coverage.
