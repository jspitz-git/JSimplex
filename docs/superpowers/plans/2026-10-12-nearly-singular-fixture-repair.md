# S6-T: preserve the no-recession test with a dyadic row-balanced fixture

> Use superpowers:executing-plans inline. Separate test-only RED/GREEN plan after
> acceptance of S6-S. Do not change production or numerical options/safeguards.

## Contract

Replace only the construction in "A nearly singular bounded model has no recession
ray" in test/solver_tests.jl with S6-S's exactly Float32 representable matrix and
bounds. Preserve all original assertions/public @inferred solve/four scalar types.
Keep exact objective equality, no isapprox/permissive new status list. This is a
new feasible set preserving the regression intent, not an equivalent matrix or
solver fix. Original cancellation stress/failure stays in S6-N evidence.

s=2^-21,d=2^-44,delta=2^-23,A=[s s;s-d s+d],rowbounds±[1,1+delta].
Four nonzeros,det2^-64,conditioninf2^24+1,strict unique objective-2^44,
x=[-2^44-2^21,2^44]. No recession since A is invertible and both rows bounded.
S6-S four-type qualification and separate factor metadata support local native
path; visible phase I/II and2/2/4 topology are unchanged. No actualx64 proof.

## Tasks and gates

1. Reconcile accepted S6-S report/review, precise source and user hashes, actual
   refs and fresh host absence. Do not rerun its drivers or old N/O/P/Q/R.
2. Add focused structural test contract before any solve in the existing testset:
   exact rational determinant, equal positive row sums, original2x2/fournonzero
   matrix and symmetric proposed row bounds. Assert intended strict optimum with
   exact matrix-vector multiplication. Avoid coupling the permanent regression to
   internal factors/ordering. Scope structural proof once outside scalar loop.
   RED on old constructor must fail a stated structural condition before solving;
   use a focused extracted pre-solve prefix so no old public census is repeated.
3. Apply only planned constructor/bounds and explanatory comment. GREEN runs the
   exact permanent testset with structural conditions and all existing assertions.
   Assert source diff contains only this testset and no removed original assertion.
4. New-source focused regression includes the adjacent no-ray/original-certificate
   cases whose declarations/dependencies are first inspected. Document selected
   testsets and counts before launch; do not rerun unrelated accepted corpus or
   silently call this a full suite. Historical other families remain open.
5. Guard/process/independent pins/source/input audit; fresh independent final
   numerical/work review. No production work/memory change; cold tiny test-only
   rational construction has bounded cost. No performance benchmark warranted.
6. If accepted, commit test-only change, integrate to master under standing
   authorization preserving main/user/env files. One focused actual-master check
   of affected testset, source/pins audit and separate absence; push both authorized
   refs and verify remote refs. CI remains disabled; never claim x64/full-suite pass.

If structural RED fails for a harness error, preserve it and correct the harness;
if GREEN changes route or numerical result, diagnose without weakening assertions.
A permanent test edit needs its own review; S6-S acceptance alone does not merge it.
Single Julia/BLAS1,heap2GiB,VM8GiB,minRAM6GiB,maxswap1GiB,existing guard. No forbidden
big/largo/AnyMOD or aliases. Before edits/launch check prior389862/389863/389852
identities/absence on fresh boot; preserve raw failures, old worktrees and user dirt.
