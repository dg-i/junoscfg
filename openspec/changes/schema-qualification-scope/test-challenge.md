# Independent Test/Challenge

Independent read-only inspection before implementation; no product or test edits.
Graphify query was attempted but the isolated worktree has no graph.json.

## Must-cover execution boundaries

- Remove the blanket function-body exemption for validator.py,
  json_yaml_validator.py, xml_validator.py, set_validator.py and
  structured_validator.py. Validation algorithms and their transitive dependencies,
  notably junoscfg.input, are explicitly in the requested scope.
- Producer closure includes ArtifactBuilder, XSD extraction/parser/fixes,
  SchemaNode, schema/grammar generators and called display helpers. ArtifactBuilder
  calls open_artifact_write/read_artifact_text; generators use display schema
  helpers. Eager package doors and import-time hooks remain relevant. New execution
  imports cannot silently enter an exempt function body.
- Qualification harness closure includes tools.schema_verification,
  tools.schema_content_worker, dependency/selection policy, corpus suite,
  conftest and executed support fixtures; bind relevant options, manifests,
  dump bytes and shipped artifacts. Other tools files are not relevant solely by
  directory membership.
- Narrowing lock classification alone is insufficient: observe_versions binds
  every installed distribution, source_boundary binds every tools Python file
  and complete pyproject, and native engine identity independently binds runtime.
  All must agree on execution scope while native verification retains admission.
- Dependency projection must bind selected implementation bytes, package source
  and artifact identity, dependency edges and relevant resolution/Python constraints.
  Include transitives (jsonschema -> referencing -> rpds-py/attrs and pytest's
  execution dependencies). Updater-only change requires reviewed module projection,
  never a blanket agent-ready-checks exemption.
- Configuration should project actual execution settings: schema tier commands,
  inputs/runtime/manifests, pytest behavior and dependency selection. Unrelated
  lint/docs/template updater settings should not qualify. Unknown relevant shape
  should fail conservatively and explain why.

## Regression decisions

| Change/condition | Expected |
|---|---|
| README, AGENTS, skills, architecture prose | skip with valid evidence |
| unrelated tools helper or workflow updater | skip with valid evidence |
| root release version in project/module/lock | skip with valid evidence |
| unrelated dev dependency version/source/artifact | skip with valid evidence |
| checks 0.17.0 -> 0.17.1 updater-only release | skip with valid evidence |
| direct producer function body | qualify |
| producer's display helper | qualify |
| each validation algorithm body | qualify |
| transitive validator input/parser dependency | qualify |
| new import/decorator/metaclass executing exempt code | qualify if uncertain |
| relevant transitive package version/artifact | qualify |
| schema options, fixture, required manifest or dump | qualify |
| missing/corrupt/wrong-root receipt or changed output | qualify with reason |
| valid evidence followed by two unrelated commits | retain reuse |
| relevant runtime implementation change at same version | qualify |

Exercise negative rows through selection and actual native receipt validation
with tiny generated outputs: mocking established_context=True alone conceals
identity-wide invalidation. Keep ordinary tests, coverage and review unchanged.

## Verified updater regression provenance

Upstream `git diff checks-v0.17.0 checks-v0.17.1 --name-only` shows update.py as
sole changed checks runtime source. Other changes: test_update.py, checks package
and lock version bookkeeping, copier.yml, template pyproject, refresh skill copies
and the review document. checks-v0.17.1 resolves to local merge 4facc55.
Pair an updater-only projected module change with a verification execution module
change in the same distribution: first skips, second qualifies.

## Existing contradictory tests

Current consumer-body parameterization explicitly exempts json_yaml_validator.py;
replace that expectation to implement the user's validation-semantics scope.
Current dependency tests intentionally invalidate unrelated dependency changes;
replace obsolete whole-lock assertions with execution-closure assertions while
retaining malformed, absent and ambiguous-input rejection.
