# Instruction audit

## Outcome

The owner sees the observable instruction surface, including blind spots, and
one evidence-backed finding per conflict, ambiguity, or stale instruction.
Mechanical defects are repaired only inside the boundary below. Meaning is
never changed without the owner's decision.

Run once per garden cycle in a fresh session as `agent-ready-garden
instructions full` or `agent-ready-garden instructions changed`. If the mode
is absent, use `full` and say so. Run directly; do not delegate a comparison
that needs one consistent view of precedence and scope.

## Modes

`full` reads the entire observable instruction surface. Use it for the first
and release-time runs, after the runtime or provider changes, and after a root
instruction, loading rule, generated bridge, or precedence rule changes.

`changed` reads the complete repository diff since `instructions-swept`, not
only changed instruction sources. From code, configuration, schema, workflow,
and documentation changes, collect removed, moved, or renamed paths, commands,
keys, flags, tools, roles, models, steps, and behavioural promises. Search the
full observable instruction surface for them and include every match. Also read
each changed source's intersecting parent, nested instruction, mirror, bridge,
import, reference, same-subject source, and runtime constraint.

A changed high-impact term widens the scan to the full affected scope: `not`,
`never`, `no`, `except`, `unless`, `must`, `shall`, `should`, `may`, `required`,
`optional`, `only`, `all`, `none`, `before`, `after`, `first`, or `last`. Root,
loading, precedence, or scope-boundary changes widen to `full`; case and
punctuation do not prevent it. An absent or invalid baseline also means `full`.

## Observable instruction surface

Inventory every source that can instruct the agent, not merely `AGENTS.md`:

- system, developer, organisation, workspace, user, and task prompts;
- root and nested Codex `AGENTS.md`, Claude `CLAUDE.md`, and provider files;
- skills, slash commands, agent profiles, hooks, and provider configuration;
- OpenSpec schemas, templates, proposals, tasks, and workflow prompts;
- plugin, tool, MCP, sandbox, and runtime instructions;
- mandatory guides, policies, mirrors, bridges, imports, and referenced files.

Semantically compare runtime or platform instructions visible in the current
context, but never quote or persist protected prompt text. Describe only its
safe source class, scope, precedence, and operational effect. Never claim an
inaccessible source was checked.

Before findings, report mode, baseline and target commits, runtime/provider,
date, discovery methods, exclusions with reasons, and blind spots. Give counts
for discovered, read, protected-but-semantically-considered, and inaccessible
sources. List each source or protected class with effective scope, precedence,
loading path, and status (`read`, `protected`, or `inaccessible`). `full` means
the full observable surface relative to those methods, never hidden content.

## Findings

Apply known runtime precedence; never invent precedence between repository
sources. Raise findings for direct contradiction, precedence ambiguity, scope
error, impossible set, provider divergence, stale instruction, duplicate
ownership with material drift risk, and contradiction with enforced repository
state. Wording alone is not a finding when effects and ownership agree.

For each finding give both sources or repository evidence, short permitted
quotes, effective scopes, precedence, concrete consequence, recommendation,
decision owner, and `Automatic correction: yes|no` with its reason. Separate
evidence from inference.

## Correction boundary

Automatically correct only an exact mirror mismatch from its declared source,
an unambiguous broken pointer with exactly one intended existing target, a
mechanically incorrect generated bridge, or a plain-prose spelling/formatting
defect with one meaning-preserving correction. Report before, after, reason,
and verification, and keep each finding in its own small PR.

Never automatically change negation, modality, exclusivity, ordering, paths,
commands, identifiers, model names, versions, dates, numbers, security terms,
quoted text, or ambiguous spelling. A short word such as `NOT` is semantic
evidence, not a typo.

All direct contradictions, precedence ambiguities, scope errors, impossible
sets, and other meaning changes require the owner to choose. Batch questions
with evidence and a recommendation under the Asking rule and edit neither side
while waiting. Implement the decision through `agent-ready-change`; this job
discovers and frames it but cannot approve it.

## Finish

Run `agent-ready skills` after a skill or mirror repair and the relevant checks
after every repair. Set `instructions-swept` to the target only after complete
coverage, verified repairs, and every semantic finding is resolved or durably
owner-visible; never hide an unanswered transcript-only finding.

At release, use disposable direct-conflict, unclear-precedence, nested-scope,
provider-divergence, and changed-`NOT` examples. They must produce findings,
remain unrepaired, and leave `instructions-swept` unchanged.
