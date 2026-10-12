# S6-C: fresh-pricing refresh fixture

Status: independently reviewed, integrated and pushed as master a465da5.
Only test/legacy_primal_preference_work_tests.jl changes. Production is unchanged
from mastere7014fb; no solver tolerance, bound-handling rule or certificate changes.

## Cause and limited correction

The old fixture has A[1,1]=1e-14 and entering upper bound1. Its step to that bound
fits the existing row feasibility tolerance, so _primal_ratio accepts the finite
Harris bound step and _primal_iteration! returns nothing after one successful flip.
The intended stale candidate/refactorization/exhaustion path never executes.
S6-B oracle-1 reproduces2pass/2fail/1error on current master and preserves the
original oracle. This is a fixture reachability defect, not evidence that the
solver should reject that tolerated step.

The synthetic bound is now1e8; its row movement1e-6 exceeds the existing tolerance.
An explicit assertion makes this precondition visible. Existing NUMERICAL_ERROR,
one-refactor/zero-iteration, unchanged-basis and cleared-exclusion requirements
remain; terminal access is guarded so a wrong nothing result reports a failed
assertion rather than hiding the rest behind FieldError. No numerical guard is
relaxed, and this test parameter change is not a performance comparison.

## Evidence

Diagnostic fixture-1 changes only that literal before evaluating the original
five assertions:5/5pass,exit0,12audit gates/pins independently verified. Diagnostic
control/observed selected-state values agree exactly. One refactor_residual event,
no flip_completed,NUMERICAL_ERROR,iterations0,refactors1,basis[3,4,5],emptyexclusions.
This proves the intended refresh path is reachable, not every possible recovery
budget behavior or platform combination. Point/original feasibility checks remain
true for the nonterminal retained point; no optimality claim follows.

Focused-1 failed10pass/2fail because the new precondition was accidentally inserted
in the unrelated first testset. Raw test source, log and pin audit are preserved;
later testsets did not run. The corrected edit was rebuilt from unchanged main test
source and checked to leave both neighboring testsets byte-identical.
Focused-2 covers the entire three-testset file; its final audited outcome is recorded
below. Historical CI/full suite remains failing; CI stays disabled.

## Work and memory

No production code diff: no additional setup/iteration/candidate/recovery work,
allocation or retained memory. One test-only scalar precondition and changed small
synthetic bound require no production cost benchmark. Old reference timings are
not repeated. User environments and earlier failed attempts remain intact.

Focused-2 passed20/20 (10+6+4),exit0,all10audit gates, independent pins/source and
zero production diff against mastere7014fb. Runner370589/child370590/driver370580
separately absent,noJulia,same boot. Fresh independent review accepts with no findings; see S6-FIXTURE-REVIEW.md.

Integration: test commit3e91736 -> mastera465da5dc85553703a5330e8766020b1261a6a2e,
pushed and remote verified. Master-1 passes20/20,exit0,all11audit gates including
independent pins/source and preservation of main user files. No production diff
against e7014fb. Separate host check confirms runner371705/child371706/driver371697
absent, no Julia, boot20de7dde-704e-41c8-bee7-b8511c0a86b0. This is one corrected
test family; other historical CI failures remain unresolved and CI stays disabled.
