# Task1 state ownership and computational budget

Scope: opt-in experimental module only. No production dispatcher or current src/test method is changed. Task1 contains no dual proposal, pivot commit, repair algorithm or whole LP solve. Those remain Tasks2–6. No speedup is claimed.

## Phase import

`eligible` admits only Float64 native PFI, algorithm dual, explicit Devex, internal `_SolveDeadline`, no mutable observer. Import also requires exact source options/numerical-policy binding and identical clock start/limit. It validates numeric values and the source basis before numerical construction. Wrong source types/configurations are rejected; invalid numeric values or weights never create an engine.

The source problem matrix/objective/bounds are borrowed READ ONLY for the ownership epoch, under the normal no-concurrent-model-mutation contract. This is not universal immutability of a caller's Julia arrays. Engine values/bounds/basis, progress objective/scaling and solve scratch are newly owned. No external callbacks or writable views receive these owners.

One nonmutating basis validation into the engine-owned inverse map, one `_assemble_basis_matrix(source,nothing)` owned assembly and one fresh native PFI factor build replace copying the source factor. The public `basis_matrix` wrapper is deliberately avoided: its validator writes source.scratch.basic_mask. `copy_basis_factorization` would mark the source shared and borrow its native payload; reconstruction avoids those owner changes. No source mutable factor owner, native LU, eta/work buffer or assembly cache is reused. Setup cost is explicit and happens once per import, not each pivot. The new workspace's refactor count includes this extra build. Current numeric values are copied as-is, not silently recomputed or certified by reconstruction.

Progress start/iteration/refactor offsets and immutable options/numerical settings are retained. Source scaling/objective vectors are copied. Fresh refactor metadata is configured for the new factor; no diagnostics observer is inherited. The engine has a separate identity Ref and independent scratch.

## Physical storage ledger (64bit, before object/array headers)

Let m be row count, n structural columns, N=m+n, z=nnz(A), e=nnz(B). Exact Julia graph/native allocation sizes are runtime evidence, not these payload formulae.

| Owner | Payload / copies | Lifetime |
|---|---|---|
| Workspace values | costs/primal/prices/weights:32N bytes; two bound arrays:2N*sizeof(Bound{Float64}); Devex bits8ceil(N/64) | phase |
| Basis and progress | basic IDs8m; states N*sizeof(VariableState); objective8n; scaling8(m+n) | phase |
| Existing fresh J scratch |4m+2N Float64 values, two N-bit masks; candidate capacity requested N Int entries; initially empty ratio/rejection/history/cache vectors and scalar refactor state | phase; J's backing overcapacity must be counted at runtime |
| PFI/native factor | one new factor + own work8m and empty history; native/CSC/LU workspaces are not bounded by Julia graph formula | phase; source old owner overlaps at import |
| Basis assembly |8(m+1)+16e bytes for pointers/rows/values | cold temporary; native retained storage accounted separately |
| Indexed scratch metadata |5 full-capacity ID/stamp pairs, lengths m,m,N,m,m:12(4m+N) | phase; no shrinking |
| Residual values | two new Float64 m-vectors:16m | phase |
| Violation sets/map | Int IDs/inverse positions16(m+N), inverse basic-row map8N | phase |
| Planned and old values |4+4 Float64 vectors of physical N capacity:64N; unused tails uninitialized and never read | phase |
| Undo bookkeeping | IDs8N, UInt32 first-write stamps4N, UInt8 masks N, old states N*sizeof(VariableState), bounded old scalar/basis fields | phase |
| RowAccess | retained16z+8(m+1); temporary8(m+1), headers additional; CSC numeric values borrowed | phase / cold temporary |
| Other | fixed policy/counters, owner Ref, generation, invariant/proposal/journal wrappers | O(1) |

State construction initializes required position/stamp/mask arrays; numeric planned/old values are reserved undef, not copied/zeroed every step. The four existing scratch values are borrowed by support wrappers; only residual/scale add numeric storage. `_zero_scratch` avoids five redundant zero-value scans for freshly created known-zero buffers; public `StampedScratch` validates arbitrary initial buffers.

Task1 does not allocate an undo snapshot on a numeric write. It reserves storage for a later Task4 protocol; it cannot yet guarantee transactional pivot publication. Real header/backing capacity and native retention need future runtime measurement. No arbitrary cap is claimed to cover factor storage by this payload formula.

## Mutators / invalidation

| Operation | Local work | Effects |
|---|---|---|
| import | validate4N numeric values; one nonmutating inverse-map validation/owned assembly/factor build, row-index build O(z+m+n), one membership/map install O(N+m) plus initialization of physical capacities | new owner/gen1; source state unchanged; counters expose builds |
| `write_value!` | one checked Float64 field write and reclassification; untouched finite provenance is retained without rechecking the other three fields; constant sparse-set insert/delete | invalidates proposal/output evidence; updates exact primal/dual membership; no full scan |
| `classify_variable!` | constant numeric/state/bound reads, optional two membership changes | declared raw owned-variable write boundary; malformed/nonfinite state marks summaries invalid |
| `invalidate!` |5 evidence stamps + scalar flags | summaries invalid until explicit rebuild; no false successful repair |
| `rebuild_invariants!` | validate4N numeric values, validate basis, full position/map/membership rebuild O(N+m) | new generation and known-valid summaries only after complete success |
| generation wrap | reset5 scratch supports/stamps, count reset entries; O(4m+N) | no reused evidence; summaries require rebuild |
| scratch clear/compact | logical used prefix; all stamps only on UInt32 wrap | no physical resize or reallocation; exact nonzeros/subnormals retained |

The phase's finite proof comes from entry validation plus every declared write, not from generation numbers alone. Unknown direct array writes invalidate the contract until explicitly classified/rebuilt; callers must not mutate hidden owners concurrently. Empty dual membership means no tracked violation under working-state tolerances, not original-model optimality. The cold `assert_invariants` reconstructs independently and allocates; it must not be called on the ordinary hot path. No full violation sum is used as a terminal proof.

## Review obligations

Source-only review and admitted tests must verify private factor/value/scratch owners, original source state, clock binding, preexisting outside-support violations, field updates, exact support reinsertion/cancellation and forced generation wrap. A fresh factor is required for ownership simplicity here, but this extra setup work may later erase runtime savings; Task6 must count it. This experimental code creates no production cost until an explicit routing change is reviewed. No performance acceptance follows from passing Task1.
