# MA-D: prepare one private Markowitz upper-reduction candidate

**Goal:** Prepare a concrete, unexecuted MA candidate and qualification package for
one upper-substitution kernel; do not modify production or launch Julia in MA-D.
**Architecture:** one call-local lazy accumulator/buffer, reused across eligible
upper rows of Markowitz forward solve; original ordinary division publishes each
independent result. All fallback, arithmetic order and ownership rules in the
[MA-C contract](../../../diagnostics/simplex-core-architecture/MA-MARKOWITZ-UPPER-CONTRACT.md)
are binding. **Tech stack:** Julia 1.13, MutableArithmetics 1.8.1, existing Test and
Python offline source/fixture checks. **Spec:** MA-1–MA-4 in the architecture roadmap.

## Global constraints

MA-D is offline source/test preparation. Do not execute Julia, imports, parsers,
compilation, Pkg resolution or numerics. Preserve src/test/Project/user manifests,
all prior artifacts and stopped routes. No new public API or backend field. No
matrix solve trajectory, tolerance, pivot rule, support omission or precision
change. No MA macro rewriting or generic dot substitution. MA-C selected only
forward upper reduction; transpose/lower/core paths remain byte-equivalent.

## 1. Candidate interface and exact inverse

Read MA-C, current source and dependency implementations; preserve fresh refs,
full44 groups AND sessions/noJulia and current continuation bytes before edits.
Create `diagnostics/simplex-core-architecture/results/MA-D/` with exclusive writes.
Save `candidate-markowitz.jl` as complete source, `candidate-JSimplex.jl` and
`candidate-Project.toml` as separate ordinary-overlay inputs, plus exact inverses.
Production remains untouched. Add only `import MutableArithmetics` to candidate
module and a direct dependency UUID d8a4904e-b15c-11e9-3269-09a3773c0cb0 with
initial compatibility `=1.8.1` in candidate Project. No transitive import shortcut.
Any later wider compatibility needs its own source/behavior justification.

Replace the selected loop by `_markowitz_upper_solve!(work,upper,diagonal,sparse_pivots)`.
Generic method contains the exact original descending loop. Specialize only
Vector{BigFloat}/PackedFactorVector{BigFloat} and exact Rational{BigInt} counterparts.
No union/mixed/other-scalar specialization. A shared typed internal helper is
allowed if the exact two entry methods keep hardware dispatch free of new work.

Define `_markowitz_ma_row_eligible(seed,row,work,diagonal_vector,pivot)` for exact target types:
length>=2, paired storage lengths equal, finite seed, then
`checkbounds(Bool,diagonal_vector,pivot)` AND `isassigned(diagonal_vector,pivot)`
before the finite diagonal read. Missing/unassigned diagonal returns false. Check
bounds/assignment before every speculative coefficient/work read, then finiteness.
Return false for invalid lengths/indices/unassigned entries without throwing.
Never pass an eagerly indexed diagonal scalar into this predicate.
The caller executes the original arithmetic loop on false; no speculative
arithmetic or retry. The BigFloat entry first compares actual Base MPFR effective
and global rounding modes; mismatch runs the whole generic original loop.

Allocate acc=zero(T) and buffer=MA.buffer_for(MA.sub_mul,T,T,T) lazily at the first
eligible row, at ambient BigFloat precision. The first term uses buffered_operate_to!
with untouched seed; remaining terms use buffered_operate!. Keep ordinary division
and assignment. Never seed scratch via a rounded copy. Do not return acc/buffer,
store them in backend, or use borrowed operands as outputs. No persistent cache.
Generic/empty/singleton cases perform the original loop; same descending order.

Prove the candidate inverse restores original whole source byte-for-byte except
explicit helper insertion/call replacement, import and Project dependency fields.
Record exact paths/hashes and all intended differences; no global method overwrite
or nested whole-module clone. A later ordinary separate checkout loads candidate
and reference in separate guarded processes (not global replacement in one Julia).

## 2. Unexecuted regressions

Create `candidate-tests.jl` for future `test/markowitz_ma_upper_tests.jl` and a
prospective one-line runtests inclusion. Reuse public Markowitz coverage without
claiming it ran. Name these testsets and specify expected original-vs-candidate
results in `test-contract.md`:

- `MA upper dispatch and fallback`: Float32/64 original path, other rationals,
  zero sparse pivots, empty/one/two-term rows, dense-core-only backend.
- `MA upper scalar ownership`: aliases among seed, coefficients, work and diagonal,
  shared rational numerator/denominator leaves, retained old outputs/inputs,
  independent output owners after zero and unit division, repeated solve and
  copied backend; scratch leaf disjointness. Construction must use actual aliases,
  not only equal values. No arbitrary mutation of shared factor inputs in production.
- `MA upper sequential arithmetic`: exact rationals; BigFloat cancellation, zero
  terms and signed zero at128/256/512 ambient bits with mixed stored precisions.
  Compare every row publication with the original sequential loop, not only residual.
  Include a high-precision seed where premature ambient rounding changes subtraction.
- `MA upper rounding fallback`: scoped RoundDown/Up/ToZero/Nearest contexts with
  effective/global mismatch, including nested scopes; original rounding state
  restored, mismatch takes fallback. No mutation of global rounding to enable MA.
- `MA upper exceptions`: rational infinities and zero times infinity, zero-divisor
  DivideError/nonfinite results, BigFloat NaN/Inf/underflow/overflow/signed zeros,
  malformed paired lengths and out-of-bounds work indices. Match original exception
  class and work/destination state at throw, preserving previous-row publication.
  Include combined faults: missing OR unassigned diagonal and an earlier rational
  zero-times-infinity term must retain the original DivideError rather than an
  early BoundsError/UndefRefError; paired ordinary malformed cases retain their
  original indexing error. These are prospective tests, not executed examples.
- `MA upper lifecycle`: successive128->512->128-bit calls, growing then small rational
  limbs, repeated/copied/refactored factor solves and in-place RHS/destination public
  usage. No new retained backend fields or alias corruption.

Separate regression sensitivity: original source lacks the helper/MA route and
must fail explicit candidate-path/work assertions while semantic fallback tests
can already pass. Structural Python absence is not Julia RED. Preserve genuine
future RED errors separately from expected assertion failures.

## 3. Freeze fixtures and costs before a launch plan

Freeze exact input bits/rationals and expected selected rows for small/large,
sparse/dense input matrices, four scalar cases BigFloat128/256/512 and rational.
Use both a long-upper-row fixture and a dense-core-only control; constructor pivot
choices are not assumed. Record expected eligible row/term counts as prospective
assertions. Failure to reach selected work stops qualification, no output-driven tuning.
Sizes bounded by64; no LP, public solver or legacy driver is needed for component
cost. Reuse existing bounded integration testsets only after freezing their exact
call count and time cap. Do not rerun the old MA-A benchmark.

Freeze a short paired schedule with at least3 alternating warm pairs and7 measured
pairs per case, a bounded repeat count, all individual samples retained. Because
ordinary source overlays run in separate processes, alternate process order and
report process/cache confounding; do not claim within-process alternation or
subtract unrelated samples. The launcher plan must bound the TOTAL count of
processes, rows, terms, solves and wall time before admission; no hours-long run.
Keep Julia/BLAS1, heap2GiB, VM8GiB, availableRAM6GiB, swap1GiB guards and one Julia.

Measure complete forward solve including lazy scratch, eligibility, divisions and
publication. Also separately report construction/first use, row-kernel attribution,
steady repeated calls (which still create per-call scratch), and post-growth small
calls. No per-solve deep snapshots inside timed windows. Record time/bytes/events,
compile/recompile/GC, output comparisons and all outliers. Count original and new
scans/solves/copies/conversions; include hardware and dense-core-only controls.
Private native limb capacity is not bounded by Julia graph size; report this limit.
Independent oracle: exact rational calculation; sequential correctly rounded
BigFloat products/subtractions/division with explicit ambient bits/mode using
actual rounded inputs. Signed zero/nonfinite behavior needs a separate explicit
oracle. Source-only proofs do not replace runtime alias/output/exception tests.

MA-D delivers frozen candidate/test/fixture/cost texts and review, not a launcher
or a numerical allowance reservation. Next MA-E must turn this into one concrete
bounded admission with exact process counts, invocation/pins and fail-closed audit.
Standing human short-run permission applies there; do not ask again merely for
permission already given. Do not launch an unspecified schedule from this document.

## 4. Review, decision and publication

Review five classes explicitly: (1) scalar/leaf ownership and output publication;
(2) ordered arithmetic, scoped rounding, precision and exceptions; (3) dispatch,
caller coverage and source inverse; (4) total work/allocation/retention and comparison
validity; (5) evidence/admission, resource limits and frozen-artifact boundaries.
Use a fresh independent most-capable reviewer. Fix important findings offline with
separate before versions and concrete checks; preserve rejected reviews.

Reject the candidate if private scratch cannot preserve behavior or added total
cost removes benefit; never weaken the tests or expand scope to obtain speedup.
MA-4 integration remains conditional on subsequent measured acceptance and focused
RED/GREEN/actual-master validation. Prepare separate PASS closure, exact complete
staged names/blobs, fail-fast diagnostic commit/push and remote verification.
Update STATUS/roadmap only after preserving current bindings. Master, CI, automation
and stopped routes stay unchanged. All MA-A/C evidence remains frozen.
