# S4 factor ownership inventory (static prerequisite)

Source: master beb161b, identical production tree in the architecture checkout.
Prepared while the sole S0 calibration process runs. No production edits or new
numerical measurements. S4 numerical attribution, subplan and acceptance remain
pending. This map prevents duplicating reuse already present in the managers.

## Huangfu-Hall ownership and allocation boundaries

`src/huangfu_hall_factorization.jl` owns these distinct lifetimes:

| Storage | Lifetime and sharing | Existing protection / future measurement |
| --- | --- | --- |
| HHBase lower/upper CSC, permutations/scaling and U row adjacency | Published base is treated as immutable and shared by saved factors. Replacement constructs fresh owned arrays. | Cannot overwrite old L/U to reduce allocation while saved copies exist. Extraction and adjacency traversal cost scales with dimension and factor nonzeros. |
| Four dense vectors work/auxiliary/prepared_partial/prepared_direction | Private to each factor, resized at successful refactorization. | Refactor extraction borrows only disposable work/auxiliary; prepared values survive a failed candidate. A saved factor gets fresh vectors. Length does not by itself measure retained backing capacity. |
| HHUnitWorkspace values/marks/support | Private solve workspace; recreated when dimension changes. | Hardware unit-BTRAN eligibility belongs to immutable base metadata. Retain numerical order/exact support; no new coefficient pruning. |
| HHUpdate records | Immutable active history; saved factors share a prefix. | `shared_update_count` prevents recycling shared arrays. Only a private suffix retires after successful factorization. History cost scales with all packed u/v entries, not just chain length. |
| u_pool/v_pool | Retired private fixed-size index/value pairs. | Each pool is already capped at4MiB payload and256 pairs; exact-length reuse avoids hiding oversized capacity. Variable-payload arbitrary-precision values are not pooled. Dimension changes drop the pools. |
| refactor_workspace | Private native/Markowitz construction backend; no alias to extracted live L/U. Saved copies start with none. | Backend may mutate before failing; the catch drops it while preserving the active base/history. Float64 native uses UMFPACK lu! with symbolic reuse disabled; equal dimensions do not establish equal pattern. |
| HHExtractWorkspace | Private Float64/Int64 CSR L extraction buffers. | Existing8MiB payload cap and density-shrink rule; oversized requests use disposable arrays and clear the cache. Output CSC arrays never alias this scratch. Empty factor clears it. |
| New extracted base | U CSC arrays, L CSR-to-CSC output, permutations/scaling, positions and row adjacency. | Native Float64 extraction already avoids SparseArrays' extra transpose object. `_hh_scale_mode` checks scaling with existing work plus two temporary vectors. Non-Float64 native converts dense LU L/U to sparse; Markowitz gathers coordinate vectors and then constructs CSC. These are separate backend/precision costs. |

Successful `refactorize!` publishes the validated new base/backend, retires only
private updates, resets preparation and adjusts scratch. Failure occurs before
publication and before update retirement. `copy_basis_factorization` shares the
base and update records, copies the history container and allocates private
scratch; it is not a deep copy of every coefficient. Do not double-count shared
base storage when attributing a live factor plus checkpoints.

`_factor_storage_count` is an arithmetic-work metric: it counts live numeric
factors/updates and intentionally excludes retired pools and construction
backends. It cannot establish total retained memory or process RSS. Native
UMFPACK storage and JIT/allocator memory need separate attribution.

## Other managers: reuse already implemented

- PFI Float64 uses a private UMFPACK spare. `_same_umfpack_pattern` compares actual
  CSC indices before symbolic reuse; failed candidate LU is discarded. Copies
  mark live storage shared. Arbitrary-precision dense native construction remains
  a separate allocation path; Float32 has reusable private LU slots.
- PFI and triangular managers recycle private update suffixes. Shared update
  prefixes must remain immutable even if a saved copy is no longer reachable;
  the scalar sharing marker is conservative, not a reference counter.
- FT/SS/BG already cap oversized packed-upper backing capacity at refactorization
  via `_reset_upper_storage!`. Ordinary FT's historical multi-GiB retention is
  documented in the preserved basis-update-chain-bench checkout under
  diagnostics/basis-memory/README.md; it is not an unresolved discovery here.
  Do not rerun that completed experiment merely to rediscover the old fix.
- Markowitz uses private construction dictionaries plus active/spare output
  slots, with shared-factor protection and failed-candidate discard. Its reset
  deliberately keeps excess dictionary objects after dimension shrink and
  empties their values; packed-vector pools and inactive dense cores also retain
  capacity. This is a candidate for bounded-retention characterization, not
  evidence of a current leak or a reason to change its policy without measurement.
- `_basis_matrix!` in simplex.jl already assembles a borrowed CSC in owned
  workspace buffers. Public `basis_matrix` returns owned storage; factors must
  not retain aliases to the assembly buffers.

## Existing tests and evidence limits

`test/huangfu_hall_tests.jl` covers refactor scratch/copy/failure isolation,
dimension and empty transitions, private-suffix pooling, exact-length reuse,
payload caps, native extraction equality and saved-factor independence.
`test/basis_matrix_reuse_allocation_tests.jl` exercises assembly reuse and saved
factors for native/Markowitz PFI/FT/SS/BG; its inspected loops do not include HH.
A future S4 change must explicitly cover HH as well as supported precisions and
backend-specific allocation behavior. No existing test was rerun for this map.

S0 suite3 prefix attribution provides a separate warning: medium's presolve
accounts for about8.17GB and168091971 allocation events per counted sample.
That is not HH factor storage. Exclusive refactorization time includes its GC;
its median can hide individual GC-heavy calls. Do not infer a factorization
arithmetic bottleneck from whole-process allocation or elapsed totals.

Next S4 deliverable, if selected under the roadmap's independent-stage rule:
choose one measured lifetime/cost hypothesis, then write the small backend
subplan with exact invalidation, sharing/failure and retention bounds. No API,
capacity increase, symbolic reuse or implementation is authorized by this map.


## Later live attribution (partial, not a completed reference)

The original map above preceded the S4-A four-vector dimension lifecycle fix,
now integrated at master4143dad; see S4-SCRATCH.md for its completed evidence.
This does not resolve allocation ownership for the entire backend.

The S0 medium-dual-counted-1 partial snapshot ending at iteration125952 contains
90247 phase-II accepted steps and1456.061697 seconds. Ordinary work accounts for
1277.777120s and154991368 allocated bytes; refactorization for178.259400s,
129075529624 cumulative allocated bytes and157.459843s GC. Recovery contributes
0.015602s and43319368 bytes. These are exclusive recorded scopes on the frozen
old source, not current-master timings or retained-memory sizes. Instrumentation
work is retained in its separate scope; no GC subtraction is used to claim speed.
The raw completed-window prefix is preserved with a SHA256 in
results/S0-L/medium-dual-counted-1-partial-attribution.json. Pins matched at capture.

The long solve has not returned or certified; plain elapsed and primal origin are
still missing. These observations motivate measuring construction/extraction/live
factor ownership separately. They do not prove all GC allocations originated in
the refactorization scope or that the S4-A scratch change speeds this fixed-size
history. The existing paired S4-A measurements remain the evidence for that fix.
