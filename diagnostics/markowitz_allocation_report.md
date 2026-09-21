# Markowitz allocation opportunities

This audit maps the current implementation; no production code is changed.
The main opportunity is repeated factorization, especially rebuilding sparse
elimination dictionaries and factor vectors. Warmed in-place Float32/Float64
FTRAN and BTRAN already allocate nothing in the measured cases.

## Scope and measurements

Julia 1.13.0, aarch64-linux-gnu, one Julia and BLAS thread. Three samples follow
two warmups, with fresh mutable setup outside each measurement. All measured
compilation times are zero. The audit includes 40 matrix/type cases and four
stages per case (refactorization, FTRAN, BTRAN, saved-factor copy), plus 16 complete
Float64 solves. Float32/Float64 dimensions are 64/256; BigFloat and
Rational{BigInt} dimensions are 16/32.

Patterns are diagonal, tridiagonal, sparse with fill-in, identity-like with a
dense trailing block, and fully populated. All constructor inputs are CSC. The
fill case has three cyclic off-diagonals. Patterns exercise different sparse
elimination lengths and dense-core sizes; these are examples rather than a
representative distribution of production bases.

Counters report allocated objects/bytes, not retained memory or peak RSS.
`Profile.Allocs` uses rate 1 for Float64 and rate 0.05 for selected generic cases.
Profile sizes and allocation events do not exactly equal GC counters; profile
percentages below use the profile's own totals and are attribution evidence,
not exact achievable savings. Timings overlapped other probes and are not used
to claim runtime improvements.

Float64, one repeated refactorization:

| Dimension | Pattern | Sparse pivots / dense core | Allocations | Bytes |
| ---: | --- | --- | ---: | ---: |
| 64 | diagonal | 62 / 2 | 829 | 84,912 |
| 64 | tridiagonal | 59 / 5 | 1,048 | 95,136 |
| 64 | fill-in | 42 / 22 | 1,052 | 134,264 |
| 64 | dense trailing block | 42 / 22 | 848 | 128,296 |
| 64 | dense | 0 / 64 | 24 | 102,088 |
| 256 | diagonal | 254 / 2 | 3,155 | 332,872 |
| 256 | tridiagonal | 251 / 5 | 4,139 | 377,480 |
| 256 | fill-in | 216 / 40 | 4,738 | 621,984 |
| 256 | dense trailing block | 166 / 90 | 3,828 | 1,175,408 |
| 256 | dense | 0 / 256 | 30 | 1,585,976 |

The 50% density switch can leave a small dense core even for a diagonal matrix;
the core sizes in the table are observed, not inferred from the input pattern.
Float32 shows the same structural sources: the 256-row tridiagonal case allocates
4,138 objects / 337,648 B, and the fill case 4,737 / 523,880 B.

## 1. Remove the redundant input CSC copy

`MarkowitzBackend` line 185 constructs `SparseMatrixCSC{T,Int}(B)` even if `B`
already has that exact type. This copies its three arrays. The subsequent code
only reads the CSC and copies entries into independent dictionaries or a dense
matrix. A matching `convert` can borrow the CSC arrays during construction.

A process-local counterfactual replacing only this constructor with `convert`
measured the following Float64 savings:

| Dimension | Pattern | Allocations before → prototype | Bytes saved |
| ---: | --- | ---: | ---: |
| 64 | diagonal | 829 → 823 | 1,728 |
| 64 | tridiagonal | 1,048 → 1,042 | 3,904 |
| 64 | dense CSC | 24 → 16 | 66,256 |
| 256 | diagonal | 3,155 → 3,146 | 6,424 |
| 256 | tridiagonal | 4,139 → 4,130 | 14,616 |
| 256 | dense CSC | 30 → 21 | 1,050,904 |

This is a small implementation change with a particularly large benefit for
dense CSC input. Dense `StridedMatrix` input already takes an earlier path and
does not incur this CSC copy. Both counterfactual and baseline passed input
preservation and post-construction input-mutation checks for all six Float64
cases. Other scalar types need coverage when implementing the change.

## 2. Retain sparse elimination workspace

The row/column dictionaries at lines 191–200 are rebuilt on every factorization,
then may grow further during elimination at lines 56–57. For the 256-row
tridiagonal case, these sites account for 2,054 profiled allocations / 209,008
profiled bytes, or 60.8% of all profiled bytes. Their shares are 68.1% for the
diagonal case, 65.2% for fill-in and 80.9% for the dense-block case.

Keep a private workspace with both dictionary arrays, active-row/column flags,
singleton queues, doubleton bit set, affected rows and position maps. The installed
Julia `empty!(::Dict)` clears entries while keeping table capacity; rebuilding a
similar basis can use retained tables. If `sizehint!` is used, request
`shrink=false`. Retain excess per-row objects for later dimension growth rather
than discarding them on every shrink.

These dictionaries are construction scratch, not part of the finished factors.
One private construction workspace per independently mutable factor can suffice;
two copies of every dictionary are not inherently required for rollback.

The significant complication is pivot determinism. Retained dictionary capacities
can change iteration order. The current pivot selection keeps the first candidate
when both score and magnitude tie, so a capacity change may change pivots, fill-in
and floating rounding. Decide how ties should be ordered and test numerical
behavior and complete solves; do not assume identical iteration histories from
capacity reuse alone. Dictionary deletion/rehashing and later fill-in may still
allocate even after initial table reuse.

## 3. Recycle private sparse L/U output arrays and metadata

Each sparse pivot allocates fresh index/value vectors for U (225–232) and L
(239–258), including empty vectors for many singleton pivots. Outer L/U arrays,
diagonal and permutation arrays also grow anew. At dimension 256, the profiled
packed-vector sites account for about 87,360 B in the tridiagonal case and
137,024 B in the fill-in case, apart from dictionary storage.

A reusable candidate factor can keep these vectors and capacities across resets,
like the update-history pools already used elsewhere. Avoid permanently allocating
empty vectors per singleton when existing private empty vectors can be reused.

Ownership is essential: `_copy_backend` currently shares permutations, L/U,
diagonal and dense core, while allocating private solve work vectors. A reset
must not clear or overwrite arrays used by a saved copy or the current active
factor. Recycle only an unshared candidate; install it after successful complete
factorization. Construction failure must leave the old basis and updates usable.

## 4. Reuse dense-core LU and solve work storage

The trailing matrix is freshly allocated at line 298 (or the dense fast path),
then `_markowitz_backend` calls `lu!(core_matrix)` and allocates a new pivot vector,
`work` and `core_work`. Markowitz does not call the recently optimized Float32
native backend, so it does not yet benefit from that reuse.

For Float32/Float64, reuse a same-size private dense-core LU via `lu!(F, A)` and
retain work-vector capacity. On the 256-row fully dense Float64 case the core
matrix alone occupies 524,288 B; removing the CSC copy first exposes it as the
next major allocation. On the tridiagonal case the core is only 5-by-5, so this
has much lower byte impact than dictionaries and packed vectors.

The core size changes independently of the basis dimension. Handle that explicitly
and keep saved-copy protection and failure rollback. Two core/output slots retain
more memory; this is an allocation-traffic optimization, not a guaranteed memory
footprint reduction.

## 5. Address generic-number arithmetic separately

Container reuse will not eliminate BigFloat/BigInt scalar allocations. For the
32-row tridiagonal case:

| Type | Refactorization allocations / bytes | FTRAN allocations / bytes | BTRAN allocations / bytes |
| --- | ---: | ---: | ---: |
| BigFloat | 2,241 / 144,672 | 191 / 18,336 | 187 / 17,952 |
| Rational{BigInt} | 4,386 / 201,632 | 1,685 / 66,480 | 1,618 / 63,120 |

The 32-row fill-in case grows to 40,915 allocations / 2,198,032 B for BigFloat and
80,606 / 2,685,384 B for Rational{BigInt}. Sampled profiles identify magnitude and
threshold comparisons, elimination arithmetic and the dense LU as significant
sources. Candidates for a later numeric-specific pass:

- Avoid repeatedly constructing `zero(T)`, including the eagerly evaluated
  fallback in `get(rows[row], column, zero(T))` inside the elimination loop.
- Reuse constants and compute rational column thresholds once per valid column
  maximum instead of dividing by `T(10)` for each candidate.
- Investigate private temporaries for BigFloat magnitude/threshold comparisons.
  Preserve the existing handling of stored values with higher precision and very
  large exponents; replacing the current exact-times-ten test with a rounded
  threshold is not equivalent.
- Cache column maxima only with correct invalidation on insertion, deletion and
  value changes. This may reduce work and generic scalar allocations, but is a
  more involved algorithmic change than reusing containers.

All 40 Float32/Float64 FTRAN/BTRAN measurements allocate zero objects and bytes.
Adding additional solve buffers there would not help. Saved-factor copying does
allocate private work arrays by design: for Float64 at dimension 256 it costs
11–12 allocations / 4,528–6,568 B across the measured patterns. Sharing that mutable
solve scratch between copies would violate the current isolation contract.

## Whole-solver relevance and recommended order

All 16 Float64 afiro/adlittle runs (four update methods, primal/dual, default
interval 20, presolve/scaling off) reach OPTIMAL. For adlittle/PFI, dual uses
10,376 allocations / 1,202,016 B over 111 pivots and 11 refactorizations; primal
uses 5,996 / 749,488 B over 82 pivots and five refactorizations.

In their full-solve profiles, dictionary construction/population/growth accounts
for 57.9% of profiled bytes in dual and 50.2% in primal. All Markowitz source sites
together account for 89.2% and 77.8% respectively. These are current attribution
shares, not promised percentages removable by one change. Comparison against the
native backend would also mix different pivot/refactorization histories.

Recommended sequence: remove the redundant CSC copy first; then retain private
construction dictionaries and scratch; then recycle protected L/U output arrays;
then reuse the dense core where its size makes this worthwhile. Generic-number
arithmetic merits a separate pass guided by the intended scalar type/workload.

## Verification and reproduction

The audit passed 80 reference-solve checks. The existing Markowitz test file
passed all 307 assertions (1m00.7s), including threshold precision, fill, permutations,
copies, dense cores and scalar types. The two CSC counterfactual runs each passed
12 ownership/solve checks. `git diff --check` passes. No full production suite was
rerun because this audit does not change production source.

```sh
julia --startup-file=no --compiled-modules=existing --project=dev diagnostics/markowitz_allocation_probe.jl diagnostics/markowitz-allocation-audit.toml
julia --startup-file=no --compiled-modules=existing --project=dev diagnostics/markowitz_csc_copy_probe.jl before diagnostics/markowitz-csc-copy-before.toml
julia --startup-file=no --compiled-modules=existing --project=dev diagnostics/markowitz_csc_copy_probe.jl borrow diagnostics/markowitz-csc-copy-borrow.toml
julia --startup-file=no --compiled-modules=existing --project=dev -e 'using JSimplex, Test; include("test/markowitz_tests.jl")'
```

Raw data: [main audit and profiles](markowitz-allocation-audit.toml),
[CSC baseline](markowitz-csc-copy-before.toml),
[CSC borrowing prototype](markowitz-csc-copy-borrow.toml).

## Implementation follow-up

The approved five steps have been implemented. See the
[production reuse comparison](markowitz_reuse_report.md) for current measurements,
the [Dict/OrderedDict comparison](markowitz_dictionary_report.md) for the chosen
construction representation, and the [execution record](../docs/superpowers/plans/2026-09-21-markowitz-allocation-reuse.md)
for verification. The allocation figures above describe the original audit;
they are retained as the baseline, not current remaining costs.
