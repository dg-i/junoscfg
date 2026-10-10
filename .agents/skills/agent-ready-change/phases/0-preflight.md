# Phase 0 — Instruction integrity

## Outcome

`openspec/changes/<slug>/instruction-integrity.md` records the complete effective
instruction stack, every conflict and its effect, the owner's assurance
preference, and one consolidated set of material unresolved questions. Phase 1
does not start while one of those questions is open.

## Process

1. Create or switch to the dedicated change branch, require a clean governed
   tree, and create the OpenSpec change folder. Do not draft the proposal yet.
2. Inventory the effective stack in actual precedence order: immutable platform
   constraints; system, developer, runtime and provider configuration; invoked
   skills; repository and every applicable nested `AGENTS.md`; owner
   instructions; approved specifications and decisions; acceptance and contract
   tests; and observed existing behaviour. Record unavailable sources and
   capabilities rather than assuming them.
3. For each contradiction, incorrect scope, unclear precedence, unavailable
   capability, or likely-defective higher-priority instruction, record the two
   sources, their scopes and priorities, the effective instruction, and its
   practical effect. Obey effective precedence. Precedence decides what can be
   done; it does not prove the winning instruction correct.
4. Classify each conflict exactly once as `automatically resolved by
   precedence`, `owner decision required`, `repository/skill correction`,
   `runtime/operator correction`, `immutable platform constraint`, or
   `specification/test disagreement`. Record the safe action and the correction
   owner. Never edit a higher-priority source from a lower-priority layer.
5. Ask the owner once, in one numbered batch, only for material unresolved
   decisions. Include evidence, effect, and the safe default for each. Continue
   automatically when there are none; do not relay phase transitions.
6. Have the owner confirm `economy`, `balanced`, or `maximum-assurance` and put
   that exact value in `.openspec.yaml` as `assurance`. The preference can add
   assurance but cannot waive a mandatory risk control or an immutable gate.
7. Commit the completed preflight before phase 1. The phase-1 fields gate reads
   it together with the proposal; do not weaken that gate to make an unfinished
   proposal pass early.

## Delta rule

Any later instruction or evidence is compared with this record and the phase-2
evidence freeze before affected work continues. Record what changed, which
conflicts and criteria it changes, and which completed work is invalidated. A
material unresolved delta produces the one owner batch; an immaterial or
precedence-resolved delta is recorded and work resumes automatically.
