# Realistic basis blocks, affected regions, sparsity and cost

**Actual bases have substantial exploitable block structure, and sampled update cycles are much smaller than the index intervals traversed today.** On the runtime histories, the largest irreducible basis blocks contain3,675–4,666 of28,453 rows, while median spiked-factor irreducible blocks contain roughly245–405 vertices versus rotation intervals around7,842–8,789 positions. This supports investigating block-preserving factorization and graph-local updates together with fill reduction. It is structural evidence, not a proved operation-skipping rule or a whole-solver speedup.

Completed one new guarded process in167.15s:2,703 ordinary Test assertions,32 passing cold trajectories,160 measured windows and51 offline gates. All76 saved structural witnesses independently verified;101 launch pins unchanged; no Julia remains. No new LP solve, production/permanent-test/environment/master/CI change. All older accepted evidence preserved and not rerun.

User preference: modestly favor elapsed time over allocations. Assessment therefore reports time/bytes/events/retained graph as separate tradeoffs; higher allocations alone do not automatically reject a faster valid component. No production default or integration is inferred.

## Actual recorded exchanges

Use the first160 accepted exchanges from three previously captured2560-step PFI/native/legacy histories: runtime at iterations30,036 and40,036 and fast0507 at1,040. The stored internal matrix and exact leaving/entering index pairs are replayed identically across modes. Early-medium is a separate mostly-permutation structural control only, with no new large-medium factorization/timing. Artificial columns retain the original negative-identity convention. Binary tapes and matrices stay local and are not redistributed.

History and original MPS hashes match the allowlist; source capture settings are historical metadata/source declarations, not a new capture of the current master trajectory. The historical capture checked matrix identity and published basis indices but did not independently certify phase homogeneity. These results describe well-defined fixed-matrix algebraic replays, not reproduction of a complete historical LP run or hidden numerical trajectory.

## Blocks in the actual basis B

Nonzero perfect matching exposes a zero-free structural diagonal, then iterative strongly-connected-component decomposition gives block triangular form. Exact zeros only; no coefficient removal/tolerance. Pairing is structural and does not choose or approve numerical pivots.

| History | Rows | Largest block at0/80/160 | Singleton blocks at0/80/160 |
|---|---:|---:|---:|
| runtime-30000 | 28453 | 3767 / 3833 / 3675 | 21758 / 21718 / 21699 |
| runtime-40000 | 28453 | 4603 / 4666 / 4589 | 20688 / 20717 / 20763 |
| fast0507-1000 | 484 | 228 / 260 / 260 | 251 / 224 / 224 |
| medium-early | 360982 | 1 / 1 / 1 | 360982 / 360982 / 360982 |

The largest block is not the whole coupled core. Runtime30000 initially also has371 other nonsingleton blocks; runtime40000 has481. Total nonsingleton dimensions are6,695 and7,765 respectively. Coupling entries BETWEEN blocks are63,346/125,743 and69,375/135,304, about50–51% of initial basis NNZ. They still require storage, updates and triangular propagation; discarding the singleton periphery is not justified.

All three sampled medium bases have singleton blocks, condensation depth2 and6,000→6,480 coupling entries. They are permuted triangular, not diagonal; this early control says nothing about later medium behavior. Fast0507 still contains a substantial228–260-row irreducible block despite its484-row dimension.

Permutations preserve NNZ(B); they expose existing decomposition. A genuinely irreducible block cannot be split merely by rearranging its rows and columns. Changing which columns belong to the simplex basis is a separate trajectory-changing strategy, not tested here. The goals within a fixed basis are reduced factor fill and preservation of useful structural locality across exchanges.

## Regions created by an entering column

U alone is already triangular, so SCC analysis of it would be trivial. Instead inspect the SPIKED U before replacement at exchanges1,17,...,145. General matching handles zero spike diagonals; most samples have one, making the earlier zero-free-diagonal-only probe insufficient. All320 sampled profiles passed matching/SCC checks.

| History/backend | Mode | Interval | Median largest spiked block | Median rotation interval | Structurally permutation-triangularizable samples /10 |
|---|---|---:|---:|---:|---:|
| runtime-30000/native | SS | 80 | 245.5 | 7843 | 1 |
| runtime-30000/native | SS | 160 | 313 | 8097 | 1 |
| runtime-30000/native | BG-local | 80 | 245 | 7843 | 1 |
| runtime-30000/native | BG-local | 160 | 313 | 8097 | 1 |
| runtime-40000/native | SS | 80 | 292 | 8711.5 | 3 |
| runtime-40000/native | SS | 160 | 404 | 8711.5 | 3 |
| runtime-40000/native | BG-local | 80 | 292 | 8711.5 | 3 |
| runtime-40000/native | BG-local | 160 | 404.5 | 8711.5 | 3 |
| fast0507-1000/native | SS | 80 | 18 | 173.5 | 2 |
| fast0507-1000/native | SS | 160 | 5 | 200 | 5 |
| fast0507-1000/native | BG-local | 80 | 14 | 172 | 3 |
| fast0507-1000/native | BG-local | 160 | 1 | 193 | 6 |
| fast0507-1000/markowitz | SS | 80 | 1 | 117 | 6 |
| fast0507-1000/markowitz | SS | 160 | 1 | 193 | 7 |
| fast0507-1000/markowitz | BG-local | 80 | 1 | 115.5 | 6 |
| fast0507-1000/markowitz | BG-local | 160 | 1 | 191.5 | 7 |

The large gap is a concrete reason to investigate localized transformations by dependency graph, especially for SS. However, SCC size is not the number of safe-to-skip operations: matching can permute rows/columns, elimination can change couplings, and factor/history/cache mappings must remain correct. Structural permutation feasibility is not numerical acceptance, a count of unnecessary existing multipliers, or an estimate of future time savings. Applying a permutation could change subsequent fill and opportunities.

On fast0507, Markowitz often yields singleton spiked blocks where native produces larger ones. Backend differences include different numerical pivot policies as well as factor ordering/representation; this experiment does not isolate ordering alone or prove Markowitz better on the large runtime bases. Markowitz was timed only on fast0507.

## Joint sparsity and structure: a measured example

For runtime40000/native/interval80, original BG versus endpoint-localized BG has:

| Metric | Original BG | Localized BG |
|---|---:|---:|
| Maximum sampled U NNZ | 218,094 | 219,696 |
| Final stored history entries | 31,560 | 24,854 |
| Maximum sampled stored factor/history entries | 378,305 | 373,392 |
| Final reachable graph bytes | 23,337,272 | 22,255,664 |
| Median whole160-exchange cycle | 799.0ms | 716.6ms |

The paired median time ratio is0.883, range0.880–0.955. U alone grows about0.7%, but history, combined stored entries, bytes and elapsed time decrease. This is the reason to optimize structural work and total factor/history storage jointly rather than force U NNZ to fall at every change. Sampled maxima are from16-step checkpoints, not continuous peak measurements. Production storage counts include BG transformation records and normalization data, not only mathematical nonzero matrix coefficients.

## Whole-cycle timings on real sequences

Each cell has one qualification replay,one warm replay andfive measured arm rotations. Intervals80/160 have one/no mid-cycle refactor; no final reset hides the aged endpoint. Whole timing includes initial AND scheduled basis assembly, initial factor/export/normalization, entering column/unit-RHS preparation, basis tracking, two FTRAN+one BTRAN per exchange, replacements, buffers, finite guards, midpoint copy and uniform nested API timers. Ordinary auxiliary FTRAN preserves the production cache eviction schedule uniformly without unused update-payload copies. Graphs, residuals, fresh references, final fingerprints and graph-size traversals are detached.

| History/backend | Interval | SS ms | FT ms | BG ms | BG-local ms |
|---|---:|---:|---:|---:|---:|
| runtime-30000/native | 80 | 512.28 | 525.52 | 677.88 | 617.12 |
| runtime-30000/native | 160 | 457.02 | 482.09 | 692.53 | 632.01 |
| runtime-40000/native | 80 | 578.91 | 621.34 | 799.02 | 716.58 |
| runtime-40000/native | 160 | 605.52 | 572.70 | 796.79 | 786.39 |
| fast0507-1000/native | 80 | 7.75 | 7.66 | 11.58 | 10.91 |
| fast0507-1000/native | 160 | 8.26 | 9.03 | 14.41 | 12.50 |
| fast0507-1000/markowitz | 80 | 5.50 | 6.03 | 7.21 | 6.43 |
| fast0507-1000/markowitz | 160 | 6.16 | 6.61 | 9.25 | 7.49 |

Independent medians must not be summed or divided to replace paired-ratio statistics. The raw summary.csv retains every mode, interval, stage, allocation count and range.

| History/backend | Interval | BG-local/BG paired median (range) | Bytes ratio | Events ratio | Final graph ratio |
|---|---:|---:|---:|---:|---:|
| runtime-30000/native | 80 | 0.912 (0.879–0.935) | 0.954 | 0.999 | 0.907 |
| runtime-30000/native | 160 | 0.920 (0.899–0.928) | 0.934 | 0.997 | 0.901 |
| runtime-40000/native | 80 | 0.883 (0.880–0.955) | 0.974 | 0.999 | 0.954 |
| runtime-40000/native | 160 | 1.005 (0.885–1.056) | 0.964 | 1.000 | 0.948 |
| fast0507-1000/native | 80 | 0.930 (0.473–0.985) | 0.946 | 0.985 | 0.928 |
| fast0507-1000/native | 160 | 0.880 (0.851–0.908) | 0.912 | 0.968 | 0.871 |
| fast0507-1000/markowitz | 80 | 0.884 (0.857–0.949) | 0.947 | 0.995 | 0.803 |
| fast0507-1000/markowitz | 160 | 0.813 (0.724–0.846) | 0.938 | 0.991 | 0.881 |

Localized BG shows7–19% paired-median whole-cycle improvement in seven groups with all five ratios below1; runtime40000/160 remains inconclusive. This is smaller than the38–47% improvement on the artificial block fixture. Allocation traffic and retained graph also decline. The localized candidate still does not demonstrate superiority to SS/FT; those remain the relevant faster references for a speed-first decision. General realistic results therefore do not justify making BG the default.

Longer interval160 reduces allocation bytes/events in SS but increases retained history/graph. Its timing effect is mixed: SS160/80 paired medians are0.884(runtime30000),1.051(runtime40000),1.065(fast native),1.119(fast Markowitz); the first three ranges cross1. The fast Markowitz interval80 is faster despite more allocations. A modest preference for speed allows such tradeoffs when meaningful, but does not select a universal interval. The production default20 and adaptive-controller policy were not exercised.

## Diagnostic overhead and uncertainty

All160 measured compile/recompile fields are zero.72 measured windows contain GC,total2.759085s; all are retained, including the fast-native80 BG outlier reflected in the paired range. Detached post-window hashing and graph-size allocation can influence subsequent GC; this is not observer-neutral kernel timing. Five repetitions, one process and three selected160-step tape prefixes limit inference.

Full matching/SCC analysis of each runtime spiked factor costs roughly4–6ms per sampled profile and about9MiB of scratch allocation. This is comparable to the per-exchange whole component workload and cannot simply be inserted before every update. The first engineering requirement is to reuse maintained incidence/matching/dependency information or analyze at refactors, accounting for invalidation, merge/split handling and copy ownership. A new full graph rebuild per pivot would likely move or increase the work.

Largest-block NNZ refers to the FIRST block attaining maximum dimension, not necessarily the densest tied block. Largest spiked block and rotation span are structural proxies from different representations; neither certifies arithmetic savings.

## Correctness, provenance and resources

Every cold16th exchange validates the entering direction before update and F/B solves against the actual new basis, full logical U triangularity, normalized-U1e8 guard and5-million active-factor-entry budget. At80/160, all checks occur at full age BEFORE reset and additionally pass directed256-bit residual enclosures plus independent fresh-native references. Backward filter=min(1e-10,128*n*eps64), scaled by max(1,||B||infinity*||x||infinity,||rhs||infinity), using ||B||1 for transpose. Fresh relativeinfinity agreement limit1e-6. Maximum recorded ordinary normwise residual is1.572e-15; directed residual magnitudes and fresh differences were not separately saved, only gate success. Backend precision, pivot rules and tolerances remain unchanged.

Hot final factor/history/output/midpoint fingerprints match their own cold arms and input hashes remain unchanged. Selected RHS checks do not establish all-RHS accuracy, conditioning, original-LP certificates, hidden hot prefixes, callback/recovery or future copy-mutation lifecycle safety. Existing direct adapters omit native combined-solve iterative refinement, as in their earlier qualification.

Budget:224main cycles,224initial+112scheduled builds=336 main factor/export constructions;35,840updates71,680FTRAN35,840BTRAN. Cold independent references add128fresh LUs and192solves. Measured subset160cycles240builds25,600updates51,200FTRAN25,600BTRAN. Backend/export/orientation internals are additional source-derived work, not a complete observed PREforward/native ledger. Structural analysis comprises320spiked profiles+12actual-B profiles+516sanity calls. Hashing,matching,sorts,matrix/norm scans,diagnostic graph and witness costs are outside hot windows and included in process cost.

All76 saved witnesses(total177,138,176bytes,below512MiB cap) were independently checked in Python and by the reviewer: exact nonzero perfect matching, canonical CSC, component strong connectivity in both directions, acyclic component ordering, dimensions and hashes. The supplied verifier additionally checks depth and detailed summaries. These cover all12Bprofiles and64selected spiked profiles; other256profiles were checked by the independently tested Julia algorithm, not separately reconstructed from saved matrices. Binary witnesses remain local and their hashes/paths are recorded.

Process167.15s inclusive; maxRSS978,128KiB, minimum availableRAM21,928,980KiB, swap0, all guards passed.711 historical/new groups AND sessions absent, no Julia after exit. Reachable graph bytes exclude allocator spare capacity and native memory; processRSS includes compilation/reference/structural diagnostics. Neither is a native retention/free ledger.

## Recommended next design

Prepare a source/design contract for BLOCK-PRESERVING factor order and GRAPH-LOCAL SS updates, with BG-local retained as a comparator. At refactorization, expose real BTF blocks and reduce fill within them under unchanged numerical admission. Compose structural permutations into the existing factor export mappings rather than add extra per-solve permutation passes. Across updates, maintain a conservative affected region including coupling writes, with bounded graph/matching work and original dense/general fallback. Zero-spike-diagonal matching and changes that merge blocks need explicit handling; SCC shrinkage is not assumed free.

The decision target should be whole-cycle time with budgets for total L/U/history entries, reachable/retained memory, metadata and allocations. Permit a modest U-fill increase when it yields cheaper transformations and solves, as the measured example demonstrates. Do not use NNZ(B), bandwidth, or maximum block dimension alone as the score. BTF analysis does not by itself implement a faster numerical factorization, and this step did not implement a new ordering/pivot heuristic or graph-local kernel.

This investigation supports a larger structural change instead of another blind full scan or storage-only tweak. Numerical safeguards take precedence; no production promotion follows. No unnecessary NEW production work/memory was introduced. The avoided original-BG region/history work is supported by realistic timings and allocations, while the expensive graph machinery remains diagnostic only.

Evidence: results-1.toml,analysis-1.json,summary.csv,witness-verification.json,PLAN.md,101 launchpins,admission and result reviews. Postexit analyzers are not launchpins. Source/runtime/capture limitations are preserved; no earlier scripts/raw or user changes were overwritten.
