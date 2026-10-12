# S6-Q independent final review

Fresh gpt-6-astra/high, one read-only review of513d111..44441195dcfa1e65f3a243d72b81e898283701e3.
No edits, Julia execution, artifact-writing audit, Git mutation or CI changes.

## Verdict and deferred minor

No Critical or Important findings; accepted for the fixed Float64 diagnostic scope.

Minor (deferred): nearly_singular_point_audit.py:33–35 reverses the general column
scaling convention. Production unscale_primal DIVIDES by column factors; original
matrix reconstruction MULTIPLIES by them. The auditor does the opposite. ALL
captured factors equal exactly1, so no S6-Q result is affected. Before any reuse,
correct those expressions or explicitly restrict the auditor to unit column
scaling. Preserve accepted artifacts; no Julia rerun is needed. This auditor is
NOT accepted as a general nonunit-scaling validator. Future S6-R must not reuse it
as such. No edit/rerun/re-review loop for this nonblocking scope limitation.

## Independent evidence

- All611 current pin hashes/resolved paths/inventory membership and517preflight
  entries match accepted S6-N. Raw/portable report/log/process/pins and copied/
  current driver are identical.
- Exact Python arithmetic using PRODUCTION scaling convention independently
  reproduces all11recorded row values/equation residuals.
- Event6 first equation residual125/2^66 in both rows; event11 first original-bound
  violation2^-47,scaled residual2^-27,objective gap-1/16. Report does not overclaim.
- Source confirms event10 is after refactor and before FTRAN/BTRAN. Certification
  precedes checks. Staged-trial versus final-workspace distinction is correct.
- Derived primal RHS[-2^20,2^20] follows states/bounds; staged workspace cannot use
  legacy preserved-bound-value exception. Final scratch RHS[0,-1] is BTRAN costs.
- Exact final endpoint matches saved S6-N;exit0 and5/5assertions recorded. Prior
  runner386534/child386535/driver386526 separately absent on recorded boot.

## Computational work and memory

No unnecessary production work or retention: only diagnostics/evidence/plans change.
Observer owns Float64 arrays/immutable bound values and retains no workspace/factor
references. No extra solves/refactors/certificates. Per-event copying scales with
nonzeros, workspace dimensions and retained eta entries; eleven tiny snapshots
under512event cap are reasonable here. Exact conversion/reconstruction is postsolve.
No measured allocation total or performance gain; no benchmark warranted.
Proposed S6-R appropriately separates fresh versus copy/refactor lifecycle without
claiming hidden-factor equivalence.

## Executor rulings on declined scope

1. Arithmetic operation/backend cause remains unknown; keep conclusions to observed
   state interval. Cost: another bounded component diagnostic before repair.
2. UMFPACK permutations/internal scaling/factors/refinement were not captured;
   inspect supported metadata contract in S6-R before any inference. Cost: no
   claim about hidden recorded-runtime factors.
3. Observer neutrality/hidden-trajectory equality not proved by endpoint equality.
   Cost: acceptance covers this trace and saved final state only.
4. Scratch buffers do not certify a runtime dual witness. Cost: witness provenance
   remains incomplete; never transfer or invent certificates.
5. General models/dimensions/precisions/nonunit scaling are outside this accepted
   trace. Cost: new qualification required before general reuse; minor above stays
   explicit, not a silent general-purpose correctness claim.
6. Production repair, strict-test/full-suite success, historicalx64 equivalence and
   performance gains remain unproved. Cost: original equality/S6 stay open and CI
   remains disabled; no production/test changes integrated.
7. S6-R outcomes remain future work. Cost: separate guarded experiment/audit/review
   required; its plan is not evidence of a successful component replay.
