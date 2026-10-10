<!-- The fields the gates read live in .openspec.yaml beside this file: type, zone, domains, removes, assurance, and declared-break, shaped `declared-break: {<surface>: {why: ..., migration: ...}}`. This file is the prose a human approves. -->

## Why

<!-- The problem or the opportunity, and why now. One or two sentences. -->

## What Changes

<!-- Specific: new capabilities, modifications, removals. Mark breaking changes **BREAKING**. -->
<!-- An override, fallback, parameter or environment read: one line naming the search you ran for the thing it configures and every reader it found. -->

## Capabilities

### New Capabilities
<!-- Each creates specs/<domain>/<capability>/spec.md; the domain is a key of [tool.template.domains]. -->
- `<domain>/<capability>`: <what it covers>

### Modified Capabilities
<!-- The exact existing path under openspec/specs/. Empty when no requirement changes; then set skip_specs: true in .openspec.yaml. -->
- `<domain>/<capability>`: <which requirement changes>

## Non-goals

<!-- What this change leaves alone, one line each. Non-goals live here and archive with the change. -->

## Impact

<!-- Affected code, APIs, dependencies, systems. -->
<!-- A figure this change rests on names the corpus and the command that reproduce it, both in this repository, so a reviewer can rerun it. -->
