# KLU versus UMFPACK on the same saved basis matrices

KLU is a useful alternative, not a universal replacement. On six large runtime bases its paired-median factor time is3–24% lower and FTRAN9–19% lower, while BTRAN6–25% higher. On fast0507 factorization is21–24% faster but solves are generally slower. The single dense irreducible control has2.30x factor time under KLU. One sparse irreducible control remains competitive despite having no BTF separation.

One new guarded process completed in25.16s (supervisor25.37s),1009/1009 ordinary Test assertions passed, exit0,20/20 offline checks passed. No new LP solve, SS/direct-export implementation, production/permanent-test/environment/master/CI modification. All earlier frozen evidence preserved. Source-only design baseline f9f1e9b4076bd541150dedba8df26efc6429d34a; master c0fa748ffa61ccb7c1caaf248c40324f60bc737b.

## Fixed inputs and costs

Nine actual Float64/Int64 bases: runtime-30000, runtime-40000 and fast0507 at saved-exchange positions0/80/160. The same exact matrix/RHS bytes serve both arms, with actual next entering column, deterministic dense RHS and actual next leaving unit RHS. Artificial columns use the captured negative identity. Three256-row controls add an irreducible sparse cycle, irreducible dense matrix and32 coupled eight-row blocks. No MPS parse or medium factorization. Captures describe fixed historical internal matrices, not a current-master simplex trajectory.

Fresh factorization includes owned CSC/index conversion, symbolic analysis/BTF/order and numeric factorization. KLU uses its separate L*U+F representation and native complete solves, with no transformed coupling export. Two warm complete samples precede five alternating measured pairs per case;32 triplets per measured sample (two FTRAN plus one BTRAN). FTRAN figures below average one sparse-entering and one dense RHS; BTRAN uses the unit RHS. KLU adapter copies RHS into its destructive API; UMFPACK uses the distinct destination/RHS API without that extra copy. All adapter/check/lock work is included.

UMFPACK6.3.5 controls match the existing threshold_one path: PIVOT_TOLERANCE=1 and IRSTEP=0, other defaults including automatic strategy unchanged. KLU2.3.5 uses tol=1, BTF on, AMD, row-sum scaling and maxwork=10. KLU's diagonal preference and UMFPACK's ordinary/symmetric strategy policies are not asserted equivalent. These results compare these concrete backend policies, not an isolated ordering kernel.

KLU.jl revision2975044cb3ac1f76f9d3eeef7ee6deedfe8375a0 is source-included as an isolated diagnostic module with unchanged vendored bytes. No Pkg install or project/cache mutation; installed Julia1.13 SuiteSparse libraries are runtime path/hash checked. Version-matched upstream C headers are source evidence, not proof of installed build identity.

## Warm measurements

K/U ratios are medians of matched-round ratios; absolute numbers are independent side medians and must not be divided to replace those statistics. Ranges and MAD for all five pairs are in analysis.json; all per-window values remain in results-1.toml.

| Basis | Factor U / K ms | FTRAN U / K µs | BTRAN U / K µs | Paired K/U factor / F / B |
|---|---:|---:|---:|---:|
| runtime-30000-B0 | 12.000 / 10.195 | 245.484 / 204.663 | 198.634 / 210.159 | 0.889 / 0.809 / 1.080 |
| runtime-30000-B80 | 12.636 / 10.867 | 255.688 / 206.087 | 206.884 / 225.125 | 0.879 / 0.807 / 1.104 |
| runtime-30000-B160 | 14.213 / 10.807 | 261.216 / 221.238 | 200.734 / 218.044 | 0.760 / 0.879 / 1.071 |
| runtime-40000-B0 | 15.968 / 13.894 | 306.998 / 248.291 | 243.903 / 255.081 | 0.847 / 0.812 / 1.058 |
| runtime-40000-B80 | 15.803 / 15.519 | 299.080 / 270.945 | 237.153 / 291.225 | 0.967 / 0.908 / 1.249 |
| runtime-40000-B160 | 16.172 / 12.771 | 288.102 / 253.336 | 233.925 / 258.188 | 0.790 / 0.848 / 1.125 |
| fast0507-1000-B0 | 0.559 / 0.417 | 3.648 / 3.959 | 3.962 / 4.350 | 0.760 / 1.054 / 1.106 |
| fast0507-1000-B80 | 0.573 / 0.447 | 4.544 / 4.666 | 4.478 / 5.216 | 0.780 / 1.039 / 1.121 |
| fast0507-1000-B160 | 0.623 / 0.487 | 4.234 / 5.606 | 4.837 / 6.344 | 0.785 / 1.302 / 1.311 |
| irreducible-sparse256 | 0.179 / 0.116 | 1.858 / 2.022 | 1.897 / 1.588 | 0.659 / 1.088 / 0.838 |
| irreducible-dense256 | 1.478 / 3.402 | 28.052 / 28.083 | 26.803 / 40.062 | 2.302 / 0.993 / 1.500 |
| coupled-blocks256 | 0.267 / 0.149 | 2.869 / 2.295 | 2.762 / 2.647 | 0.568 / 0.800 / 0.948 |

On the runtime bases, five of six2F+1B triplet median ratios favor KLU:0.878,0.887,0.902,0.878,1.016,0.925. The last two ranges cross1, as does runtime30000/B80. The corresponding fast ratios1.082,1.065,1.331 all have ranges above1. This is the cost of the selected native solve mix, excluding update/pricing/certification and excluding amortized factorization. It is not a simplex-step or solver speedup.

Factorization medians favor KLU in all nine real bases, but four of the six runtime paired ranges cross1; only runtime30000/B0 and runtime40000/B160 have all five factor ratios below1. Fast factor pairs are consistently below1. Runtime FTRAN is consistently lower except runtime40000/B80 whose range crosses1. Short single-process measurements and backend-policy differences limit inference.

All120 measured samples have zero measured compilation/recompilation and in-window GC across factor/FTRAN/BTRAN stages. Preparation loading/assembling all12 cases takes0.383s inclusive, of which0.223s compilation;135,759,440 GC-counter allocation bytes/314,873 events, outside hot windows. Cold qualification and full-process compilation/cleanup are separate and not attributed as speedups.

## Allocations and memory

Both backends have zero GC-counter bytes/events in every measured FTRAN/BTRAN window. At runtime factor construction KLU uses only50–57% of UMFPACK allocation traffic bytes, but15.5–19.4x as many allocation events (1283–1626 versus83–84 per factor). Many small native block allocations are plausible from KLU's organization; exact event category attribution was not instrumented. These counters may include native SuiteSparse callback allocations, not only Julia objects or live memory.

KLU's final reported native footprint is10–21% HIGHER on runtime bases, despite fewer stored L/U/F entries; its native peak is19–33% LOWER. On fast0507 final native footprint is43–77% higher. Fewer coefficients and lower cumulative allocation bytes therefore do not imply lower retained memory. Native allocation reserve/block structures are included by KLU's memory counters; no tuning of those parameters was attempted.

| Basis | Native current U / K MiB | Native peak U / K MiB | Stored entries U / K (L+U+F) | KLU blocks / largest |
|---|---:|---:|---:|---:|
| runtime-30000-B0 | 5.589 / 6.146 | 9.713 / 6.547 | 238543 / 195694 | 22130 / 3767 |
| runtime-30000-B80 | 5.604 / 6.281 | 9.715 / 6.650 | 240202 / 204555 | 22087 / 3833 |
| runtime-30000-B160 | 5.683 / 6.364 | 9.719 / 6.636 | 244673 / 210033 | 22075 / 3675 |
| runtime-40000-B0 | 6.246 / 7.289 | 9.962 / 7.793 | 302071 / 271536 | 21170 / 4603 |
| runtime-40000-B80 | 6.157 / 7.435 | 9.965 / 8.087 | 289562 / 281100 | 21201 / 4666 |
| runtime-40000-B160 | 6.063 / 6.942 | 9.965 / 7.702 | 283756 / 248722 | 21248 / 4589 |
| fast0507-1000-B0 | 0.112 / 0.162 | 0.251 / 0.230 | 5124 / 7179 | 253 / 228 |
| fast0507-1000-B80 | 0.131 / 0.186 | 0.265 / 0.290 | 7257 / 8767 | 225 / 260 |
| fast0507-1000-B160 | 0.124 / 0.220 | 0.270 / 0.299 | 6303 / 10962 | 225 / 260 |
| irreducible-sparse256 | 0.047 / 0.047 | 0.142 / 0.075 | 981 / 1022 | 1 / 256 |
| irreducible-dense256 | 0.534 / 1.036 | 3.073 / 1.133 | 65792 / 65792 | 1 / 256 |
| coupled-blocks256 | 0.065 / 0.065 | 0.201 / 0.065 | 3420 / 2552 | 32 / 8 |

KLU native current/peak are snapshotted before cold diagnostic extraction/sorting. UMFPACK current=(NUMERIC_SIZE+SYMBOLIC_SIZE)*SIZE_OF_UNIT and peak=PEAK_MEMORY*SIZE_OF_UNIT. These are library reports, not independently captured allocation/free ledgers. Julia reachable wrapper graphs are separate (runtime U2.57–2.72MiB, K2.14–2.28MiB) and omit native pointer payload. The last resource sample gives process HWM608,296KiB/VM peak1,166,308KiB; RSS, compiler/allocator retention and per-factor native footprints are not interchangeable. RSS before/held/released is saved for context, not native free proof.

Cold metadata accesses UMFPACK L/U/Rs separately (three native extractions), and KLU L/U/F/Rs/p (up to five native sort/extract calls, four if F empty). This avoidable diagnostic repetition is bounded outside all measured windows; it is not proposed production work. Numerical cold solves/enclosures run BEFORE extraction so they qualify the same unsorted native state as measured factors. Untimed residual/norm/hash scans and their O(nnz+n) temporaries also remain outside hot windows and are included in process cost.

## Numerical and ownership qualification

All24 cold qualifications passed three normal forward/transpose residual checks and independent directed256-bit enclosures, plus two known-point solves. Maximum cold normwise residual1.1988967381689757e-14; maximum known-point relative error1.143004552117688e-9 (limit1e-6); maximum scaled factor-growth ratio1.9566103430244413 (limit1e8). Stored L/U/F stays below5M. Every warm/measured endpoint passed the original normwise tolerance min(1e-10,128*n*eps64), with finite output, unchanged CSC/RHS hashes and deterministic within-arm output hashes. No tolerance was raised or coefficient dropped.

Both caller-value poisoning tests passed; input CSC indices/values are owned by the chosen constructors as checked from source. Both singular attempts threw SingularException. Different backend endpoints need not be bit-identical; no full original-model certificate, update chain, callback/recovery ownership, copy lifecycle or public solver equivalence was tested.

Literal executed budget:196 factor attempts (192 main successes,2 ownership successes,2 expected singular attempts),8522 FTRAN,4272 BTRAN,24 cold qualifications,48 warm and120 measured samples. No reference factor or solve was added.57 launch pins unchanged; actual loaded KLU/UMFPACK/AMD/COLAMD/BTF/SuiteSparse-config paths/hashes checked.25 resource samples, minimum available RAM22,162,376KiB, swap0; all713 historic/new groups AND sessions absent, no Julia after exit.

## Without block structure

“No blocks” means one irreducible diagonal block after matching and SCC/BTF, not simply a visually unstructured sparse matrix. KLU then orders the whole block with AMD (or COLAMD if selected) and applies the same sparse left-looking Gilbert–Peierls factorization with its numerical partial pivoting. Off-block F is empty; KLU does not automatically switch to UMFPACK or change solver tolerances. A zero-free structural diagonal is not a proof of numerical nonsingularity.

With one block, forward solve applies row permutation/scaling, solves L then U, and scatters by column permutation; transpose solve applies the reverse/transposed sequence (Uᵀ then Lᵀ, with corresponding permutations/scaling). With multiple blocks, triangular substitution also propagates the separate F couplings. All of that work remains in the native solve.

The sparse-cycle256 control has one256-row block and F=0: KLU factor ratio0.659, triplet ratio1.007 (range0.918–1.100), so lack of block separation does not itself make KLU unsuitable. The dense256 one-block control also has F=0: KLU factor ratio2.302 (range2.164–2.382), BTRAN1.500 and native retained bytes1.938x. UMFPACK's multifrontal dense kernels can be a better fit there; one-block dimension alone cannot select a backend. Both controls are small, synthetic and well-conditioned, not universal bounds.

## Decision and next step

Keep UMFPACK as the production default. KLU merits an optional base-backend qualification on runtime-like sparse problems because build and many forward solves improve, but slower BTRAN, increased retained native memory and fast-case fill/solve regressions prevent universal replacement. A later same-exchange whole-cycle comparison must include basis updates and refactors. Do not yet convert KLU L*U+F into the current direct SS multiplicative export: transformed couplings can introduce the fill/work being avoided. Graph-local SS remains a separate open design.

Initial admission rejection (wrong KLU Rs order), its preserved driver/plan, one source correction and subsequent order correction are retained with all review/pin versions. No failed Julia run or numerical retry occurred. Original45 read-time bindings map changed driver/plan only to driver.before-review.jl/PLAN.before-review.md; the51-binding corrected manifest maps its driver only to driver.after-scaling-fix.jl.55 reviewed and57 launch bindings map the executed source. The early correction-only acceptance is not the final launch admission; REVIEW-ADMISSION-ORDER-FINAL.md is.

No unnecessary NEW production work or memory was introduced. The cold diagnostic duplicate extraction/scans are explicitly identified rather than credited as kernel savings. Whole-solver performance, native free accounting, integration, other precisions and general backend selection remain unqualified.
