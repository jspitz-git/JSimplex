# Optional native Float64 pivot policy

## Purpose and boundary

Preserve an explicitly selected native pivot policy across fresh construction,
private refactor candidates, spare reuse, copies, empty transitions, recovery and
precision transfers. This is the next SOURCE/DESIGN step requested after the
accepted `NATIVE-ACCURACY-QUALIFICATION.md` component result at `e0c7646`.
No code, candidate, driver or numerical run is created by this design stage.

The measured alternatives both restored all 2126 component residuals. Pivot1
removed sparse96 growth245688->1, with15extra U entries and48reported native
bytes; refinement retained the growth and cost1.39–6.98x in solve windows with
extra32n scratch bytes. Pivot1 is therefore the design candidate, not a new
production default or general stability guarantee. All old failures, outliers,
allowances and stopped routes remain frozen. The old direct-LU cost1 remains
FAILED/CONSUMED and cost2 BLOCKED. This design does not enable HH symbolic reuse.

## Alternatives and selected approach

1. **Selected: immutable selection plus factor-owned controls.** A symbolic
   SolverOptions setting travels through existing option-copy paths; a small
   immutable enum in the native backend fixes its lifetime policy. Only fresh
   native construction translates the selection into an owned control vector.
2. Mutating the active factor's controls after construction is rejected: copies
   share that factor, scratch was sized at construction, and fresh recovery loses
   such an out-of-band change.
3. Changing the default or automatically switching after a residual failure is
   rejected here: it changes all existing trajectories or adds retry work that
   the component experiment never qualified. A general arbitrary-control API
   would also expose unqualified refinement/scaling/strategy combinations.

## Selection and precision semantics

Add keyword `native_pivot_policy::Symbol=:default` and a final field of that name
and type to immutable `SolverOptions{T,M,R}`; retain the three type parameters.
Accepted values are `:default` and `:threshold_one`. Reject any other symbol.
For `:threshold_one`, require `basis_refactorization=:native` and manager PFI,
Forrest–Tomlin, Suhl–Suhl or Bartels–Golub; reject Markowitz and HH at option
validation, for every scalar type. Default accepts all current combinations.
This option is initially exposed through SolverOptions, not a new MOI raw
attribute; MOI's existing constructors continue to select the default.

The setting expresses persistent intent. It affects only an actual Float64
native UMFPACK factor. For every other supported precision the existing backend
and arithmetic remain unchanged, but options retain the symbol. Thus conversion
Float64→BigFloat→Float64, including `_copy_precision_options`, reactivates the
same selection when Float64 returns. No type conversion, precision increase or
new DenseLU/Markowitz control is induced by this flag. Focused tests cover Float16, Float32, BigFloat256, Rational{Int} and
Rational{BigInt}. `_supported_value_type` also admits other concrete AbstractFloat
and Rational types; their generic dispatch remains unchanged, not newly runtime
qualified by those representatives. Selection is not permission to claim their
native UMFPACK qualification.

Preserve the symbol through `_validated_options`, `SolverOptions(T, options)`,
`_phase_options`, `_remaining_options`, `_lp_auxiliary_options` and
`_copy_precision_options`. Preserve the existing 16-positional-field
`SolverOptions{T,M,R}` construction as a compatibility overload that supplies
`:default`; new internal positional copies append the actual symbol. Old
low-level positional construction was not a validated public option parser;
new public keyword/conversion paths must validate the selection and combinations.

## Backend invariant and interfaces

Define private enum `_NativePivotPolicy::UInt8` with `_NATIVE_PIVOT_DEFAULT` and
`_NATIVE_PIVOT_ONE` in `src/factorization.jl`, plus
`_native_pivot_policy(value::Symbol)::_NativePivotPolicy`. Add
`const pivot_policy::_NativePivotPolicy` to mutable `UMFPACKBackend`, preserving
its nonparametric type and existing fields. Backend copies keep the enum value;
no factor controls are shared via a new global registry or mutable policy object.

`_native_lu(B::SparseMatrixCSC{Float64,Int}, policy::_NativePivotPolicy)` performs
exactly one fresh LU. Default calls the original `lu(B)` path unchanged.
Threshold-one obtains a fresh installed default control vector, sets only
PIVOT_TOLERANCE=1.0 and IRSTEP=0, and passes it to `lu(B;control=controls)`.
Use constants from `SparseArrays.LibSuiteSparse` plus one for indexing; the
installed uppercase constants are not exported into `SparseArrays.UMFPACK`.
The wrapper copies controls. No global default edit, caller vector argument,
active-control mutation or extra factorization is allowed. AUTO strategy,
symmetric pivot tolerance0.001, scaling, q, dropping and other defaults stay.
Threshold-one is full partial pivoting only when strategy is UNSYMMETRIC; it
makes no such promise when AUTO selects SYMMETRIC.

Add `_factorize_basis(B, backend::Val, policy::_NativePivotPolicy)` and ordinary
manager constructors `Manager(B, backend::Val, policy::_NativePivotPolicy)` for
PFI/FT/SS/BG. Old one/two-argument constructors forward default. Native Float64
uses `_native_lu`; native other precisions retain the old dense path. Markowitz
accepts default only, rejecting threshold-one before factorization. Extend
`_basis_factorization(B,mode::Val,backend::Val,policy::_NativePivotPolicy)` for
these four managers, with a default-only delegating fallback for other managers.
`_basis_factorization(B,options)` converts the validated symbol once at setup
or fresh reconstruction. No policy lookup belongs in FTRAN/BTRAN/update loops.

Legacy two/four-argument UMFPACKBackend wrappers remain available with the
historical default reconstruction policy, including tests wrapping a singular
raw LU. They do not certify arbitrary caller-supplied control values. Only the
policy-aware factory creates a threshold-one-tagged backend; directly replacing
internal fields or mutating F.control is outside the owned-policy invariant.
Do not add repeated 20-control scans to police such external mutation.

## Lifecycle transitions

| Transition | Required behavior |
| --- | --- |
| Initial empty | Store selection even with no active factor; allocate no native controls/LU |
| Fresh nonempty or no spare | One `_native_lu` with stored selection; publish only after success |
| Private spare | Existing pattern check and `lu!` reuse; control vector already belongs to the same immutable backend policy; do not recreate/rewrite it |
| Copy | Separate backend slot container, same enum, shared active factor, no shared spare; preserve existing shared flags |
| Nonempty→empty→empty→nonempty | Retain policy and existing spare lifecycle; do not create a factor merely to carry metadata |
| Dimension/pattern change | Original CSC conversion/pattern rules; selected policy persists regardless of reuse decision |
| Failed private lu! | Drop mutated spare; preserve active factor, dimension, policy and saved copies; rethrow original exception |
| Failed fresh LU | No publication; preserve all existing state and selection |
| Recovery/phase/cleanup/retry | Existing factory uses preserved options; new private factor receives same effective selection, no new recovery branch or retry |
| Precision transfer | Preserve option intent, use original backend for destination scalar; reactivate only on Float64 native construction |

No cache of controls or metadata needs invalidation: the enum is constant for a
backend lifetime. Selecting another policy requires a new independently owned
backend. Existing finite checks, quality checks, tolerances, failure handling,
work accounting, clocks and original-model certificates remain unchanged.

## Direct prototypes and comparison boundary

The frozen candidate in `diagnostics/direct-lu-markowitz/reproduce/direct-factor.jl`
currently rebuilds an ordinary backend inside every direct refactor and retains
only backend/normalization intent. A later new version must add the same immutable
policy field to DirectLowerBackend and pass it through direct/fallback, copies,
empty, failed refactor and resized transitions. The fresh replacement must receive
the stored policy before export. It must not retain a full UMFPACK factor merely
to retain one enum. Markowitz keeps default. Native ordinary reference and direct
candidate must use the same policy; label it explicitly. No comparison may use
pivot1 only on the candidate. Export orientation work remains counted.

This design's implementation plan first qualifies ordinary production-policy
plumbing in an isolated candidate. It does not edit the frozen direct candidate,
resume cost2 or promote any prototype. A separately reviewed new direct-adapter
and benchmark admission is required after ordinary policy qualification.

## Work and memory contract

One Symbol field per options object and one enum field per native backend add
constant metadata, including copies; alignment can exceed the raw enum size.
Fresh threshold-one construction obtains the same default-control vector that
plain lu obtains internally, sets two entries and incurs the existing wrapper
control copy. Count actual allocations rather than assuming this is free.
Default must retain the original call and arithmetic. Private spare reuse adds
no controls, copies, matrix scans or solves; existing O(n+nnz) pattern work stays.
Policy reads/assignments occur at construction, copy, empty reset or recovery,
not per solve, candidate column or update. No additional retained native owner,
growing ledger, cache or extra scratch. Pivot choices may increase fill/native
work; the observed15U/+48bytes is not a universal bound. Measurements must
separate policy-plumbing overhead from changed factorization and trajectory.

## Acceptance and next boundary

Preparation must produce a byte-invertible ordinary source overlay, focused
regression/ownership tests and a complete source-level work ledger, then receive
independent gpt-6-astra review. All Julia RED/GREEN/cost work requires its own
concrete command/input/runtime/source budget and fresh independent admission.
No long/full-suite/large-MPS run or changed tolerance is needed. Short-run
permission already exists; it never substitutes for exact admission.
Production merge, public-solver qualification and a new direct comparison are
separate gates. This document accepts no implementation or runtime behavior.
