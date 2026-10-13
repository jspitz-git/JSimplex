# MA-C: Markowitz upper substitution ownership contract

Date: 2026-10-13. MA-1 SOURCE/DESIGN ONLY. Baseline diagnostic
`5da5785ace8309f04981b375a23291b6576b8dac`, master
`6f68e24e8ddac42b948da8fcc2d636c010751194`.

## Decision and scope

Select exactly one kernel: the ordered upper-row multiply/subtract reduction in
`_backend_forward_solve!` for `MarkowitzBackend`, src/markowitz_factorization.jl
lines 509–516. Prepare a candidate for exactly BigFloat and Rational{BigInt}.
This accepts a bounded implementation investigation, not production deployment,
a numerical result, or a speedup. No production/test/environment changes or Julia
execution occurred in MA-C. MA-A is reused only as motivation: its private warmed
dot output borrowed the accumulator and is not a qualification of this solve.

The selected loop runs once per sparse pivot in each Markowitz forward solve.
It follows lower substitution and the dense-core solve; descending pivot order,
packed coefficient order, every multiply/subtract (including zero coefficients),
ordinary division, and final destination permutation must remain unchanged.
Transpose solve, lower scatter, dense LU, factor construction, pricing, DSE and
support omission are outside scope. Dense-core-only backends have no selected work.

Direct callers include factorization.jl (PFI forward), triangular_factorization.jl
(triangular forward), hypersparse_updates.jl (dense fallback), simplex_recovery.jl
(backend solve in recovery), and precompile.jl. Frequency is basis forward solve,
including setup, iteration and recovery, not one call per simplex iteration.
Existing markowitz_tests.jl covers four scalar types, mixed sparse/dense core,
permutations, copy/refactor and public solves; pinning it does not execute it here.

## Ownership and publication

`work[pivot] = rhs[row_order[pivot]]` copies scalar references. Factor packed
values, diagonal, RHS, previous destination entries and work entries can share
mutable BigFloat storage or numerator/denominator BigInts. Array ownership is
insufficient. Never mutate any of these scalars or use them as MA output buffers.

Use one lazily created, call-local accumulator plus `MA.buffer_for(MA.sub_mul,T,T,T)`
per eligible forward solve. Reuse this scratch across eligible upper rows only.
No backend fields, cache, global storage, pool, cross-call reuse or copied-factor
scratch sharing. The existing backend work vector already precludes concurrent
use of the same backend; this change must add no further shared state.
Separate backend copies and separate calls receive separate scratch.

For the first term, use `MA.buffered_operate_to!(buffer,acc,MA.sub_mul,seed,a,b)`:
read the original seed directly. Do not round/copy seed into ambient-precision
scratch before subtraction. Subsequent terms use buffered subtraction into acc.
Each row ends with the ORIGINAL ordinary `acc / diagonal[pivot]` and assignment.
That ordinary result has fresh BigFloat storage or fresh rational BigInt owners;
it must not alias acc/buffer. Retain this publication operation rather than
publishing scratch or adding a redundant output copy. Empty/single-term rows use
the original loop/division. Scratch never escapes to destination, work or factors.

Installed Base mpfr.jl creates a new BigFloat for binary multiply/subtract/divide.
Installed gmp.jl creates fresh BigInts for rational arithmetic; Base rational `/`
uses rational division. Prospective identity tests must verify the actual final
quotient route, including zero, unit divisor and exceptional divisor. Source
reasoning is not runtime qualification or proof of native memory release.

## Arithmetic and eligibility

BigFloat operations use the current ambient result precision, not maximum stored
input precision. MA product and accumulator must be created at that ambient
precision at the eligible solve's first row. Original mixed-precision operands
are passed without conversion. No FMA, compensated dot, reassociation, skipped
zero or changed precision/tolerance. The first-term rule avoids extra rounding
of a higher-precision seed before the first subtraction.

**Installed rounding mismatch:** MA 1.8.1 SaQfc uses `Base.MPFR.ROUNDING_MODE[]`;
installed Julia 1.13 uses `rounding_raw(BigFloat)`, which consults
`CURRENT_ROUNDING_MODE` first. Require equality of those raw modes before using
MA; otherwise use the whole original upper loop. Never change either rounding
state to qualify. Nested/scoped rounding is a required fallback regression.
No claim that MA-A exercised this mismatch. This is a newly read source fact.

For exact BigFloat/Rational{BigInt}, a row is eligible only with at least two
stored terms, finite seed, finite diagonal and finite coefficient/work operands.
Use a read-only row eligibility pass. Pass the diagonal vector and pivot index,
not an eagerly indexed diagonal scalar. Check diagonal bounds AND assignment
with nonthrowing predicates before reading it. Missing/unassigned diagonal
returns false; the original row arithmetic still precedes its final diagonal
lookup. Validate paired lengths and checked/assigned coefficient and work
positions before speculative reads; malformed rows fall back to the original loop
so its exception order remains authoritative. Do not eagerly throw from eligibility.
Short-circuit eligibility may stop at the first rejection. Other scalar types
and rounding mismatch retain the original arithmetic path. No global finite scan.

Rational finite inputs avoid MA's different treatment of denominator-zero values;
Base has explicit DivideError/nonfinite branches that must remain authoritative.
Finite rational products/subtractions are exact, with unbounded limb growth.
Zero diagonal is not excluded: retain original final division and exception.
For BigFloat, finite operands can still yield nonfinite intermediates; separate
MPFR multiplication/subtraction must match original behavior, including signed
zero, underflow, overflow and flags. Admission tests must reject the candidate if
this is not demonstrated. Unsupported contracts retain the original route.

No user callback or custom scalar arithmetic occurs in this packed Vector kernel.
Eligibility reads ahead within a row but publishes no values. On arithmetic or
index exception, the current work entry and destination publication boundary must
match the original; earlier completed rows stay completed. Allocation-failure
timing cannot be identical for an allocation optimization and is not promised.
Do not catch arithmetic exceptions and retry after partial mutation.

## Work and memory ledger

Let S be sparse pivots, K the total stored upper terms, E eligible rows and Ke their
terms. Baseline selected arithmetic is K multiplies, K subtracts and S divisions.
Candidate keeps these counts and order. For exact target types it adds at most
one read-only eligibility traversal of each considered row (O(K)), at most two
operand finiteness checks per term plus seed/diagonal checks per considered row,
paired-size/bounds checks and one rounding-mode comparison per BigFloat solve.
Rejected rows pay the scanned prefix plus original arithmetic. No extra basis
solve, matrix conversion, vector copy, sorting, dimension scan or support cache.
Hardware Float32/64 must retain the old loop without eligibility passes or scratch.

Lazy scratch is created at most once per solve and only after an eligible row.
BigFloat has two mutable scalar buffers. Rational buffer composition is product
scratch (two rationals + one BigInt), product rational, subtraction scratch
(three BigInts), plus accumulator rational: twelve BigInt leaves total, all
pairwise private and disjoint from input owners. Limb capacity can grow with the
largest intermediate within a solve; there is no constant byte bound or native
free proof. End of call releases Julia roots, not a promise of immediate GC/free.
Ordinary division still allocates an independent output per row. No new retained
backend storage. No seed-copy scan or extra output-copy cost is hidden.

These checks and per-solve allocations may outweigh saved temporaries, especially
with short rows. They are correctness costs to measure, not grounds to weaken
ownership/exception guarantees. No unnecessary production work or memory is
introduced in this source-only milestone. The candidate's extra eligibility pass
and scratch cost are explicit prospective costs, not accepted performance.

## Next step and evidence

Follow `docs/superpowers/plans/2026-10-13-ma-markowitz-upper-preparation.md`:
MA-D prepares an unexecuted candidate, named regressions, exact fixtures and
bounded cost schedule. No equivalent inventory milestone is needed. Candidate
qualification requires concrete launch bindings and independent admission under
the user's standing short-run authorization. No automatic launch from this report.

MA-C source-evidence.json contains fresh read-time hashes, not retroactive MA-A
launch pins. Initial exploration also read another installed MA tree xwKH0;
all conclusions above were checked against SaQfc 1.8.1, the MA-A-bound installation.
Two guessed source filenames/pin glob were absent; subsequent reads used actual
paths. No parser, old auditor or numerical rerun was involved.

Current S4-AD continuation bindings map only to MA-C/STATUS.md.before-MA-C and
MA-C/roadmap.md.before-MA-C at exact hashes; all older maps and evidence remain.
Fresh host preflight checked all44 groups AND sessions, boot and process identity;
no Julia or matching group/session remained. User settings and environments are
hash-preserved. Automation paused, CI off, HH reuse disabled, broader plan open.
