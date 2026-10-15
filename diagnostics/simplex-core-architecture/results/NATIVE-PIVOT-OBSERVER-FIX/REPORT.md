# Offline correction of sparse diagnostic token capture

Separate UNEXECUTED test-support-fixed.jl introduces one dense_tokens(format,
values::AbstractVector) helper: allocate Vector{String}(length(values)), enumerate
logical elements in order, format each scalar and assign into dense output.
It never broadcasts strings into sparse storage. Only four original expressions
change: observed solve output/RHS and exact-equation RHS/output. The numerical
input arrays, solver calls, exception behavior and observer counters stay intact.
The observer still catches diagnostic failures as well as numerical failures;
exception labels alone are not backend-throw evidence.

The old failed GREEN is reused as the observed failure: forward_solve returned a
dense output before scalar.(sparse RHS) threw zero(::String). Its audit remains
FALSE,5352passes/1error/1506unfulfilled, and its only attempt stays CONSUMED.
No old script or Julia was rerun. The new source inverse removes one helper and
reverses four expressions to recover the whole original support file exactly.
The separate driver changes only four include routes: support local, three frozen
original test files explicitly at the qualification sibling. Whole inverse exact.
No candidate production source or original test predicate changes.

## Regression coverage, unexecuted

regression.jl was written before the helper. It defines a callable regression
against the actual supplied helper/scalar/token functions, without factor/solver
calls or mocked numerical results. Twelve cases: dense/sparse Float64 special
bits, implicit and explicit zeros, signed zero, subnormal, infinities, NaN payload;
all-zero sparse and empty dense; dense/sparse Float32, BigFloat128, Rational{Int64}
and Rational{BigInt}. Checks require dense String vectors, exact expected tokens,
TOML round-trip, detached token storage, unchanged input values/representation and
mutable scalar owners. Precision/rounding restoration is checked. The original
sparse broadcast has one explicit expected MethodError discriminator.

Prospective119assertions=12*9+4*2+1negative+2ambient. Sixteen helper calls,
one deliberately failing old-expression call, zero factor/native/solver calls.
The119 are separate from frozen6858candidate/neighbor assertions; neither is
claimed executed. Regression fixture/snapshot/TOML allocations are cold diagnostic
work. Original792selected entries and324equations must not be reduced to partial
observed counts. No new test is silently inserted into the current frozen driver.
A later concrete admission must wire and count regression execution explicitly.

## Other tokenization sites

Remaining support broadcasts use active/spare UMFPACK control Vector{Float64} and
CSC nzval Vector{Float64}; their concrete dense storage is source-bound. Frozen
cost driver broadcasts use dense control/info arrays, allocated dense output
vectors, dense info matrix columns, CSC nzval and dense parsed RHS arrays; owner
IDs are constructed as a dense vector. They do not use the broken NP observer.
These known-dense sites stay unchanged. This is a bounded inventory of these two
drivers, not a claim about every repository broadcast.

## Work and memory

No new production work, allocation, retained memory, factor solve, scan or
precision change. Within diagnostic observation each affected vector now gets
one dense String container and n scalar conversions, retaining strings rather
than numeric owners. There is no intermediate dense numeric copy. Dense access
is O(n); generic sparse iteration may use binary-search getindex, giving up to
O(n log(1+nnz)) access overhead plus scalar formatting; absent mutable scalar zeros
can allocate. This is disclosed cold diagnostic overhead on tiny test vectors,
not an allocation/speedup claim or a new hot-path optimization. All logical token
values are required by the existing complete-output schema. A specialized sparse
cursor is unnecessary scope expansion for this bounded correctness repair.
No measured benefit, zero-allocation claim or runtime acceptance is established.

## Next admission

Preparation only. NO Julia/query/parser/import/compile/numerics, new stage,
reservation, launcher execution, production/test/env/CI/master/direct change.
The offline helper/driver/regression must receive independent review before any
newly labelled GREEN-2 preparation. That future admission must bind a new output,
stage, exact driver/support/regression and audit routing, unchanged candidate75
source, original6858/792/324 plus separately counted119regressions, and a short
explicit cap. It must retain the failed GREEN and accepted RED as separate inputs.
Frozen control/seal/launch scripts target the consumed green path and MUST NOT be
rerun or overwritten. Cost cannot bypass the failed old predecessor. This turn
creates no numerical allowance or executable replacement launch arrangement.
Standing human short-run permission is retained, with no repeated permission ask;
concrete stage review is still mandatory. Broader plan OPEN, CIoff, HHreuse disabled,
automation paused, master6f68e24 unchanged, all historical rejections preserved.
