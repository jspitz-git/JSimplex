# Markowitz reuse: matched production before/after measurements

The completed implementation eliminates all measured allocations in warmed Float32/Float64 refactorization across 80 matrix/update-method cases. Generic arithmetic still allocates, with measured bytes reduced by 36–75%. All 16 complete Float64 LP cases reach OPTIMAL before and after; whole-solve bytes decrease in every case, while some allocation counts and timings increase.

## Scope and method

This comparison loads complete, separate source snapshots in independent Julia processes: the pre-sequence source at `/tmp/jsimplex-markowitz-original/src`, and the completed implementation frozen at `/tmp/jsimplex-markowitz-reuse-final/src`. Only `JSimplex.jl` and `markowitz_factorization.jl` differ between these source snapshots. The production changes cover borrowing matching CSC input; retaining OrderedDict construction scratch; protecting and recycling sparse output; reusing dense-core LU/solve storage; and reducing generic-number temporary arithmetic. The related [dictionary comparison](markowitz_dictionary_report.md) explains the OrderedDict choice and pivot-order tradeoff.

Julia 1.13.0, aarch64-linux-gnu, one Julia thread, one BLAS thread. Matrix cases cover Float64 and Float32 at n64/n256, diagonal/tridiagonal/cyclic fill/dense trailing quarter/fully dense patterns, and PFI/Forrest–Tomlin/Suhl–Suhl/Bartels–Golub wrappers (80 cases). Generic cases use n32 tridiagonal/fill matrices with BigFloat and Rational{BigInt}, PFI updates (four cases). All matrix inputs are CSC.

Each matrix factor is constructed once outside measurement, then reset three times to warm compilation, workspace capacity and both private output slots. Five samples follow for floating-point cases, three for generic cases, with GC before each sample. Samples repeatedly reset the same factor; they do not create saved copies between measurements. Bytes/object counts are minima, with maxima also recorded in raw data; times below are medians. Every floating-point sample, including the maxima, is zero-allocation after the change. Measured compilation is zero throughout. The probes ran sequentially, but other repository tests overlapped; timing differences are not controlled benchmark guarantees.

## Repeated refactorization

PFI allocation and time results are shown below. All four wrappers produce the same zero-allocation result after the change; raw files contain every wrapper. The construction, new factor, saved-copy detachment, dimension/pattern changes and failure paths are outside these steady-state allocation measurements.

| Type | n | Pattern | Allocations before → after | Bytes before → after | Median μs before → after |
| --- | ---: | --- | ---: | ---: | ---: |
| Float64 | 64 | diagonal | 829 → 0 | 84,912 → 0 | 49.6 → 18.0 |
| Float64 | 64 | band | 1,048 → 0 | 95,136 → 0 | 50.9 → 32.2 |
| Float64 | 64 | fill | 1,052 → 0 | 134,264 → 0 | 155.9 → 88.4 |
| Float64 | 64 | hybrid | 848 → 0 | 128,296 → 0 | 55.7 → 33.7 |
| Float64 | 64 | dense | 24 → 0 | 102,088 → 0 | 53.5 → 40.7 |
| Float64 | 256 | diagonal | 3,155 → 0 | 332,872 → 0 | 90.4 → 32.5 |
| Float64 | 256 | band | 4,139 → 0 | 377,480 → 0 | 145.9 → 59.6 |
| Float64 | 256 | fill | 4,738 → 0 | 621,984 → 0 | 1572.9 → 816.3 |
| Float64 | 256 | hybrid | 3,828 → 0 | 1,175,408 → 0 | 356.4 → 168.7 |
| Float64 | 256 | dense | 30 → 0 | 1,585,976 → 0 | 517.9 → 360.0 |
| Float32 | 64 | diagonal | 829 → 0 | 75,408 → 0 | 35.3 → 15.4 |
| Float32 | 64 | band | 1,048 → 0 | 84,992 → 0 | 50.3 → 27.9 |
| Float32 | 64 | fill | 1,050 → 0 | 113,720 → 0 | 147.8 → 89.1 |
| Float32 | 64 | hybrid | 846 → 0 | 107,656 → 0 | 44.1 → 32.9 |
| Float32 | 64 | dense | 24 → 0 | 68,808 → 0 | 62.3 → 39.6 |
| Float32 | 256 | diagonal | 3,153 → 0 | 295,192 → 0 | 83.4 → 39.3 |
| Float32 | 256 | band | 4,138 → 0 | 337,648 → 0 | 136.0 → 63.1 |
| Float32 | 256 | fill | 4,737 → 0 | 523,880 → 0 | 1427.3 → 798.8 |
| Float32 | 256 | hybrid | 3,699 → 0 | 928,040 → 0 | 305.0 → 162.7 |
| Float32 | 256 | dense | 28 → 0 | 1,059,688 → 0 | 297.4 → 259.1 |

Matrix permutations, sparse L/U counts, sparse pivot counts and dense-core dimensions match between revisions in all 84 cases. Forward and transpose solves agree with the all-ones reference; CSC input values remain unchanged. `band` is tridiagonal, `fill` uses cyclic offsets 1/5/13, and `hybrid` has a dense trailing quarter. Structural counts for Float32/64 are:

| n | Pattern | Sparse L / U nonzeros | Sparse pivots | Dense core dimension |
| ---: | --- | ---: | ---: | ---: |
| 64 | diagonal | 0 / 0 | 62 | 2 |
| 64 | band | 59 / 59 | 59 | 5 |
| 64 | fill | 156 / 156 | 42 | 22 |
| 64 | hybrid | 0 / 0 | 42 | 22 |
| 64 | dense | 0 / 0 | 0 | 64 |
| 256 | diagonal | 0 / 0 | 254 | 2 |
| 256 | band | 251 / 251 | 251 | 5 |
| 256 | fill | 1074 / 1154 | 216 | 40 |
| 256 | hybrid | 0 / 0 | 166 | 90 |
| 256 | dense | 0 / 0 | 0 | 256 |

Sparse L/U counts exclude the separately stored diagonal and dense core. These constructed cases preserve pivot order across the two container types; this does not imply that arbitrary input matrices preserve it.

## Generic-number arithmetic

| Type | n32 pattern | Allocations before → after | Bytes before → after | Byte reduction | Median μs before → after |
| --- | --- | ---: | ---: | ---: | ---: |
| BigFloat | band | 2,241 → 361 | 136,896 → 34,656 | 74.7% | 89.7 → 56.7 |
| BigFloat | fill | 40,915 → 8,839 | 1,989,136 → 848,544 | 57.3% | 770.1 → 250.0 |
| Rational{BigInt} | band | 4,386 → 3,303 | 190,720 → 112,752 | 40.9% | 168.3 → 189.7 |
| Rational{BigInt} | fill | 80,606 → 54,839 | 2,681,160 → 1,705,880 | 36.4% | 1346.2 → 961.9 |

These improvements combine container/output reuse and arithmetic changes; this end-to-end comparison does not attribute individual savings to each step. BigFloat/BigInt scalar arithmetic and generic dense LU still allocate. No expensive generic-number complete LP solves were added to this audit.

## Complete LP solves

All cases use Markowitz refactorization, the four update methods, primal/dual algorithms, default refactorization interval 20, presolve disabled, scaling off and iteration limit 10,000. Each timed invocation starts a fresh full solve, with no global prototype cache. Five samples follow three warmups. All cases reach OPTIMAL and match known objective values within the asserted tolerance (`rtol=1e-10`, `atol=1e-7`). The largest before/after objective difference is 8.73e-10.

| Problem | Update | Algorithm | Allocations before → after | Bytes before → after | Median μs before → after | Iterations / refactorizations before → after |
| --- | --- | --- | ---: | ---: | ---: | --- |
| afiro | pfi | dual | 1,082 → 1,127 | 111,744 → 84,384 | 184.5 → 165.4 | 20 / 1 → 20 / 1 |
| afiro | pfi | primal | 1,499 → 1,798 | 156,976 → 127,680 | 177.9 → 173.4 | 16 / 1 → 16 / 1 |
| afiro | forrest_tomlin | dual | 1,336 → 1,381 | 122,848 → 95,488 | 206.8 → 202.2 | 20 / 1 → 20 / 1 |
| afiro | forrest_tomlin | primal | 1,761 → 2,060 | 169,040 → 139,744 | 212.9 → 202.8 | 16 / 1 → 16 / 1 |
| afiro | suhl_suhl | dual | 1,328 → 1,373 | 122,800 → 95,440 | 208.0 → 209.9 | 20 / 1 → 20 / 1 |
| afiro | suhl_suhl | primal | 1,759 → 2,058 | 170,304 → 141,008 | 207.3 → 195.1 | 16 / 1 → 16 / 1 |
| afiro | bartels_golub | dual | 1,445 → 1,490 | 129,328 → 101,968 | 227.1 → 228.6 | 20 / 1 → 20 / 1 |
| afiro | bartels_golub | primal | 1,850 → 2,149 | 176,416 → 147,120 | 217.8 → 225.0 | 16 / 1 → 16 / 1 |
| adlittle | pfi | dual | 10,376 → 2,853 | 1,202,016 → 307,240 | 1088.7 → 865.3 | 111 / 11 → 114 / 4 |
| adlittle | pfi | primal | 5,996 → 3,937 | 749,488 → 393,968 | 854.4 → 792.0 | 82 / 5 → 82 / 5 |
| adlittle | forrest_tomlin | dual | 5,108 → 3,381 | 629,904 → 368,048 | 994.2 → 1045.6 | 98 / 4 → 98 / 4 |
| adlittle | forrest_tomlin | primal | 6,632 → 4,573 | 802,896 → 448,208 | 1059.6 → 1020.0 | 82 / 5 → 82 / 5 |
| adlittle | suhl_suhl | dual | 5,094 → 3,464 | 632,128 → 375,920 | 1021.5 → 979.2 | 98 / 4 → 99 / 5 |
| adlittle | suhl_suhl | primal | 6,642 → 4,585 | 812,080 → 460,464 | 1109.8 → 1023.5 | 82 / 5 → 82 / 5 |
| adlittle | bartels_golub | dual | 6,240 → 3,769 | 742,352 → 396,192 | 1462.6 → 1215.6 | 100 / 5 → 100 / 5 |
| adlittle | bartels_golub | primal | 6,809 → 4,750 | 816,064 → 460,480 | 1278.5 → 1335.4 | 82 / 5 → 82 / 5 |

Afiro performs only one reported refactorization. Its allocated bytes fall while allocated object counts rise: the fresh OrderedDict/workspace/output setup has a different allocation profile and receives little repeated-reset amortization. This is why steady-state zero allocation does not imply fewer allocation events in every complete solve.

Adlittle PFI dual changes from 111 iterations/11 refactorizations to 114/4; Suhl–Suhl dual changes from 98/4 to 99/5. OrderedDict gives stable insertion order rather than the previous Dict hash iteration order, affecting tied pivots and downstream floating-point behavior. Full-solve costs include those trajectory changes. Other cases retain the listed iteration/refactorization counts, though matching counts alone do not prove identical internal paths. Afiro objectives are approximately -464.753142857143 and adlittle objectives 225494.96316238.

## Validation and limits

Each revision passes 420 matrix assertions plus 32 full-solve status/objective assertions: 452 checks per revision, 904 total. Cross-result checks confirm identical permutations/fill/core sizes on the 84 constructed matrix cases, zero after-allocation maxima on all 80 floating cases, and zero measured compilation time. This diagnostic is separate from the production regression suite and the independent history/rollback tests.

The complete production regression suite passes **222,012/222,012** checks
(8m03.9s). The focused implementation suite passes 3,129 checks; the subsequent
updated workspace/core suite passes 580 checks, including the additional dense
NaN rollback and shrink/regrowth capacity regressions. An independent review
also passes 480 randomized reset histories across the four update methods.
`git diff --check` is clean, and current production source hashes match the
measured after revision.

Allocation counters measure traffic, not retained memory or peak RSS. Private reusable dictionaries and two protected output/core slots can retain more memory. These timings are from a shared host; several whole-solve medians increase slightly, and the data does not justify a universal runtime speedup claim. Capacity growth, changed dimensions, saved snapshots, startup cost, singular refactorizations and concurrent factorization require their own functional coverage and may allocate.

## Reproduction and raw data

- [Probe](markowitz_reuse_probe.jl).
- [Before results](markowitz_reuse_before.toml).
- [After results](markowitz_reuse_after.toml).

The raw files record SHA-256 hashes of every original source file before dependency-loader adaptation. The probe copies the complete selected source directory into a private temporary directory and changes only dependency imports to `Base.require(PkgId(...))`, which supplies the package context absent from direct module inclusion. Factorization and solver source remain unmodified. The `/tmp` source snapshots are session-local; preserve them when reproducing this exact comparison. A rerun against later source should be reported as a new revision and checked against the recorded hashes.

```sh
julia --startup-file=no --compiled-modules=existing --project=dev diagnostics/markowitz_reuse_probe.jl before diagnostics/markowitz_reuse_before.toml /tmp/jsimplex-markowitz-original/src
julia --startup-file=no --compiled-modules=existing --project=dev diagnostics/markowitz_reuse_probe.jl after diagnostics/markowitz_reuse_after.toml /tmp/jsimplex-markowitz-reuse-final/src
```

Omitting the third argument selects the original snapshot for `before` and the current repository `src` for `after`.
