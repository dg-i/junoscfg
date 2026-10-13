## Resolved instructions
instruction-integrity.md records owner approval of the completed experiment's
production recommendation and master push. Regular phases and native gates apply.
## Requirements
Existing schema-pipeline/verification-evidence and the adjacent delta; preserve
consumer/CLI behaviour, existing workflow/version selection exceptions and coverage.
## Evidence
Experiment branch f277c896582ccfb94787a02ff06fae4f896f236f; measured code
7c25be1885025a30713b66bfdc3a1b0824631858. Nine full observations and 23 controls
support the design. Starting master 507a3dc74248ce2d670f6a5e27023d34990e6965.
Native engine owns evidence; application owns truthful complete reports/selection.
## Non-goals
No product syntax/schema artifacts, lowered assertions/floors, arbitrary receipt
import or phase bypass. No false claim that 45 seconds was achieved.
## Acceptance criteria
Delta test identities; negative worker/coverage/selection/engine controls;
independent Test/Challenge and fresh review of native engine and application;
complete native checkpoint and measured production timings with cache conditions.
## Performance expectations
Cold <=400 seconds and warm <=200 on the experiment machine; no-schema target
45 seconds remains an explicitly measured gap if production cannot safely meet it.
Baselines: cold565.161, matched warm serial241.295, no-schema245.391 seconds.
## Outstanding decisions
None: owner approved adoption and pushing master; concrete implementation choices
must preserve these existing promises and conservative unknown handling.
## Execution and checkpoint
- Assurance preference: economy.
- Risk floor: high, verification trust boundary.
- Roles required: Builder, independent Test/Challenge, fresh Reviewer, Finalizer.
- Resume point: phase 4 after committed freeze and design.
## Delta log
- Initial freeze based on approved experiment; production cannot adopt its waiver.
## Scope and completion
One application outcome with required upstream engine dependency. Review and merge
upstream dependency before installing its immutable commit; finalize, archive,
version and push the application only after checks and independent review pass.
