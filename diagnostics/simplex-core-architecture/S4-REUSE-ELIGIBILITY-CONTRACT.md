# S4-J: HH symbolic-reuse eligibility contract

Source/evidence only on2d8bc0a/master0eb75c3. No Julia, factor, workspace, component,
solver, old parser/auditor or benchmark execution. New offline27checks/530hashes
pass. First source-parser ValueError/exit1/source preserved separately: an unscoped
end marker matched an earlier docstring, yielding an empty wrapper slice. A new
source_eligibility_2.py bounds the end search after the method start; no old script
was rerun or rewritten. No production/test/CI/user-file change.

## Closed-path eligibility, not a public guarantee

The narrow future candidate is native Float64/Int64, square nonempty canonical CSC,
existing valid exclusively owned native workspace/symbolic state, identical stored
indices, and the original default controls/q=nothing path. These are separate
conditions; `_same_umfpack_pattern` proves only dimensions/index equality, including
zero/one-based index adjustment. It neither checks values nor compares controls or
symbolic validity. Wrapper numeric setup handles a null symbolic object by building
one, even if the requested reuse flag is true.

HH native construction calls lu without q/control keywords. Installed UmfpackLU
copies incoming controls/CSC, default IRSTEP=0; current repository src has no
`.control` property access. Thus within the inspected closed HH path there is no
control mutation and no new control-vector copy/cache/scan is justified solely to
recheck this invariant. This is not protection against direct field mutation,
external wrapper calls, future routing changes, or other native controls. The
wrapper's nonnull-symbolic early return ignores newly supplied q, and symbolic
native construction receives nzval as well as controls. Pattern identity does not
prove value-independent ordering/fill/quality or equal trajectories.

Do not add a current-controls-only comparison pretending it captures the controls
used to build symbolic state. A broader mutable-control API would need separate
provenance/invalidation design. Production reuse stays false and no eligibility
helper is implemented here. Finite-basis qualification is currently restricted to
F/G/I inputs; it is not a blanket runtime finite guarantee.

## Dispatch, mutation and failure table

| Boundary | Actual route / work / publication |
|---|---|
| Unsupported scalar/backend, native Float64 on non-Int64 host | options.jl186 validation rejects before initial factor construction. Different-scalar refactor has no matching typed HH method; no implied conversion/promotion. |
| Nonsquare HH input | Constructor/refactor checks square before native call; refactor check is outside catch, so existing native workspace is not discarded by this precondition error. |
| Empty Float64 initial basis | `_hh_initial_lu` returns nothing; empty owned HHBase and zero-length scratch, no UMFPACK symbolic/numeric work. |
| Empty native refactor, any supported scalar | `_hh_refactor_backend` returns nothing before inspecting old factor; empty base constructed. Successful publication clears pools on dimension change, replaces obsolete scratch/unit storage, resets extraction scratch at n=0; no native LU. |
| Changed nonempty shape or absent native workspace | Fresh `_hh_native_lu`, no reuse helper. Float64 copies/converts CSC as needed then fresh symbolic/numeric; scratch replacement prepared before base publication. Failure drops workspace reference, old extracted base remains subject to existing failure contract. |
| Non-Float64 native | Private dense Matrix{T} plus native LU, preserves scalar, no UMFPACK symbolic reuse. Empty constructor may use zero-dimensional dense LU; do not conflate with Float64 early return. |
| Markowitz | Separate Markowitz constructor/refactor/extraction, no UMFPACK reuse; unchanged. |
| Same shape Float64 | Existing production lu!reuse=false; candidate only changes keyword to exact pattern result. Pattern mismatch rebuilds symbolic; match permits retention. All existing native CSC copies/numeric work/extraction remain. |
| Nonfinite same-pattern basis | No whole-input finite scan in HH refactor or installed lu! wrapper. Dimensions/workspace/CSC mutate before numeric; native status/errors and subsequent extraction checks decide outcome. Current source alone cannot promise rejection, exception class, or stage. |
| Extraction validity | Scale orientation may invoke one native solve; diagonal U must be finite/nonzero and L diagonal unit. Nonfinite U offdiagonal marks finite_upper=false, not blanket rejection; lower entries are not all-finite checked here. This metadata selects a conservative solve path, not input certification. |
| Failed numeric/extraction | HH catch drops refactor_workspace. Disposable work/auxiliary/extraction scratch and native owner can already be mutated. Old extracted base/history/prepared values are not intentionally published until after try. Later retirement/publication allocations are not covered by a universal transactional guarantee. |

Public model conversion validates finite coefficients; model validation scans A.
This does not make the internal AbstractMatrix factor API reject nonfinite input,
nor prove all arithmetic intermediates stay finite. No certificate or tolerance
rule is changed. No rerun of H's consumer inventory is needed.

## Existing execution and new gap

Nine relevant C-focused production/test hashes match current source. Pinned driver
actually includes dimension/HH/precision/Markowitz/scalar/public integration files;
selected raw rows show dimension8, scalar/failure336, scratch/copy/failure10 passes.
These354selected passes are a subset of the accepted4366run, not new measurements.
Dimension/empty native and other-scalar fallback routes already have source-matched
execution; because the proposed keyword lives only in the same-size Float64 route,
these branch bypasses do not justify repeating their numerical lifecycles now.
They are not proof of a changed production implementation or every input shape.

F recorded native pattern/dimension fallback and explicit-zero cases; G direct HH
and I actual borrowed/recompute cover their specific finite lifecycles. None tests
same-pattern NONFINITE basis refactor. Existing NaN tests reject update directions,
not basis input. The selected next discriminating obligation is this one boundary,
with a separate S4-K four-case paired diagnostic plan. Empty/dimension/scalar routes
stay unchanged/source-matched; arbitrary external control mutation remains excluded.
If nonfinite behavior diverges or publishes unusable factors, preserve failure and
stop; do not silently add a finite guard or weaken expectations to obtain acceptance.

## Computational work and limitations

No new production work/allocation/retention. Existing pattern comparison costs up
to m+1+nnz(B) index comparisons, short-circuits on mismatch, retains no cache.
A potential finite-input eligibility scan would add O(nnz(B)) reads per refactor;
it is NOT implemented or assumed free. It must be justified by the selected evidence
before any later proposal. Control provenance metadata would add fixed-size storage
and comparisons; closed-path ownership currently avoids that cost. Native copying,
numeric factorization, extraction O(m+nnz(L)+nnz(U)), optional orientation solve,
update-record retirement and packed retained payload remain. No representative cost
or native-memory result follows from tiny held-owner diagnostic runs.

SOURCE-bound controls and wrapper behavior are not a C implementation proof.
Other consumers, arbitrary q/controls, nonfinite outcomes, post-publication failures,
platforms/fullsuite and speed/native-retention remain unqualified. All safeguards,
prior rejections and disabled CI stand. Do not rerun either source parser or any
accepted evidence; first failure is preserved and corrected output is exclusive.
