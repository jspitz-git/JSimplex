# Direct FT/SS/BG: long replacement chains

All 24 Float64 combinations passed ordinary Test 760/760 and 41 offline acceptance gates. The qualified process exited0 in28.03s; no Julia remains. No production, test, environment, CI or master change. This is a synthetic factor-component comparison, not a public LP solve or production admission.

The strongest signal is structural: SS reduces history and total work on linked blocks; it offers no clear advantage on the other three patterns. BG is slower in every measured group. All three allow the banded input to produce a completely populated triangular U under a deliberately long common refactor interval. Smaller storage-layout changes do not address that behavior.

## Whole-cycle timing

Five measured rotations after one warm rotation per fixture/backend, same256 replacements and one actual refactor at128. Times include starting factor/export/normalization, fresh direction/FTRAN/BTRAN and midpoint buffers, updates, enteringFTRAN plus RHSFTRAN/BTRAN, refactor, finite guards and uniform nested timers. Cold structural/oracle work and endpoint graph/fingerprint checks are detached. All 120 measured compile/recompile and in-windowGC values are zero.

| Input | Backend | FT ms | SS ms | BG ms | SS/FT paired median (range) | BG/FT paired median |
|---|---|---:|---:|---:|---:|---:|
| band | native | 9.088 | 9.650 | 20.558 | 1.044 (0.746–1.135) | 2.317 |
| band | markowitz | 8.067 | 8.160 | 18.841 | 1.009 (0.972–1.123) | 2.329 |
| blocks | native | 4.873 | 3.261 | 9.691 | 0.650 (0.601–0.963) | 2.006 |
| blocks | markowitz | 4.948 | 3.350 | 9.775 | 0.677 (0.671–0.693) | 1.951 |
| sparse | native | 9.415 | 9.387 | 22.060 | 0.966 (0.928–1.146) | 2.343 |
| sparse | markowitz | 8.877 | 9.350 | 20.926 | 1.036 (0.877–1.168) | 2.343 |
| dense | native | 9.432 | 9.871 | 21.941 | 1.048 (0.923–1.081) | 2.326 |
| dense | markowitz | 9.582 | 9.443 | 21.690 | 1.016 (0.980–1.075) | 2.314 |

On linked blocks SS saves35.0%/32.3% of whole-cycle time by paired medians (native/Markowitz), with all five ratios below1. Other SS ratio ranges cross1. BG paired medians range1.951–2.343; its lower event count does not imply less allocation traffic or faster work. One process, five short repetitions and64-dimensional dyadically dominant synthetic bases support a local finding only.

## Fill and retained work

| Input/backend | Manager | Initial U nnz | U at128 before/after refactor | Final U nnz | Stored history scalars at256 | Maximum storage/baseline ratio | Final reachable KiB |
|---|---|---:|---:|---:|---:|---:|---:|
| band/native | FT | 181 | 2080/301 | 2080 | 6920 | 20.50 | 778.8 |
| band/native | SS | 181 | 2080/301 | 2080 | 6920 | 20.50 | 779.8 |
| band/native | BG | 181 | 2080/301 | 2080 | 6979 | 20.60 | 1139.9 |
| band/markowitz | FT | 181 | 2080/301 | 2080 | 6837 | 20.28 | 773.0 |
| band/markowitz | SS | 181 | 2080/301 | 2080 | 6837 | 20.28 | 774.1 |
| band/markowitz | BG | 181 | 2080/301 | 2080 | 6853 | 20.42 | 1136.6 |
| blocks/native | FT | 300 | 1184/297 | 1184 | 3569 | 7.77 | 408.5 |
| blocks/native | SS | 300 | 1120/297 | 1128 | 1981 | 5.27 | 252.2 |
| blocks/native | BG | 300 | 1184/297 | 1184 | 5462 | 10.65 | 758.3 |
| blocks/markowitz | FT | 295 | 1184/293 | 1184 | 3498 | 7.76 | 417.9 |
| blocks/markowitz | SS | 295 | 1248/293 | 1464 | 1959 | 5.82 | 256.2 |
| blocks/markowitz | BG | 295 | 1184/293 | 1184 | 5395 | 10.69 | 743.7 |
| sparse/native | FT | 940 | 2080/973 | 2080 | 6896 | 5.50 | 838.5 |
| sparse/native | SS | 940 | 2080/973 | 2080 | 6896 | 5.50 | 839.5 |
| sparse/native | BG | 940 | 2080/973 | 2080 | 6918 | 5.52 | 1090.0 |
| sparse/markowitz | FT | 946 | 2080/975 | 2080 | 6778 | 5.08 | 812.6 |
| sparse/markowitz | SS | 946 | 2080/975 | 2080 | 6778 | 5.08 | 813.6 |
| sparse/markowitz | BG | 946 | 2080/975 | 2080 | 6810 | 5.10 | 1101.1 |
| dense/native | FT | 2072 | 2080/2072 | 2080 | 7069 | 2.70 | 871.5 |
| dense/native | SS | 2072 | 2080/2072 | 2080 | 7069 | 2.70 | 872.5 |
| dense/native | BG | 2072 | 2080/2072 | 2080 | 7069 | 2.70 | 1067.4 |
| dense/markowitz | FT | 2071 | 2080/2071 | 2080 | 7019 | 2.69 | 863.5 |
| dense/markowitz | SS | 2071 | 2080/2071 | 2080 | 7019 | 2.69 | 864.5 |
| dense/markowitz | BG | 2071 | 2080/2071 | 2080 | 7020 | 2.69 | 1091.2 |

At64 dimensions the full triangular envelope has2080 positions. For the band input all three grow from181 U nonzeros to2080, and remain at2080 after the explicit basis returns exactly to its original columns. The first storage-ratio8 crossing occurs at49 updates with native and51 with Markowitz. The basis itself remains sparse; this is factor/history fill, not densification of B. A production adaptive fill controller could refactor sooner; this component replay deliberately holds the common128 schedule and is not a measurement of that controller. Cold numerical growth/residual and original pivot checks remain mandatory.

For linked blocks SS ends with1981/1959 stored history multipliers versus FT3569/3498; median spike endpoint minus leaving position is18/23 versus57. Its allocation traffic is lower by33.6%/32.0% and final reachable graph by38.2%/38.7%. Its median update time is1.046/1.037ms versus FT1.722/1.709ms and BG6.388/6.446ms. FTRAN also falls from2.418/2.424ms to1.581/1.631ms. The common constructor/refactor work is small. This is reduced retained transformation work, not merely a transfer of costs into preparation.

Crucially, Markowitz/blocks SS ends with1464 U nonzeros versus FT1184, yet still runs faster with a smaller whole retained graph. U nnz alone is an insufficient optimization target: include transformation histories, their application, and indexing work. BG retains a larger reachable graph in every group and spends most of its excess time inside replace_column!, rather than setup or factor solves.

## Correctness, ownership and work budget

Inputs are64×64, exact dyadics, four patterns and three variants per column. Every basis is row/column strictly dominant with diagonal8 and offdiagonal integer/512;128 forward replacements are followed by their exact inverse sequence. Native threshold_one and Markowitz default policies are unchanged. Initial lower/U/permutation/scaling fingerprints match across all3 managers within each backend. Only actual normalized direct mode is allowed; Float32 generic fallback is excluded. Input Float64 arrays and relevant index/sequence metadata remain hash-identical.

Cold passes check all512 entering/RHS forward solves and256 transpose solves per cell against explicitly selected input columns using independent directed BigFloat256 enclosures. The historical128*n*eps*max(1,||B||inf*||x||inf,||rhs||inf) bound is preserved (using ||B||1 for transpose solves); factor arithmetic and tolerances are not raised. A cold guard on the normalized U magnitude (not a conditioning certificate) and original finite/pivot checks stop invalid paths. All hot endpoint/history/output fingerprints and midpoint outputs match the corresponding cold run; final forward and transpose residuals are independently rechecked. Hot prefixes are not fully captured, so this is not an observer-neutrality or hidden-trajectory proof. The tested residual bounds passed, but residual magnitudes were not stored. No failures occurred in the qualified numerical run.

Across cold+warm+measured:168 replay starts,168 scheduled refactors (336 underlying basis-build/export/normalization operations),43008 replacements,86016 FTRAN and43008 BTRAN entries. Measured subset:120 starts+120 refactors,30720 replacements,61440 FTRAN and30720 BTRAN. Backend export/scaling/orientation and Markowitz internal work are additional source-derived work, not a complete instrumented PREforward/native ledger. Cold graph and directed oracle allocations are reported separately and not attributed to factor performance.

Allocation events/bytes and all stage medians are in summary.csv and analysis-1.json. Reachable graph bytes from Base.summarysize exclude allocator spare capacity and native memory; they are not peak live memory or a full free/retention ledger. Whole-process peakRSS717216KiB includes Julia/compiler/oracles/traces and cannot be assigned to an individual manager. Minimum availableRAM22109508KiB, swap0; all guards passed.

## Next decision

Prioritize preserving the limited affected region of SS on block-structured bases. Before a new heuristic or storage rewrite, verify that this advantage persists on recorded realistic exchange sequences and with a shared earlier refactor schedule compatible with the existing fill criterion. The band result argues for structural/refactor organization rather than another buffer micro-optimization. Do not promote SS globally from this dataset, and do not pursue another BG storage tweak on the assumption that it resolves the measured update cost. No new numerical run or implementation is part of this record.

## Evidence and preserved failure

Canonical admitted run: comparison-2 with driver-2.jl/command-2.json/pins-2.json (99 pins). The first comparison-1 stopped on a comprehension parse error before fixture/sequence execution; its driver, original reviews, pins and raw exit1 log remain unchanged. SYNTAX-FIX and independent REVIEW-SYNTAX record the two whitespace-only fixes. Qualified run Test760/760, offline analysis41/41, source pins unchanged, all historical and new groups/sessions absent after exit. The analyzer was written after launch; it is a postexit analysis tool, not a launch pin.

Final independent result review and publication records accompany this report. All current and previous evidence is preserved; no old scripts or accepted measurements were rerun.
