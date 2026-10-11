# S3 static support inventory (partial; no performance acceptance)

Inspected production: master4143dad, architecture production8701a58. This is
read-only preparation while S0 medium-dual-counted-1 owns the sole numerical
process. No additional Julia job or production change. The parent S3 inventory
checkbox remains open until manager/consumer mapping and measured counts finish.

Let m denote basis rows, n structural columns, N=m+n working variables,
s the live support size, and k the update-chain length. Bounds below describe
source loops, not measured operation counts or a demonstrated saving.

## Existing ownership and invalidation

IndexedVector owns dense values, an index list and generation-stamped membership.
set_entry! converts and verifies finiteness before publishing membership; exact
zeros are canonicalized. Cancellation can leave zero-valued members until
compact_support!, which scans only the recorded support. clear! touches recorded
support, then advances the generation; rollover clears the full membership array.
load_indexed! rejects aliasing, clears old support and scans every source value.
A coherent partial result is allowed after conversion failure. Preserve these
contracts rather than introducing a second generation framework.

HypersparseWorkspace borrows six existing scratch vectors: row_rhs,row_solution,
rho,tau,tableau_row,pricing_row. Its six validity flags describe each exact owned
value array. _pipeline_changed! invalidates by identity; _pipeline_vector! either
performs a finite/support rebuild over the full vector or compacts known support.
_reset_pipeline_support! preserves existing dense values and only resets metadata.
It has its own generation rollover full clear. Unknown/external vectors cannot
silently borrow another scratch vector's support.

Candidate publication already copies numerical scratch. _copy_hypersparse_cache!
copies valid index lists and reconstructs membership in candidate-owned storage;
row metadata is immutable/shared and mode observations are shared by the live
phase. Matrix mismatch or disabled policy invalidates support. This metadata copy
is additional support-sized work, not elimination of existing dense state copies.
_invalidate_sparse_pricing_scratch! also clears staged scratch recursively.

## Pipeline and manager map

| Boundary | Existing support behavior | Cost / constraint |
| --- | --- | --- |
| Unit/column/BFRT RHS | _pipeline_rhs_buffer! clears valid support, otherwise fills dense values; set/add/subtract maintain exact support | O(old s) or O(m), plus actual column nonzeros/flip contributions. Finite RHS checks remain separate in bound flips. |
| Dense FTRAN/BTRAN output | _pipeline_basis_kernel! invalidates output, then _pipeline_output_support! rebuilds known scratch | One O(m) finite/support pass. External output separately calls all(isfinite) and count(!iszero), potentially two O(m) scans. |
| Indexed FTRAN/BTRAN output | Kernel invalidates before work, publishes valid only on success; output support is compacted | O(s) compaction, with possible repeated compaction inside kernels. Exceptions invalidate output; do not promote partial solve support to an accepted result. |
| PFI | Indexed base solve, eta chain forward/reverse, exact support updates | Per-update support and eta work; :auto may copy all m values to dense after fill, then reload support over m. |
| FT/SS/BG | Indexed base/upper solve, ordered row-update chain and permutations | Sparse graph caches plus work/scratch; chain fill can cause full dense copy and support reload. Preserve manager-specific update ordering. |
| HH | _pipeline_sparse_available! explicitly false; dedicated alias-safe dense solve | HH has no IndexedVector solve interface. Under hypersparse policy output still incurs support reconstruction. Do not claim existing indexed-manager tests cover HH. |
| DenseLUBackend | Pipeline sparse availability false | Dense fallback is required; an exact support handoff would need a separate valid producer contract. |
| Standalone sparse pricing | load_indexed!(rhs,rho), sparse_price!, then copy back to dense tableau row | Full m input conversion and N output copy remain. Hardware slack signs are restored while copying; aliasing may require an RHS copy. |
| Pipeline sparse pricing | Known input/output IndexedVectors, RowAccess lazily constructed | Retains support, but sorts a private copy of input row indices to preserve CSC per-column accumulation order. Noncanonical CSC falls back to full column traversal. |
| Pipeline dense pricing | _csc_price! invalidates output | Subsequent output-density accounting rebuilds N-element support; no reduction order may be changed silently. |

Sparse basis caches own factor snapshots/graphs, indexed work/scratch and dense
fallback buffers. _sparse_working_precision! accounts for new history and dirty
upper metadata, plus RHS stored precision; do not remove these for BigFloat.
Sparse triangular solves compact support before reachability and after updates.
Graph construction/copies and reachability scratch are setup/cache costs, separate
from ordinary repeated support passes. Cache invalidation on refactorization and
upper edits must be completed in the remaining manager-specific inventory.

## Dense consumers after sparse solves

Current update_primals! traverses all m basic variables. update_duals! traverses
all N reduced costs, may perturb objective costs to restore dual feasibility,
and handles leaving/entering entries separately. Skipping exact-zero tableau
entries is not automatically equivalent: that loop also checks and repairs
pre-existing reduced-cost violations and has signed-zero behavior.

DSE update_dse! performs a checked weight FTRAN then updates all m basic weights
with a lower floor. Devex scans all N tableau entries for the reference norm and
then all m basic weights. A zero direction coefficient does not by itself license
skipping a weight floor or validation. Bound flips independently check the RHS,
solved change and every predicted basic value before publication, then traverse
all m basic values. Support reuse cannot replace these numerical obligations.

Incremental primal flip/pivot helpers likewise validate predictions before writes:
primal two m passes, price validation/update N passes, and basic-cost reset m.
They accept dense AbstractVector interfaces and presently consume no exact support
contract. This inventory does not propose enabling their policy flags; S2 guards
and arithmetic changes are separate.

## Validation and next steps

Existing suites cover indexed_vector, hypersparse_factorization/update/pipeline,
allocation/storage/edge/recovery/sequence/overflow, sparse_pricing and signed zero.
Use existing regressions for aliasing, generation rollover, cancellations,
precision retention, candidate copies and sparse-to-dense transitions.

Before selecting a first S3 path, finish invalidation/precision mapping per
manager, enumerate real source writers, and count full support rebuilds/compaction
work on frozen sparse/dense histories. Reuse existing support_rebuilds,
dense_resets and dense_fallbacks counters where they express the exact metric;
separate setup, solves, pricing, value/weight consumers and candidate copying.
No such numerical measurement may start while S0 owns the guard. The controlled
legacy baseline has hypersparse=false: enabling experimental timing-based mode
selection is not an architecture optimization or an acceptable paired baseline.
A new experiment must hold the selection policy fixed and explicitly classify
any arithmetic-order/signed-zero change. Broad S3 acceptance remains pending.

## Independent review additions

Matrix cache matching uses object identity (===), not automatic mutation detection.
An in-place structure/value change to the same A requires explicit invalidation,
including RowAccess stored-precision metadata. Do not infer validity merely from
identical dimensions or a still-matching object address. Owned immutable working
matrix assumptions must be explicit at any new support handoff.

The pipeline also calls _invalidate_prepared_destination! before solve/pricing.
Prepared triangular spike provenance and exact support validity are separate
contracts: preserving one cannot substitute for invalidating the other.

Primal steepest-edge has its own dense consumers: finite checks and dot(h,h)
over m entries, weight BTRAN and pricing, and an N-entry update/validity loop.
When shared_row=false it also computes another unit BTRAN and pricing row.
Primal Devex likewise scans N weights and conditionally builds the shared row.
On-demand primal edge initialization can perform one checked FTRAN per selected
uncached candidate; these solves must not be misclassified as support rebuilds.

For BigFloat HH under hypersparse policy, _hh_stored_precision scans L/U/scaling
and all update coefficients on every scoped solve, plus RHS stored precision.
The indexed managers instead maintain history_scanned and upper_precision_dirty.
This difference is an existing precision safeguard/cost, not evidence permitting
its removal. Base/update immutability and copy/refactorization invalidation would
need a separate reviewed precision-cache contract.

Independent review accepts the partial map after these additions. No runtime work
or memory is introduced by this documentation; no benchmark is needed to review
it. Counts and candidate implementation remain pending behind the sole S0 job.

Manager invalidation anchors: native PFI refactorize! (factorization.jl), Markowitz
PFI refactorize! (markowitz_factorization.jl) and _refactorize_triangular! all set
factor.sparse=nothing after successful reconstruction. Triangular upper edits
call _invalidate_sparse_upper!, which also invalidates the dense upper cache and
marks stored upper precision dirty. _copy_sparse_basis_cache copies independent
indexed/reach/dense scratch while sharing immutable graph coefficients/metadata.
A new result-support cache cannot outlive these factor/shape transitions.


## Concrete scratch writers and invalidation

Additional source inspection at architecture e519fbe (production unchanged).
The direct `scratch.<field>` search was followed through local aliases and generic
`destination` helpers; the search alone is not a completeness proof.

| Writer / boundary | Arrays and frequency | Publication rule |
| --- | --- | --- |
| `simplex.jl recompute!` | row_rhs: dense zero, nonbasic RHS accumulation, then basis costs; each reconstruction | Invalidates row_rhs before both distinct constructions; checked solves own row_solution/rho output metadata. No support survives from the primal RHS into the cost RHS. |
| Pipeline unit/column/BFRT/weight builders | row_rhs; each corresponding solve | Known indexed construction maintains membership. Dense and nonfinite weight paths invalidate; a nonfinite estimate remains visible to the existing weight-reset guard. |
| `dual_simplex.jl _dual_direction_residual_ok!` | tau becomes residual, row_rhs becomes scale; each native direction check | Invalidates both before any write. These arrays no longer contain solved changes/RHS after this call, even if the direction passes. |
| `simplex_recovery.jl refine_basis_solve!` | Generic destination; only accepted correction | Builds trials privately and invalidates after accepted whole-vector copy. Rejected trial leaves that destination result/support unchanged; other recovery scratch is not rolled back. See view qualification below. |
| Native dual correction/refinement | row_rhs, row_solution, rho, tableau_row; recovery | Each accepted copy has explicit invalidation. `_try_native_dual_tableau!` also invalidates the restored old tableau on rejected correction. |
| `legacy_primal_pivot.jl` price recovery | rho; recovery | Private dual/prices are checked before publication, then rho invalidated. Selected pivot rho is not persistent objective-dual metadata. |
| Native primal point/joint recovery | row_solution; successful recovery | Rewrites it from the accepted basic primal point and invalidates. No solved-column support may survive point restoration. |
| Native phase transfer / cleanup point retention | row_solution and rho; handoff | Restores basic/dual values and invalidates each; recovered certificates do not confer support validity. |
| `_copy_pivot_state!` | All six dense buffers; candidate creation/publication | Dense copies precede `_copy_hypersparse_cache!`. Valid metadata is reconstructed in destination-owned membership, invalid source buffers stay invalid. Shared matrix/mode metadata does not share value arrays. |
| `price!` and `_pipeline_price!` | tableau_row or pricing_row, sometimes external output; each pricing call | Invalidate before dense writing; indexed branch marks valid only after success. `price!` also invalidates before standalone sparse-pricing copyback. |
| LP-refinement witness probe | rho; fresh probe construction | Fresh scratch initially has no support metadata, but `_lp_workspace` emits refactor_other before returning. The subsequent rho copy lacks invalidation if an observer creates metadata during that event. See pending regression below. |

`_dual_row_residual_ratio` is a read-only scalar contraction; unlike the direction
residual check, it does not rewrite tau/row_rhs. Primal/dual value and weight loops
consume these buffers but do not themselves modify their support. Their separate
finite checks, bound repairs and weight floors still matter for sparse consumers.

A possible pricing producer can maintain exact support during its already required
N-entry output write, but its immediate density consumer currently calls
`_pipeline_vector!` and compacts valid support again. Counting only an avoided
N-entry rebuild would therefore overstate savings if another O(s) pass remained.
Any future subplan must specify both publication and consumption, preserve signed
zeros and CSC accumulation order, and include dense-output bookkeeping cost.
The default legacy policy has no hypersparse metadata to rebuild; an opt-in-only
saving cannot be reported as a default whole-solver improvement.


Static review identified two pending correctness regressions, not verified fixes:

1. `refine_basis_solve!` accepts AbstractVector, while `_pipeline_changed!` matches
   exact owned Vector identity only. A view into rho can receive an accepted
   correction while the parent's formerly empty support remains marked valid.
   Ordinary inspected callsites use whole vectors; the broader helper interface
   permits the view. Reproduce both the stale support and the next pricing result.
2. `_lp_workspace(...;recompute=false)` emits refactor_other with the fresh probe
   before `_lp_project_certificate` writes its accepted dual into rho. An observer
   that only constructs metadata for the zero scratch can expose the missing
   subsequent invalidation. Test a valid original witness, callback-created empty
   metadata, accepted projection, and the next sparse pricing result.

New diagnostic `reproduce/pipeline_boundary_regressions.jl` prepares those tests,
with whole-vector/no-observer controls. It is not executed while the S0 guard is
occupied. No production fix or runtime failure is claimed yet. The next available
serial slot should reproduce these safety gaps before implementing S2 or widening
S3 reuse. A validated correction will need a small implementation subplan and
focused cost review; do not add broad per-call overlap scans speculatively.
