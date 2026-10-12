# S6-AF source preflight

Base9129d61/master3c0af5c; 517 shared source/test/runtime/environment pins match AE.
AE immutable input/report hashes captured. Float64, native policy, hypersparse=false.

SimplexWorkspace is parametrized by factor; construct a new workspace from original
fields after real setup, replacing only factorization. _new_candidate_workspace
(simplex_pivot.jl:45) shares the exact wrapper and inner; stage values/scratch copy
vectors separately. Discard retains max refactor count; no factor-copy path without
pending update. Unexpected copy/update will count then fail fast.

Pipeline basis solve (hypersparse_pipeline.jl:448) invalidates destination once.
Unit metadata is forwarded to inner _unit_transpose_rhs; triangular _UnitTransposeRHS
and PFI vector fallback must remain unchanged. Prepared and ordinary FTRAN dispatch
remain separate. Native correction (legacy_dual_correction.jl:129) directly calls
transpose_solve!, so has no outer invalidation. Underlying triangular solves also
invalidate internally; those are not outer-wrapper entry counts.

| Subject path | Prepared FTRAN | Ordinary FTRAN | Unit BTRAN | Correction BTRAN | Cost BTRAN | Outer invalidation | Unit metadata | Refactor |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Four nonrefresh modes |2|0|2|1|0|4|2|0|
| After refresh |2|1|2|1|1|6|2|1|

Both unit BTRANs forward real e2 and must return AE rho before declaring badrho.
Prepared duplicate returns e1. Correction input/output exactly AE vectors. Refactor
forwards actual B without resetting hits. Primal recompute RHS=-B[:,2], output=-e2;
zero-cost BTRAN output0. Refactor event precedes recomputation, native refinement=false
so cancellation flag still permits those two solves. Complete attempt counts occur
before dispatch/classification; successful output ledgers are separate. Throws from
existing observers exercise provenance, not throwing-backend accounting.

Four new unwrapped controls: source dual_simplex.jl:1234 requires one ordinary
refactor after no eligible column before certification, followed by second unit
BTRAN. Predicted whole kernels FTRAN1/BTRAN3/refactor1; INFEASIBLE, no pivot/rejection.
This is expected control work, not a subject budget relaxation. No old fixture runs.

Observers own copied values only; existing stop-flag/throw behavior retained. Setup
counts recorded separately and removed from iteration kernel deltas. No postcall
certificate or basis solve. All original 108 failing-group assertion predicates are retained in matching modes.
Exception results from the single actual public call are rethrown into the original
@test_throws type oracle without a second solve. Refresh uses the original five-field
tuple under before_refresh; nonrefresh uses seven-field before. The untouched test
file preserves all216assertions, including the other108native assertions.
Static extra-unit budget check requires rejection without another numerical call.
