# S6-A: historical CI failure inventory

Status: existing logs audited; preference oracle reproduced on current master.
Mastere7014fb includes accepted S5-C, not a full-suite repair. CI remains
`disabled_manually`; Extended validation is a separate workflow and was not run.

## Historical evidence

- [Latest failed diagnostic branch run](https://github.com/jspitz-git/JSimplex/actions/runs/38149970679),
  source4914cbb:329511passed/197failed/1error/0broken,329709total,266m43.7s.
- [Last failed master run](https://github.com/jspitz-git/JSimplex/actions/runs/38142752357),
  sourceb720674:329508passed/200failed/1error/0broken,329709total,261m08.2s.

Both completed assertions and emitted final test summaries; these are not clean
timeouts or runner setup failures. Julia1.13.1 x64 on Ubuntu24.04, coverage=true,
check-bounds=yes. Local accepted work uses Julia1.13.0 aarch64 with preserved local
environment; it does not reproduce the CI environment. Source/test content is
identical between both failed refs. The three differing results therefore cannot
be attributed to a source change between those runs; cause remains unknown.

| Test file | Latest failed assertions / errors | Old master | Current evidence and limitation |
| --- | --- | --- | --- |
| legacy_primal_direction_price_tests.jl |12/0|12/0|S2 focused suite included this file and passed on local runtime; do not repeat that accepted reference or call CI fixed. Four manager cases fail at214–216 in CI.|
| legacy_primal_preference_work_tests.jl |2/1|2/1|Known prior local failure in diagnostics/refactor-safety/results/preliminary-baseline-preference.log. No accepted current-source reproduction; first bounded target.|
| dual_pivot_consistency_tests.jl |48/0|48/0|Recovery/cancellation assertions61,63,66,68,69,103; cause unknown.|
| native_phase_transfer_tests.jl |8/0|8/0|Reconstruction work assertions164,211; not a demonstrated certificate regression.|
| native_artificial_row_tests.jl |96/0|96/0|Budget/cancellation/publication assertions65,66,68,70,71; cause unknown.|
| solver_tests.jl |1/0|1/0|Nearly singular bounded model assertion552; unresolved numerical outcome.|
| bigfloat_integrity_tests.jl |30/0|30/0|Cross-precision supplied tolerance assertion282, NUMERICAL_ERROR vs INFEASIBLE; cause unknown.|
| primal_perturbation_integration_tests.jl |0/0|3/0|Assertions187–189 differ with identical CI source. Local S5-C focused suite passes this file; does not prove CI/order/runtime cause resolved.|

All listed test files are unchanged from both failed refs to current source.
Production changes since failed master are confined to HH factorization and
perturbation cost-copy handling; new restoration test/runtests registration also
exist. Neither fact proves unrelated failures fixed. Existing local semantic
passes and interrupted full-suite attempts remain separate evidence. No failure
category is silently dropped because a later focused subset passes.

## Exact inventory audit

results/S6-A/ci-inventory-1.json records each failure/error with log line, test
line, expression/evaluated text, per-file counts, Git revisions, job metadata,
raw SHA256 manifest and five checked gates. Counts sum exactly to both final
summaries. Full unmodified downloaded logs are preserved under
.superpowers/simplex-core-architecture/S6-A/ci-inventory-1; compact extracts and
metadata are committed. API collection did not enable or execute any workflow.
No production work, allocations or retained memory are added by this inventory.

## Next bounded reproduction

2026-10-12-pricing-refresh-reproduction.md selects only the existing failing
preference testset and reports actual terminal/events/work/state on current
source. Hypothesis: its corrupted factor fixture may now take a valid alternative
path, so the expected NUMERICAL_ERROR is not reached. This is unproven; no oracle
or solver change is justified until the observed path and feasibility are checked.
Other failure families, the test.mps case, external100combinations and current
master full-medium validation remain open. S6 is not passed.

## S6-B bounded reproduction on mastere7014fb

oracle-1 executes the exact existing selected testset without diagnostic AST edits:
2passed/2failed/1error,exit1, all10audit gates and independent pins/source pass.
The failure reproduces the old local/CI outcome: terminal is nothing (so accessing
status errors),refactorizations0 instead of1,iterations1 instead of0. This is
failure evidence, not a successful suite. No solver/test tolerance was changed.

The independently audited preference-3 twin observations show the same selected
state with and without the observer: primal[1]=1, unchanged basis[3,4,5], prices
[-2,1,0,0,0],1iteration,0refactors, original feasibility and point certification
true. Observed sequence:refactor_initial,pricing,pivot_proposed,flip_completed.
Post-iteration FTRAN column1 residual0 is a single-column probe, not proof of
whole-factor consistency; the fixture deliberately corrupts its factor first.
No terminal certificate or optimum is claimed from a returned iteration.

Source explanation: primal_simplex.jl::_primal_ratio permits a finite entering-bound
Harris step when the small limiting pivot is below zero_tolerance and the predicted
step obeys the existing per-bound tolerance. Here coefficient1e-14 times upper1
is inside that tolerance, so the fixture can flip before the intended deferred
candidate/refresh path. Its description/expected work does not match this observed
path. This does not prove the separate refresh-budget behavior correct.

Raw diagnostic failures preserved:preference-1 used nonexistent matrix field;
preference-2 tried replacing a concretely typed diagnostic context after workspace
construction;preference-3 completed twins but accidentally shared/modified AST
nodes with its subsequent oracle (UndefVarError). Only twin observations from3
are qualified; oracle-1 is the separate clean original-oracle evidence. The reusable
driver now deep-copies AST for future use; no successful rerun of that revised
combined driver is claimed. Completed twins were not repeated for that fix.
Separate host check370101/370104/370089 absent,no Julia,same recorded boot.

Next subplan qualifies a fixture whose finite bound cannot take the tolerated flip
shortcut, before any test correction. Source production remains unchanged.
