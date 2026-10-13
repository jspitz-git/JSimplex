# S2-B: price-audit input storage design

Status: SOURCE/DESIGN ONLY; proposed optimization is UNEXECUTED and unqualified.
Base diagnostic commit c44472e; production master d02416c. No Julia was launched.

## Continuation ruling

The user reported that automatic continuation had stopped. The corrected heartbeat
explicitly confines the wait for original-run evidence to S6-AQ and permits other
open roadmap work. Select this bounded S2 audit-cost prerequisite from the existing
S2 inventory, not the rejected S2-A flip controller. S6-AQ remains conditional;
no new original-run evidence, reproduction, or historical-cause conclusion exists.
The broad S2 error-controller, drift, and reconstruction-elision gates remain open.

## Existing operation and dependency

`src/primal_updates.jl:52` copies the predicted primal and reduced-cost vectors,
then independently reconstructs the workspace. It retains the reconstructed state
when the prediction is inaccurate. Neither prediction copy is a target here.
`_primal_price_prediction_reliable` first rejects nonzero basic prices, then builds
`_PriceAuditMatrix`, materializes `vcat(ws.scratch.rho,predicted)`, allocates a fresh
`SolveQualityScratch`, and invokes `solve_quality!`. The scratch allocation stays.

Let m be rows of A, n its structural columns and N=n+m the working variable count.
The implicit matrix has N rows and m+N columns. The concatenation copies m+N scalar
slots (n+2m), once per reached price audit. A full successful scalar pass through
`_quality_components!` visits nnz(A)+m+N terms in the existing stored order.
The compensated path uses the same three ordered sections. Finite-input scans,
residual arithmetic, native compensated checks and existing wider fallback remain.
These are source counts, not measured allocations, timing or dynamic call totals.

The normal incremental transactional audit occurs at iteration multiples of20;
other direct audit calls also exist. Earlier value/basis checks can return before
price auditing. This is not the ordinary native iteration hot path and does not
establish a current-default or long-medium speedup.

## Bounded candidate design

Introduce a private, immutable, read-only `_PriceAuditValues{T} <: AbstractVector{T}`
with exactly two `Vector{T}` references, `dual` and `predicted`. Activate it only for
T in Float32/Float64 and concrete same-type Vector inputs with both parents nonempty.
If either parent is empty, the helper returns the original vcat result. The private
constructor rejects empty parents with ArgumentError, including direct construction.
It also requires T === Float32 or T === Float64, not merely T<:Union{Float32,Float64};
a vector with union element type is not an eligible hardware vector.
All other scalar/storage forms retain the original vcat path. No workspace field, persistent cache, mutable
registry, global method overwrite or changed numerical policy is permitted.

Its linear indexing returns dual[i] for i<=length(dual), otherwise
predicted[i-length(dual)], with ordinary bounds checks. Define size, IndexStyle and
Base.dataids by forwarding both underlying vectors' dataids. The installed Base
abstractarray.jl documents dataids for custom wrappers; without this forwarding,
solve_quality!'s existing mightalias guard could miss an overlapping input.
Base.mightalias also returns false for empty arrays. A parent that aliases initially
empty compensation/error_sum scratch can be resized inside compensated evaluation;
dataids forwarding alone cannot protect that case. The empty-input fallback and
constructor domain check are mandatory, not optional performance heuristics.
Do not add setindex!, materialization, arithmetic, or a second element traversal.

Use a private `_price_audit_values(dual,predicted)` helper: the generic fallback
returns vcat, while the hardware-vector method returns the wrapper. Only replace
the existing values assignment with that helper in the proposed production diff.
The actual production file is unchanged in S2-B. No Julia syntax/dispatch/inference
or arithmetic equivalence has been executed; these remain explicit gates.

The borrowed inputs must remain stable for the synchronous residual evaluation.
The reached implementation reads x, writes separately owned scratch, and has no
logger/observer/stop callback. In the normal caller, predicted is a pre-recompute
owned copy and rho is read immediately after recompute. No objective-dual state
may survive beyond this invocation. Concurrent mutation of a workspace is not
made safe by this design. Direct aliasing with residual scratch must still reject.
Empty sides must use materialization; repeated nonempty owners and nonempty
parent-storage aliases recognized by the existing dataids contract need explicit
tests. This is not a general foreign-buffer or unsafe_wrap overlap guarantee;
normal production use retains the existing separately allocated quality scratch. Direct empty-adapter construction must
throw before solve_quality!. This does not alter the existing Base alias contract.

## Alternatives and work/memory decision

Keep vcat: established behavior, one temporary m+N-slot vector. This is the control.
Persistent workspace concatenation/scratch reuse: rejected for this small scope;
it introduces capacity retention, invalidation and nested-audit ownership duties.
Borrowed wrapper: selected for qualification only; constant reference metadata and
no copied input slots for eligible inputs, but up to four O(1) emptiness checks
(two in the helper and two at the private constructor boundary), up to two exact-T
comparisons at construction, a routing comparison
at each indexed access and custom
iteration/alias dispatch may cost more than a contiguous vector. Removed data
traffic is not proof of lower elapsed time. Existing quality scratch and prediction
copies dominate some cases and are not counted as savings.

There is no new production work or memory in this documentation-only change.
A future candidate must measure whole price-audit time, aggregate allocation events
and bytes on sparse and dense fixed inputs, with compilation and warmup excluded,
interleaved repetitions and all raw samples retained. Report both wins and losses;
reject a material regression rather than inventing a density threshold. No native
free/retention claim follows from removing a Julia vector or holding two references.
The wrapper's references are invocation-local in the intended use, not a proven
GC collection point. No factorization, basis solve, certificate or default-policy
call is removed. Existing wider residual evaluation is retained, not new routine
precision promotion.

## Verification and preservation

A fresh source check binds the exact relevant source, tests, installed Base alias
contract, this report and the successor plan. Whole tracked src/test files are
compared with master without executing tests. All40 AP closure bindings are checked
before continuation edits; AP-bound STATUS/roadmap are preserved byte-for-byte in
this result directory. Old accepted scripts/raw/false audits/rejections are not
executed or rewritten. The earlier read-only lookup of nonexistent solve_quality.jl
failed; actual implementation is simplex_numerics.jl. This was a path lookup error,
not a numerical failure. Command output is summarized in read-errors.txt.

Next S2-C is offline candidate/test-source preparation and independent review only,
under 2026-10-13-price-audit-values-preparation.md. No numerical allowance is granted
by this source decision. A subsequent concrete launcher/pin/auditor admission must
precede any Julia parsing, import or execution. CI remains off; native HH symbolic
reuse remains disabled; S2-A/S6-J/whole-AF rejections and all broader gates persist.

## Review amendment

The initial design was rejected for empty-parent scratch aliasing. Its exact report
and successor plan are preserved as before-review files. One offline amendment
restricts borrowing to nonempty hardware vectors and defines rejection at the private
constructor boundary. Empty cases retain vcat. The successor test contract also
requires bitwise Float32/64 comparisons so NaNs and signed zero are not judged by
plain ==. This is still a proposed design; no Julia behavior is claimed as tested.

The same review pass grades M1 exact hardware dispatch as Important for the next
plan and resolves it with two explicit factory methods plus constructor type checks.
M2 bit-aware comparisons was resolved in the empty-parent amendment. The four-check
intermediate amendment and its exact texts remain preserved; the final bounded
supplement binds the exact-type clarification. No runtime claim or new allowance.
