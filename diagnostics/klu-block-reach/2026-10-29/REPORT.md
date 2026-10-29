# Actual-RHS reach in KLU blocks and a practical fixed-base boundary

**There is a substantial coefficient-work opportunity for entering-column FTRAN on runtime, but little on fast0507. A fixed-base FTRAN boundary can use a graph unchanged between refactors, avoiding the need to maintain a new BTF at every pivot.** Plain block-skipping BTRAN has a smaller opportunity than its block counts suggest; a stronger BTRAN model requires a reverse coupling index and is not an admission for the base RHS after update history.

Completed one new guarded diagnostic process in23.16s:7405/7405 ordinary Test assertions,483 fresh KLU factors,483 combined native extractions,483 matrix-identity probes,zero basis solves and zero timing-benchmark windows. Independent Python recomputation verified all483 binary graph records/966 actual RHS and their weights/classification. A separate offline pass evaluates1449 fixed-base entering-RHS scenarios at hypothetical fixed refactor intervals20/80/160. No new Julia run, factor, solve or timing was needed for that pass.

Baseline diagnostic04c211565976a47cb1e151629c9ed77f5db99618, master c0fa748ffa61ccb7c1caaf248c40324f60bc737b. No src/permanent-test/environment/CI/master changes or graph-local solve/update implementation. Earlier measurements and evidence remain frozen.

## Inputs and interpretation

Use161 consecutive pre-exchange bases (states0..160) from EACH of the same runtime-30000, runtime-40000 and fast0507-1000 captured tapes. At state k the real next entering column and leaving basis-position unit RHS come from step k+1. Binary hashes match; negative-identity artificial columns follow the capture. No repeated/padded exchanges, new LP/MPS solve or medium factorization. This is a fixed internal-matrix algebraic replay, not a current-master simplex trajectory or newly proved phase-homogeneous capture.

KLU2.3.5 uses the previously qualified exact source/library identity and tol1/BTF/AMD/row-sum/maxwork10 settings. A single combined `_extract!` gets L/U/F/P/Q/R/Rs per factor, replacing separate diagnostic property extractions; native source unchanged. All nine0/80/160 anchors exactly reproduce earlier accepted B hashes, separate L/U/F entry counts, block count and largest block dimension. Full block-size vectors were not saved by that older study and are not claimed as anchor evidence.

A graph node is an irreducible block. Each stored F coefficient is one edge from its column block to an earlier row block; exact-zero coefficients are marked and do not create reach, duplicates remain and their traversal is charged. FTRAN starts in blocks of the entering RHS's original nonzero rows (map P). BTRAN starts from the leaving basis-position column (map Q) and traverses reversed edges. Confusing P/Q or merely counting blocks would give the wrong result.

## Current-basis structural opportunity

Fractions are medians over161 queries, percent of full work/storage domain. The block-only work model counts L/U offdiagonal slots plus U diagonal divisions and all F column slots in reached blocks. It excludes the implicit L unit diagonal. The alternate edge-aware BTRAN model additionally avoids couplings from unreached source blocks, requiring reverse incidence. These are coefficient/division visit counts supported by native source, not equal-cost flops, observed machine-instruction counts, elapsed time or whole-solver savings.

| History / RHS | Blocks reached | Rows reached | L/U work reached | Block-only coefficient work | With edge-aware F |
|---|---:|---:|---:|---:|---:|
| runtime-30000 / FTRAN | 15.9% | 25.4% | 59.3% | 45.0% | 45.0% |
| runtime-30000 / BTRAN | 19.0% | 35.2% | 78.7% | 83.0% | 58.5% |
| runtime-40000 / FTRAN | 18.1% | 29.7% | 72.8% | 57.7% | 57.7% |
| runtime-40000 / BTRAN | 21.1% | 39.1% | 85.0% | 86.2% | 67.1% |
| fast0507-1000 / FTRAN | 41.6% | 72.1% | 98.3% | 92.5% | 92.5% |
| fast0507-1000 / BTRAN | 47.6% | 75.0% | 98.4% | 98.5% | 93.5% |

Runtime FTRAN can structurally omit about42–55% of this coefficient-work model. For BTRAN, skipping roughly79–81% of block nodes omits only14–17% of block-only work: the small reached set includes the expensive core. The reverse-index edge-aware model could omit33–41%, but its lookup/index maintenance is additional work. Fast0507 retains98% of L/U work and93–98% of total work in the ordinary block model, so it is a poor first target. Fully supported dense RHS reaches every block and gives no such block-elision saving. Auxiliary weight/cost/certificate RHS are outside the captured query coverage.

Runtime FTRAN dependency discovery itself visits median12,224/13,279 F slots per query; BTRAN reverse discovery14,369/16,556. Those are extra graph passes unless fused/reused with numeric processing. The avoided coefficient scans therefore cannot all be credited as net work removed. Factor coefficient types, division versus multiply/subtract cost, memory locality and branch costs differ. Full-vector preparation/gather/scatter/clearing and existing numerical residual/finite checks remain. Exact structural reach does not prove bitwise signed-zero, exception, alias or callback behavior of a future skipped-arithmetic implementation.

## Why a fixed base is the useful first boundary

The ordinary PFI and triangular FT/SS/BG source calls `_backend_forward_solve!(..., factor.base, source)` BEFORE applying eta/row-update history and later upper solves. The source can therefore remain the original sparse entering column at the FULL base-backend boundary. The base matrix and its own permutations/scaling stay fixed until refactorization: a dependency graph may be built once per new base and does not require per-pivot SCC maintenance. This is a source-backed boundary for ordinary full-base wrappers, not proof for the private DirectLowerBackend (which solves only its extracted lower part) or every alternate hypersparse/controller route. Post-base updates and safeguards remain fully charged.

We reused the saved graphs for bases at fixed schedules and applied each subsequent actual entering support through that base's ORIGINAL row map. This tests the input-side locality relevant to such an optional KLU full-base backend without implementing or replaying an update chain. The refactor intervals20/80/160 are scenarios, not captured current-master/adaptive refactor events.

| History | Interval20 FTRAN work reached | Interval80 | Interval160 |
|---|---:|---:|---:|
| runtime-30000 | 44.5% | 42.3% | 42.2% |
| runtime-40000 | 58.3% | 57.2% | 57.1% |
| fast0507-1000 | 92.7% | 92.7% | 88.2% |

The runtime opportunity survives fixed bases: approximately42–58% of modeled coefficient visits remain, so42–58% could be omitted before added bookkeeping. It is not just an artifact of refactorizing every sampled current basis. A future candidate should obtain support during existing RHS assembly or use call-local validated support metadata; an additional full-vector scan solely to discover sparsity would spend part of the saving. Dense/unknown support should retain the general path.

BTRAN is different. Ordinary PFI and triangular source applies transposed eta/row-update history (and upper solves/permutations) BEFORE calling the full base transpose solve. An outer unit RHS need not still be unit or sparse there. Thus the current-basis unit-BTRAN numbers do not establish a base-backend BTRAN optimization. Capturing/deriving that transformed support would be a different experiment; do not hand off the outer unit label unchanged.

## Dynamic update and scaling constraints

| History | Next columns preserving OLD upper partition /161 | Coupling-only changes with fixed maps/scales /161 | Changed canonical column partition /160 transitions |
|---|---:|---:|---:|
| runtime-30000 | 23 | 1 | 138 |
| runtime-40000 | 42 | 0 | 114 |
| fast0507-1000 | 113 | 25 | 59 |

Preserving the old partition means no changed entry lies below the old diagonal block; it can still split an internal block. A new backward coupling can require reorder/merge. Token changes compare canonical groups of original basis-column positions, not arbitrary numbering of native blocks; the count does not measure every participating column or row ownership. The first two columns predict all161 next exchanges; partition comparisons have only160 captured successors.

At least one row's absolute column contribution changes in161/161 runtime30000,155/161 runtime40000 and161/161 fast queries. Recomputing native row-sum scales may therefore change factors outside the nominal block. Coupling-only classification is conditional on fixed maps/scales, not permission to update only KLU.F or reuse native numeric factors. KLU.F is an extracted copy; modifying it does not update the native factor. A block-native SS representation needs separate update/merge/scaling/ownership proofs. The fixed-base FTRAN route avoids those dynamic-structure obligations because only its RHS changes.

## Memory and diagnostic cost

Typed payload for both-direction CSR plus original-row/column block maps and block weights is median2.196MiB(runtime30000),2.275MiB(runtime40000),28.85KiB(fast). This excludes queue/stamps, vector/object headers, retained capacity, L/U/F values and the native factor. A forward-only design can omit reverse incidence, but exporting owned factors while retaining native numeric storage can duplicate factor memory. It must be budgeted explicitly; these payload counts are not a complete candidate memory footprint.

The analysis intentionally rebuilds native factors and graphs at all483 bases and serializes253.48MiB of primitive witnesses locally. That is a finite diagnostic, not work to add at every production pivot. Local factor/export references are released on function return, with GC every8 states; primitive result records retain no factor. No allocation or speed comparison is inferred from the23.16s process duration.

Guard: one Julia/BLAS thread, heap hint2GiB, VM cap8GiB,23 samples, minimum available RAM22,194,232KiB, swap0; last sampled HWM560,772KiB/VM peak935,484KiB. All715 historic/new groups AND sessions absent and no Julia afterward. Library paths/hashes and53 launch bindings unchanged. Maximum factor-identity relative error1.0408340855860843e-15; this validates exported identities at one deterministic vector per base, not a complete original-model certificate or a new sparse solve.

## Verification and recommendation

Ordinary Test covers graph closure against independent Floyd on all3-vertex upper DAGs/all seed subsets/both directions, zeros/duplicates, update classification, all483 factor identities/block structures, nine anchor sets and immutable inputs. Independent Python parses every local witness, checks dimensions/maps/acyclic direction/flags and recomputes all966 queries, weights, update classes, canonical partitions and exact byte totals. The separate fixed-base pass reads the same immutable witnesses and produces1449 scenario records; no old script or numerical process was rerun. Source boundary reads are postexit evidence, explicitly not retroactive launch pins.

Prioritize a bounded graph-local ENTERING-COLUMN FTRAN candidate at a fixed full-KLU base boundary on runtime-like problems. Keep generic BTRAN and dense/unknown RHS paths initially; do not first attempt a dynamically maintained block-native SS manager or prioritize fast0507. Before implementation, specify support ownership/alias invalidation, complete solve/gather/reset costs, native/exported factor duplication and fallback numerical behavior; then measure whole calls and component cycles under unchanged safeguards. None is admitted by this work-count result alone.

No unnecessary NEW production work or memory was introduced. The source-backed FTRAN opportunity removes coefficient traversals in principle, but pays extra reach/index work and must preserve the other costs. Overall performance work, graph-local SS updates, backend integration and full-solver speedup remain open.
