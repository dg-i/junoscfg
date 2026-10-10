# Agent-guidance lessons from `identifier-key-fields`

Date: 2026-10-10

## Scope

This review compares two completed executions of the same junoscfg change from
the same approved intent commit:

- the orchestrated pilot, which discovered requirements with the owner and used
  specialised fresh agents; and
- the autonomous single-agent replay, which received the settled owner decisions
  and sanitised device facts before starting.

The review asks only how junoscfg's local instructions and evidence surfaces can
improve. It does not decide which implementation to keep, backport code, or
redesign the generic `agent-ready-python` workflow. Those are active in the
separate tasks **Consolidate identifier-key-fields** and **Improve change
workflow**, respectively.

Evidence came from both branches, their phase reports, gates, deviations and
state files, their OpenSpec change folders, and deduplicated local runtime
events. No private device value is reproduced here. The repository graph was
used to trace instruction-to-contract-to-test relationships; claims below were
then checked against the source documents.

## Executive judgement

junoscfg's strongest controls worked: synthetic test-data rules prevented device
data leakage, the evidence hierarchy eventually corrected schema assumptions,
the one-IR architecture focused the change, and fresh review prevented silent
loss from reaching the final result.

The main weakness was not agent capability. The operative truth was fragmented.
Before the replay froze it, an agent had to reconstruct the intended behaviour
from `ARCHITECTURE.md`, `AGENTS.md`, module contracts, OpenSpec deltas, private
device output, owner chat answers and corrections from earlier phases. The pilot
therefore spent three spec passes and five device-probe rounds settling rules
that later let the replay finish without owner intervention.

The correct local response is:

1. keep architectural policy short and authoritative;
2. put stable module invariants in the relevant `CONTRACT.md` and main specs;
3. freeze sanitised device facts once per device-sensitive change;
4. select expensive junoscfg gates from the paths and risks touched; and
5. retain fresh independent review for cross-domain schema and conversion work.

## Experiment comparison

| Measure | Orchestrated pilot | Single-agent replay |
|---|---:|---:|
| Requirements at start | Incomplete; discovered during the run | Settled decisions and device facts frozen up front |
| Elapsed session span | About 8 h 8 min | About 2 h 38 min |
| Owner interaction after start | Substantial | None |
| Specification executions | Initial run plus two corrections | One |
| Device-probe rounds | Five | None; sanitised results supplied |
| Test phase | About 50 min | About 29 min |
| Main implementation phase | About 2 h 34 min, including a stall and two resumptions | About 1 h 29 min |
| Review | Fresh, stronger reviewer | Same-session self-review |
| First review findings | 3 High, 2 Medium, 5 Low | 1 High, 1 Low |
| Later correction/re-review | Fix pass, fresh re-review, small final refactor | Short fix pass and focused self-re-review |
| Measured change footprint | 87 files, +6,742/-705, 5 binary | 47 files, +2,679/-722, 5 binary |
| Final gates | Green | Green |

The replay is not a blind A/B result. It was deliberately advantaged by the
pilot's owner answers, router observations and review-derived invariants. It
therefore demonstrates the value of settled evidence and autonomous progression,
not that self-review can replace independent review.

Runtime pricing is not compared. The phase metrics correctly left cost and
tokens unmeasured, and the interactive runtime logs are not the supported
metrics input. A consistent local deduplication shows fewer response events and
far fewer cache reads in the replay, but not fewer output tokens; shorter elapsed
time must not be reported as lower cost without provider billing evidence.

## What the two runs teach

### 1. Fresh review paid for itself

The pilot's fresh reviewer found three silent or correctness-breaking classes
after the full gate was green: numeric `maxOccurs` entries collapsed, keyworded
key fields were interpreted positionally, and open `name` identifiers were
validated as closed enums. Corpus evidence also exposed a large performance
regression. These were not formatting defects; they contradicted Junos
correctness.

The replay already had those invariants in its frozen packet and still found a
new High defect: meta commands with partial or surplus keys could modify the
wrong parent or entry. Its same-session review caught that because the prompt
named concrete adversarial invariants, but its verdict explicitly retained a
shared-blind-spot risk.

**Local implication:** keep [solo review](../how-to/solo-review.md) and the
fresh-session rule. Schema-parser, artifact, conversion, grammar, validation or
anonymization changes that cross more than one of those boundaries should
always receive an independent adversarial corpus review, regardless of whether
the implementation gates are green.

### 2. The full gate was necessary but insufficient

The pilot's first implementation passed the normal full check while the
`--jvd` warning budget and `--schema` evidence would have exposed two of the
three High findings. The full gate optimises routine feedback; it cannot be the
only oracle for a schema-wide change.

**Local implication:** junoscfg needs a path-to-risk gate table. At minimum:

| Changed concern | Required pre-review evidence |
|---|---|
| XSD parser, schema node, fixes or artifact builder | schema tier, one final regeneration, reproducibility comparison |
| Set reader or grammar | base/head corpus acceptance diff and no-silent-loss probes |
| Field validation | jvd warning budget and representative strict-mode probes |
| Cross-format IR or writer | set/structured/JSON/YAML/XML semantic parity and round trip |
| Anonymization | red-zone tests, syntax-value preservation, mapping stability |
| Entry lookup or a schema-wide walk | bounded large-case timing against a frozen baseline |

The table belongs in the developer guide, with a short pointer in `AGENTS.md`.
It should not inflate `ARCHITECTURE.md`.

### 3. Device evidence should be one reviewed input, not a chat stream

Five pilot rounds were partly caused by legitimate discovery, but also by
flawed or incomplete probes: an invalid route-filter action, a nonexistent
modifier, a missing parent-level line and pre-existing configuration in a
preflight. Each new result had to be relayed into a running agent.

The replay's frozen, sanitised packet removed this coordination cost. It also
made the provenance and precedence explicit without exposing device content.

**Local implication:** extend [Settle a schema question](../how-to/settle-a-schema-question.md)
with a junoscfg device-evidence form containing:

- the exact hierarchy and question;
- accepted and rejected forms, including order and surplus-token variants;
- requested set, JSON and XML views;
- clean preflight and explicit rollback/cleanup confirmation;
- device family/release, with operator values removed;
- observation, interpretation and remaining unknowns as separate fields; and
- one owner approval of the sanitised summary before specification work resumes.

The incoming generic evidence-freeze mechanism can carry this form; junoscfg
should own the networking-specific questions and privacy rules.

### 4. Stable invariants are missing from module contracts

The architecture now states Junos correctness and the evidence hierarchy, but
the contracts agents read immediately before editing do not yet carry the
stable rules this experiment proved. In particular:

- `display/CONTRACT.md` does not state that one kernel answer owns entry keys,
  statement children and positional-versus-keyword key form;
- `validate/CONTRACT.md` does not state the cardinality rule or the relationship
  between declared keys and generated artifacts;
- `convert/CONTRACT.md` does not state that incomplete data and meta statements
  must remain whole and loud across every reader; and
- `anonymize/CONTRACT.md` does not state that schema enum values are syntax and
  must not be anonymized.

**Local implication:** after the consolidation task settles the final names,
add each invariant and its public regression test to the owning contract. Do
not put change-specific helper names into `ARCHITECTURE.md`, and do not duplicate
the same rule in several contracts.

### 5. Several instruction sources currently disagree

The experiment encountered or revealed concrete drift:

- phase 4 says Hypothesis is already approved, while `docs/TOOLBOX.md` does not
  list it;
- the developer guide says field validation prints warnings to stderr, while
  `ARCHITECTURE.md` says library calls return diagnostics and never write them
  to a terminal;
- the developer guide calls name-based fallback constants safe, while the
  evidence hierarchy requires a documented fallback and prefers correction at
  the schema-owning layer; and
- regeneration guidance says when to run `--regen-schema`, but not that agents
  should explore in scratch output, perform one official final regeneration,
  and avoid expensive confirmation-only rebuilds.

**Local implication:** run an instruction-consistency edit after the two active
tasks finish. `ARCHITECTURE.md` decides system truth; contracts decide module
truth; the developer guide explains mechanics; `AGENTS.md` links to them. A
lower-level guide must not introduce a competing policy.

### 6. No-silent-loss review must include metadata operations

Both runs concentrated initially on data statements and token consumption. The
replay showed that `deactivate`, `activate`, `protect` and `delete` can violate
the same invariant even when ordinary set lines are correct.

**Local implication:** the conversion review checklist should cross three axes:

1. complete, partial, surplus and missing keys;
2. set, structured, JSON, YAML and XML entry paths; and
3. ordinary statements plus every supported metadata verb.

One table-driven test matrix is preferable to repeating the same examples in
many phase prompts.

### 7. Product latency and workflow latency are different priorities

`ARCHITECTURE.md` correctly ranks product runtime latency below correctness and
simplicity. That sentence does not mean multi-minute regenerations, corpus runs
and duplicate gates are free during development.

**Local implication:** state in the testing section that the architecture's
runtime quality ranking does not waive workflow economy. Reuse immutable
base-line results, run focused tests while editing, regenerate only after the
generator is final, and rerun an expensive gate only when an input that
invalidates its result changed.

## Short SWOT analysis

### Strengths

- Explicit one-IR architecture and owning-layer rule.
- Synthetic test-data conventions and private capture boundary worked.
- OpenSpec requirements, named tests and review challenges leave a strong audit
  trail.
- Fresh-agent review and corpus evidence caught defects normal gates missed.
- Generated artifacts and public package doors are clearly governed.

### Weaknesses

- Authoritative behaviour is fragmented across too many surfaces.
- Expensive test tiers are documented but not selected automatically from risk.
- Local toolbox and generic phase guidance disagree.
- Owner and device decisions were initially transient chat state.
- Supported metrics left human effort, retries, phase span and tokens unmeasured.

### Opportunities

- A single sanitised device-evidence artifact per change.
- Risk-triggered schema, corpus, parity and performance gates.
- Stronger module contracts backed by public regression tests.
- Frozen baselines and compact table-driven cross-format fixtures.
- Provider-neutral telemetry from the incoming workflow work.

### Threats

- Same-session review can share the implementation's assumptions.
- Costly, repetitive gates encourage agents to skip the most valuable probes.
- Copied policy text will drift and produce plausible but contradictory actions.
- Raw router evidence can leak if sanitisation remains an informal relay.
- Overly compressed line caps can move important criteria into the wrong
  artifact instead of making them clearer.

## Actionable junoscfg improvements

| Priority | Improvement | Primary location | Acceptance evidence |
|---|---|---|---|
| P0 | Add the path-to-risk gate table and exact commands | `docs/architecture/developer-guide.md`; pointer in `AGENTS.md` | A schema-parser change's task list includes schema, corpus, parity and performance evidence before review |
| P0 | Preserve fresh independent review for cross-domain schema/conversion and anonymization work | `docs/how-to/solo-review.md` and local change guidance | Reviewer session did not implement; report contains independent corpus/adversarial probes |
| P0 | Add settled entry/cardinality/no-silent-loss/enum invariants to owning contracts after consolidation | four module `CONTRACT.md` files | Each invariant names a public regression test and has one owner |
| P1 | Add the sanitised device-evidence form and consolidated probe checklist | `docs/how-to/settle-a-schema-question.md` | One approved summary answers all device-dependent spec questions; raw output stays private |
| P1 | Reconcile the four documented instruction conflicts | developer guide, toolbox and phase-4 guidance | Repository search yields one answer for Hypothesis, diagnostics, fallbacks and regeneration policy |
| P1 | Extend the conversion review matrix to metadata verbs and structured missing-key cases | conversion bugfix guide or a linked review checklist | Tests cover four metadata verbs over complete, partial and surplus keys across applicable doors |
| P1 | Document scratch generation, one official regeneration and invalidation rules | developer guide testing tiers | Phase evidence records regeneration count and why an additional run was necessary |
| P2 | Keep `ARCHITECTURE.md` policy-only and replace duplicated prose with links | `AGENTS.md`, developer guide, how-to pages | No lower-level document states a competing evidence or correctness policy |
| P2 | Configure incoming provider-neutral telemetry for junoscfg's expensive tiers and human device work | local workflow configuration after **Improve change workflow** lands | Phase span, test duration, retries, regenerations and owner/device interventions are measured rather than estimated |
| P2 | Prefer one data-driven public-door matrix plus small focused regressions | phase-4 local guidance | New cross-format changes avoid duplicating equivalent fixtures while every specified door remains exercised |

## Recommended sequence

1. Let **Consolidate identifier-key-fields** settle the implementation and
   helper names; do not write contracts against moving names.
2. Let **Improve change workflow** land the generic evidence freeze, automatic
   progression, cached baselines and telemetry; do not recreate them locally.
3. Apply the P0 contract and risk-gate changes in one junoscfg documentation
   change, with a fresh review against this report.
4. Apply the P1 device-evidence and consistency cleanup next.
5. Run one future device-sensitive change through the revised instructions and
   compare owner interventions, regeneration count, expensive-gate time and
   review findings with this experiment.

The target is not zero human judgement. Device truth and product scope remain
owner decisions. The target is to ask for each decision once, preserve its
evidence, and ensure every later agent reads the answer from the repository
rather than reconstructing it from conversation history.
