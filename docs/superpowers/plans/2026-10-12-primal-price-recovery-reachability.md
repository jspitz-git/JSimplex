# S6-U: repeated primal price recovery reachability

> Use superpowers:executing-plans and systematic-debugging. Diagnostic-only until
> a concrete cause is demonstrated and a separate RED/GREEN repair plan exists.

S6-A stores twelve CI failures per run at legacy_primal_direction_price_tests.jl
214–216: result NUMERICAL_ERROR and exactly one corrected-price/correction-attempt
assertions in "A repeated price disagreement cannot renew the recovery budget".
Four Float64 manager cases use native_price_roundoff_fixture and an existing
publication observer that sets reduced_costs[7]=-1.0. Accepted historical local
S2 focused suite included this file; do not repeat it or declare the CI cause known.

1. Reconcile original fixture/helpers, exact historical assertions/evaluated values,
   previous diagnostic coverage and current source. Read all relevant price-quality,
   correction, direction consistency, ratio, retry, publication and budget paths.
   Stored CI map is only an aggregation, not a new numerical reproduction.
2. Identify the missing causal observation before any numerical run. Prepare a
   bounded current-source census of the four existing manager cases, preserving
   the original oracle and existing fault injection. Record selected owned state,
   attempted recovery, budget and publication ordering, returned status and source/
   options/policy. Any additional observer must be read-only, handle non-workspace
   states, and never add solves/certificates/refactors in callbacks. Distinguish
   current observed paths from hidden original/CI arithmetic and observer neutrality.
3. Audit exact original assertions, result publication, work counts and process/
   pins/source. A local pass does not establish x64 cause. If a counterfactual is
   needed, first specify the narrowly controlled boundary and preserve public
   integration coverage. Do not repeat rejected S6-J's uncontrolled downstream
   refactor strategy or weaken zero/exact-one work assertions.
4. Fresh independent numerical/work/memory review. Preserve failures, decisions,
   raw controls and qualified scope. A repair requires a separate RED/GREEN plan.

Do not repeat accepted N/O/P/Q/R/S/T/reference/corpus/cost runs or old local full
file. No tolerance/precision/safeguard changes, certificate transfers or CI enablement.
No fullsuite/x64/speedup claim. Single guarded Julia/BLAS1,heap2GiB,VM8GiB,
minRAM6GiB,maxswap1GiB. Fresh separate boot/start_ticks/command process absence
before edits/launch. Preserve old worktrees/environment/user changes.

## Preflight observation contract

The old log establishes zero publication/correction events, not the actual returned
status or the private BTRAN residual. The existing local S2 full file is accepted
and is not rerun. This census executes only the original target testset once (four
managers), retaining its five assertions and its sole reduced_costs[7] injection.
Additional owned snapshots are taken before callbacks and after that injection,
and around the iteration. Kernel diagnostics are enabled to count actual calls;
this is an observed current-source run, not an observer-neutrality comparison.
Snapshots never solve, refactor, certify, or mutate the workspace. Private fresh
BTRAN candidates and the local price_recovery_attempted variable are not exposed
by events; event ordering and source control flow give bounded inferences only.
Exact offline residuals use the captured matrix/basis/costs, not extra live solves.
A zero/absent correction event alone does not identify which prerequisite failed.

## Result

Four unchanged cases passed 20/20 original assertions; exit0, 47 audit gates,
615 unchanged pins. See S6-PRIMAL-PRICE-REACHABILITY.md. Private BTRAN/CI cause
and observer neutrality remain unproved. Independent final review pending.
