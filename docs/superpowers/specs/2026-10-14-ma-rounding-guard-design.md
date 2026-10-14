# MA-T: allocation-conscious BigFloat rounding eligibility

## Requested outcome and limits

Prepare a plan to remove the extra allocations associated with the BigFloat
scoped-rounding eligibility check while preserving numerical correctness. This
step is SOURCE/DESIGN ONLY: no Julia, parser, imports, compilation, driver,
candidate, production edits or new measurements. The human requested this plan
and independent review directly; implementation is a subsequent step.

Baseline is diagnostic ddd842fa9bcc7789452b1952e62423ecd94735e3 and master
6f68e24e8ddac42b948da8fcc2d636c010751194. MA-S-FALLBACK preserves 42 scoped
BigFloat measured pairs with +128 bytes/+8 events per four calls. The extra
present-key rounding lookup is the leading suspect, not proven object attribution.
The proposed change must pass a future experiment; compiler allocation elimination
is not established by source expressions or an inline annotation.

MA-S-2 remains rejected48/52. Its two Rational controls remain independently
unresolved and cannot be repaired, reclassified or waived by this plan. Success
here qualifies ONLY the changed guard, never the whole MA DenseLU candidate or
production integration. All original drivers, candidates, raw, gates and reviews
remain frozen. CI remains off, HH reuse disabled, automation paused.

## Recommended approach

Create a diagnostic-local `_dense_ma_rounding_matches()::Bool`. Read current task
scope on every call. If there is no scope, or the no-default MPFR rounding key is
absent, return true. Otherwise compare the typed scoped MPFR value with the live
global `ROUNDING_MODE[]`. Preserve the existing type/backend/shape/n16 checks in
exact order and replace only their final rounding expression with this helper.
Explicit scoped modes equal to the global mode must stay eligible; mismatching
ones must delegate the complete original call before any destination mutation.

The helper mirrors only the installed no-default branch of ScopedValues.get.
Use a **call-site `Base.@inline` on `Base.KeyValue.get(scope.values, key)`**, then
unwrap/type-check and compare inside the Bool-returning helper. Do not return an
Any-valued tuple or Some from the helper. Do not clone HAMT algorithms or inspect
leaf fields directly. The existing lookup still owns hashing, identity matching,
collision traversal and persistent read semantics; its `path` uses copy=false.
A temporary tuple remains in the source and may be eliminated by compilation;
zero runtime allocation is a qualification gate, not a design assertion.

The explicit local call-site inline overrides the lookup definition's @noinline
according to installed expr.jl, but is not a guarantee of all downstream inlining
or zero allocations. Do not force-inline whole solves, use effect assertions,
redefine Base methods or replace the compiler's global behavior.

## Alternatives and reasons

1. Keep the existing rounding_raw expression: smallest compatibility surface but
   retains the measured extra path; it is the reference and compatibility fallback.
2. Use isassigned/haskey or getindex: installed source still routes through the
   same KeyValue.get boundary. Presence-only rejection also narrows eligibility
   for equal scoped/global modes. Neither is selected.
3. Clone direct HAMT traversal or cache the last scope/mode: adds internal-layout
   coupling or retained task state/invalidation obligations. Not selected. Do not
   escalate to these alternatives if the bounded inline candidate fails.

## Equivalence and compatibility

Installed CURRENT_ROUNDING_MODE is a no-default ScopedValue{MPFRRoundingMode}.
`rounding_raw(BigFloat)` returns its value if present, otherwise ROUNDING_MODE[].
Thus absent-key equality is true and present-key equality is exactly the original
comparison. The source helper must retain the installed Scope union assertion,
type-check the retrieved value before comparison, and propagate unexpected lookup
errors. No catch-and-retry, no global rounding changes or numerical fallback after
partial work. No support is added for forged/corrupted private Scope storage.

Read-only use never mutates scope, dictionary, factor, RHS or numeric leaves. No
persistent scope/value/product cache, task retention or locks. Scope inheritance,
nesting, restoration after throw, task yield and changes between consecutive calls
must observe the actual current task each time. Concurrent unsynchronized writes
to global MPFR rounding/precision remain outside the original contract; do not
claim this change makes those writes thread-safe. Tests serialize global changes.

Private dependencies are Core.current_scope, Base.ScopedValues.Scope,
CURRENT_ROUNDING_MODE, ROUNDING_MODE, MPFRRoundingMode and Base.KeyValue.get.
The prototype is limited to the exact pinned installed Julia1.13.0 sources. Before
loading it, an external admission checks these source hashes and no-default key
construction, plus relevant scopedvalues/dict/hamt/expr implementations. Any drift
refuses this prototype before Julia. No per-solve filesystem or version scans.
A later production proposal must separately establish a supported runtime range
and select the original predicate on unsupported runtimes before private API use;
version numbers alone do not establish internal source equivalence. This design
is not that production admission and makes no portable allocation guarantee.

## Work and memory review

Frequency: one predicate per otherwise eligible-size FTRAN/BTRAN, including
recovery/certification callers. No new vector/matrix scan, basis solve, copy,
conversion or precision change. At most one existing trie lookup per call; depth
scales with active scoped-value storage/hash traversal, not n, nnz or factor history.
No claim of universally O(1) work. The local comparison eliminates a source-level
Some wrapper and exposes the existing tuple to the optimizer. HashState and path
return tuples remain source values; their allocations must be measured.

Inlining may increase compilation and code size. Keep the annotation local, report
first-call compile time separately, and inspect that code growth is confined to
this predicate rather than duplicated numerical loops. No new production work or
retained memory is introduced by this documentation. Future acceptance must reject
unnecessary computation/allocations/retention, even if numerical results agree.
