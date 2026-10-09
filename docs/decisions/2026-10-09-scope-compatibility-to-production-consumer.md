---
status: accepted
scope: ["src/junoscfg/__init__.py", "src/junoscfg/cli.py"]
enforced-by: agent-ready lane
review-by: 2027-04-06
bans:
  - junoscfg.display.to_yaml.json_to_yaml
  - junoscfg.convert.output.xml_output
---

# Scope compatibility to the production consumer

## Context

The beta stage treated every symbol Griffe discovered in every implementation
submodule as the `api` compatibility surface. That prevented removal of an
unused direct JSON-to-YAML helper and an XML-output stub, even though neither
was documented as a primary entry point or used by the production consumer.

The owner permits package API changes provided they do not break
`dg-i/ansible-collection-junos-config`. At its inspected HEAD, that collection
imports exactly `convert_config`, `validate_config`, `Format`, and
`FieldValidationError` from the top-level package. Its pipelines also use the
documented CLI conversion and `edityaml` commands. All 33 collection tests pass
against the roadmap integration checkout.

## Decision

Name `consumer` and `cli` as the beta compatibility surfaces. The consumer
surface is the top-level package, pinned by the collection's real imports and
test suite; implementation submodules and secondary package doors remain
documented conveniences but may change in a minor release.

Retire the unused `json_to_yaml` helper and the XML-output module. JSON-to-YAML
conversion remains available through `convert_config()`, and XML output keeps
raising the same `NotImplementedError` through `convert_config()` and
`junoscfg.convert.from_dict()`.

## Consequences

- A minor release may change a secondary package-door API without a prior
  deprecation when the production collection and CLI remain compatible.
- Changes to `src/junoscfg/__init__.py` or `src/junoscfg/cli.py` still require a
  declared surface break and the configured minor bump where compatibility
  changes.
- The retired imports are banned so they cannot return accidentally.
