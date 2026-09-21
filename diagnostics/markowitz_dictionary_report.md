# Markowitz construction dictionaries: Dict versus OrderedDict

Recycled OrderedDict is the stronger candidate in this experiment: it reaches the same warmed allocation counts as recycled Dict on every Float64 case, keeps pivot order independent of earlier capacity growth, and avoids the large iteration slowdown seen when Dict retains oversized tables. It changes the existing hash-order tie behavior, so adoption is a numerical-path change as well as a storage change. These diagnostics do not modify production source or dependencies.

## Method

Julia 1.13.0, aarch64-linux-gnu, one Julia and BLAS thread; OrderedCollections 2.0.1 from the installed transitive package. Four separate sequential processes compare fresh Dict, recycled Dict, fresh OrderedDict and recycled OrderedDict. The baseline is `/tmp/jsimplex-markowitz-after-csc.jl`, with the input CSC already borrowed. A frozen copy of the surrounding source is in `/tmp/jsimplex-markowitz-dictionary-frozen/src`; process-local `include_string` replacements select the dictionary type and optional scratch reuse. Production changes made after freezing cannot enter these runs.

Both recycled variants retain row/column dictionaries, active flags, singleton queues, the doubleton set, affected rows and position maps. L/U output vectors, permutations, diagonal, dense core and solve buffers are fresh. The scratch cache is global per scalar type, for this single-threaded prototype only. It is emptied before every matrix case and every measured full solve. It can share construction scratch across independent backend instances within a full solve; a production per-backend workspace may therefore save less in full solves. Shrinking the dimension currently discards excess dictionaries. Neither limitation is a production recommendation.

Allocation counters and minimum/median elapsed times follow two warmups and a GC before each sample. Float64 cases use seven samples, other types three, full solves five. Measured compilation is zero everywhere. Timings overlapped other repository testing, so they are evidence of direction and scale rather than isolated benchmark guarantees. All comparison tables below use median time.

## Repeated same-matrix refactorization

Cells show **allocations / bytes / microseconds**. Each numeric path is the same across all four variants on these matrices: identical row/column permutations, sparse L/U counts and dense-core dimension. This isolates container reuse from changes in fill.

| n | Pattern | Fresh Dict | Recycled Dict | Fresh OrderedDict | Recycled OrderedDict |
| ---: | --- | ---: | ---: | ---: | ---: |
| 64 | diagonal | 823 / 83,184 / 34.6 | 283 / 19,888 / 23.2 | 1,463 / 81,136 / 30.4 | 283 / 19,888 / 33.9 |
| 64 | band | 1,042 / 91,232 / 51.6 | 507 / 31,024 / 47.4 | 1,682 / 89,184 / 39.7 | 507 / 31,024 / 41.8 |
| 64 | fill | 1,044 / 129,448 / 167.3 | 412 / 33,432 / 164.7 | 2,420 / 206,376 / 113.4 | 412 / 33,432 / 97.7 |
| 64 | hybrid | 840 / 122,712 / 50.0 | 204 / 21,528 / 49.3 | 1,640 / 122,200 / 50.3 | 204 / 21,528 / 48.2 |
| 256 | diagonal | 3,146 / 326,448 / 89.4 | 1,062 / 76,224 / 78.0 | 5,706 / 318,256 / 69.1 | 1,062 / 76,224 / 60.7 |
| 256 | band | 4,130 / 362,864 / 142.5 | 2,054 / 124,224 / 130.9 | 6,690 / 354,672 / 93.6 | 2,054 / 124,224 / 88.5 |
| 256 | fill | 4,729 / 603,272 / 1600.7 | 2,223 / 189,224 / 1641.3 | 10,277 / 947,336 / 888.7 | 2,223 / 189,224 / 942.2 |
| 256 | hybrid | 3,819 / 1,104,472 / 374.2 | 711 / 131,304 / 193.3 | 7,019 / 993,880 / 241.6 | 711 / 131,304 / 193.7 |

`band` is tridiagonal; `fill` has three cyclic off-diagonals; `hybrid` is diagonal with a dense trailing quarter. The fresh OrderedDict fill cases allocate more objects and bytes as insertion arrays grow. After same-matrix warmup, both containers have enough capacity and their Float64 allocation totals match exactly. This does not imply zero refactorization allocations: fresh output/core allocation remains.

| n | Pattern | L nonzeros | U nonzeros | Sparse pivots | Dense core dimension |
| ---: | --- | ---: | ---: | ---: | ---: |
| 64 | diagonal | 0 | 0 | 62 | 2 |
| 64 | band | 59 | 59 | 59 | 5 |
| 64 | fill | 156 | 156 | 42 | 22 |
| 64 | hybrid | 0 | 0 | 42 | 22 |
| 256 | diagonal | 0 | 0 | 254 | 2 |
| 256 | band | 251 | 251 | 251 | 5 |
| 256 | fill | 1074 | 1154 | 216 | 40 |
| 256 | hybrid | 0 | 0 | 166 | 90 |

L/U counts exclude the separate sparse diagonal and the dense core. Forward and transpose reference solves pass for all 20 type/shape cases in each variant: Float64 n64/256, Float32 n64, and BigFloat/Rational{BigInt} n16, four patterns each. Saved-factor copies remain usable after construction scratch is reused. Float32 has the largest ordinary-case error, 3.58e-7; generic arithmetic remains the dominant allocation source on fill cases. For n16 fill, recycled Dict/OrderedDict use 385,600/385,600 B for BigFloat and 574,552/574,920 B for Rational{BigInt}.

## Capacity history and equal-magnitude ties

The history run first factors a genuinely denser matrix of the same dimension (diagonal n+1, negative cyclic offsets 1 through n/4), then returns to the original matrix. Retained hash slots confirm that capacity is reused. Standard diagonal-dominant patterns keep the same pivots/fill after this history in both containers, but oversized Dict tables make iteration materially more expensive.

| n256 pattern | Dict ordinary → after-history μs | OrderedDict ordinary → after-history μs | Dict / OrderedDict retained hash slots after history |
| --- | ---: | ---: | ---: |
| diagonal | 78.0 → 131.6 | 60.7 → 132.2 | 132,608 / 131,072 |
| band | 130.9 → 287.6 | 88.5 → 203.1 | 132,608 / 131,072 |
| fill | 1641.3 → 5914.6 | 942.2 → 1021.6 | 133,504 / 131,072 |
| hybrid | 193.3 → 212.7 | 193.7 → 249.6 | 132,608 / 131,072 |

This is allocation traffic versus retained capacity, not a retained-memory measurement. Both types pay to clear hash slots; Dict also scans its table while iterating, whereas OrderedDict iterates its live insertion arrays. Large earlier matrices can therefore affect time even when they do not change the numerical path.

A second probe uses 40 nonsingular n32 matrices with diagonal 1 and three cyclic off-diagonals whose signs come from `MersenneTwister(seed)`, seeds 1–40. Every candidate magnitude initially ties. Same-matrix warmup changes no pivots in either container. After the denser-matrix history, Dict changes permutations **and L/U/core structural counts in 40/40 cases**; OrderedDict changes neither in **0/40 cases**. For seed 2, Dict L/U/core changes from 56/51/16 to 55/56/15. All 480 forward/transpose checks across the two tie experiments pass; maximum error is 8.71e-14 for Dict and 7.75e-14 for OrderedDict.

OrderedDict achieves stable insertion order across different capacities, but it does not reproduce the original Dict order. Retaining Dict and specifying a deterministic tie rule alone also needs care: row traversal, update order and singleton queue insertion can affect subsequent pivots even when the general pivot-search tie is explicit.

## Complete solves

PFI basis updates, Markowitz refactorization, primal and dual algorithms, presolve disabled, scaling off, iteration limit 10,000. All 16 runs reach OPTIMAL. Each measured solve starts with an empty prototype scratch cache.

| Problem / algorithm | Fresh Dict bytes / μs | Recycled Dict bytes / μs | Fresh OrderedDict bytes / μs | Recycled OrderedDict bytes / μs |
| --- | ---: | ---: | ---: | ---: |
| afiro / dual | 109,664 / 186.4 | 83,616 / 183.6 | 109,136 / 174.0 | 83,952 / 197.6 |
| afiro / primal | 154,480 / 172.2 | 101,840 / 179.6 | 151,888 / 164.6 | 100,976 / 176.9 |
| adlittle / dual | 1,158,848 / 1121.0 | 485,216 / 1043.8 | 571,528 / 866.9 | 332,280 / 846.4 |
| adlittle / primal | 730,144 / 914.2 | 386,896 / 805.3 | 751,312 / 785.4 | 399,472 / 870.2 |

Fresh and recycled versions of each container follow the same solver trajectory. Afiro takes 20/16 dual/primal iterations and one reported refactorization, with objective approximately -464.753142857143. Adlittle primal takes 82 iterations and five refactorizations for both containers. Adlittle dual differs: Dict takes 111 iterations and 11 refactorizations; OrderedDict takes 114 iterations and four refactorizations. All adlittle objectives agree with 225494.96316238 (container difference below 1e-9). OrderedDict’s lower dual full-solve cost therefore includes changed solver behavior and must not be attributed solely to faster dictionary operations.

## Recommendation and limits

Prefer recycled OrderedDict over unconstrained recycled Dict if adding OrderedCollections as a direct dependency and accepting changed pivot tie order are within scope. It gives the same warmed floating-point allocation savings, stable preparation-history behavior in the explicit tie test, and better measured sparse iteration performance. Keep the workspace private per independently mutable factor; do not copy this prototype’s global cache into production.

The evidence is limited to these constructed matrices and two small LPs. It does not establish numerical equivalence for all inputs, quantify peak or retained memory, cover multithreading, or exercise production failure rollback. Generic-number calculations are unchanged and still allocate. Container choice and output/dense-core reuse should be evaluated separately so their ownership risks remain clear.

## Artifacts and reproduction

- Main prototype: `diagnostics/markowitz_dictionary_probe.jl`.
- Tie/history prototype: `diagnostics/markowitz_dictionary_ties_probe.jl`.
- Raw main results: `diagnostics/markowitz_dictionary_{dict_fresh,dict_recycled,ordered_fresh,ordered_recycled}.toml`.
- Raw tie results: `diagnostics/markowitz_dictionary_{dict,ordered}_ties.toml`.
- Frozen production snapshot: `/tmp/jsimplex-markowitz-dictionary-frozen/src` and baseline `/tmp/jsimplex-markowitz-after-csc.jl` (session-local, required by these probes). The frozen `moi.jl` imports its installed dependency with `Base.require(PkgId(...))` because directly including the isolated module has no package dependency context.

```sh
julia --startup-file=no --compiled-modules=existing --project=dev diagnostics/markowitz_dictionary_probe.jl dict_recycled diagnostics/markowitz_dictionary_dict_recycled.toml
julia --startup-file=no --compiled-modules=existing --project=dev diagnostics/markowitz_dictionary_ties_probe.jl ordered_recycled diagnostics/markowitz_dictionary_ordered_ties.toml
```

Use the other mode names from the artifact list for the other runs. These commands intentionally require the frozen snapshot; silently running against production after subsequent optimization would invalidate the comparison.
