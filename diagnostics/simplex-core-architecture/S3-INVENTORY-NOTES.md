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
