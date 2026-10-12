# S6-AA: reliable zero-budget exchange test repair

Separate permanent test-only subplan, conditional on accepted S6-Z qualification
and fresh review. Execute inline; fresh independent final numerical/work review.
No production, options, tolerance, precision or workflow changes.

## Scope

S6-Z qualifies identity6 Float32 exchange across four managers,29/29,23gates621pins.
It preserves the narrow reliable-zero-budget contract. Both structural feasible
sets are the same singleton (old det31071); equations, activities, sparsity and
cancellation behavior differ.
Only target `Reliable artificial exchanges need no reconstruction recovery` may
select the new helper. Existing `artificial_exchange_roundoff_fixture` and all
neighboring testsets stay byte-identical. No claim that all eight historical CI
failures are repaired; first four scalar-unknown accepted=false cases remain open.

1. Verify current refs/source/user hashes and separate host absence. Save original
   helper/target/neighbors for byte comparisons. Structural pre-solve RED: require
   the target call to a new exact identity helper and require its matrix construction;
   the old source must fail those requirements before any workspace/exchange/solve.
   Label this structural RED, not reproduction of numerical failure. Preserve output.
2. Add a small helper using the exact S6-Z construction and existing options/policy,
   basis/states/map/maintained point. Choose a distinct test-local name, e.g.
   `reliable_artificial_exchange_fixture`; avoid factoring/reformatting native helper.
   Change only the target's helper call, retain original four assertions, diagnostics,
   max_refinements0 and manager loop. Brief comment explains exact reconstruction and
   separate native recovery coverage. No diagnostic snapshots/counters beyond the
   preexisting SimplexDiagnostics, adapters, extra permanent solves or iterations.
3. GREEN runs actual changed target and selected native neighbor `Artificial exchange
   recovery preserves cancellation and policy limits` on the changed test source.
   This bounded integration gate (four target+sixteen neighbor exchanges) verifies
   helper isolation and shared namespace; no full-file or old census replay. Also
   assert source separation/unchanged globals, exact helper construction and unchanged
   native helper/neighbor/original oracle bytes except intended target name. Preserve
   failures without weakening cancellation, exact work assertions or tolerances.
4. Audit process/exit/actual source/pins/input/policy, raw/portable equality and main
   user hashes. Fresh independent review numerical intent and work/memory: no
   production cost, small cold fixture setup only, no benchmark/speedup claim. If
   accepted, commit only changed test, integrate into current master preserving dirt,
   guarded actual-master target+structural gate, verify source identity and pin/user
   hashes, then authorized push and remote-ref verification. Keep diagnostic evidence
   on its own branch. CI remains disabled. Update STATUS and next plan.

Single numerical Julia/BLAS1,heap2GiB,VM8GiB,minRAM6GiB,maxswap1GiB. Separate fresh
host identity/absence call before every launch or pinned edit; no pinned edits during
runs. No big/largo/AnyMOD/aliases. Preserve user files, raw attempts, old worktrees
and environments. Accepted S6-X/Y/Z and older corpus/reference/cost must not rerun;
do not execute old qualification driver after changing the test. Broader S6 and
actual x64/fullsuite success remain open.

## Completion

S6-AA completed: structural RED2expectedfailures/zero exchanges; GREEN127/127;
master19/19 and18audit gates621pins. Fresh independent review no findings.
Testf2e7647 -> master74f7835; push completed. Source/raw/pins/user hashes verified.
See S6-RELIABLE-EXCHANGE-FIXTURE.md and REVIEW. Broader validation remains open;
next separate S6-AB phase-reconstruction-boundary-qualification preflight.
