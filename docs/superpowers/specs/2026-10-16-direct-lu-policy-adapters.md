# Direct LU adapters after native policy integration

## Purpose and baseline

Prepare all three direct LU managers—Forrest–Tomlin, Suhl–Suhl and Bartels–Golub—
for a new fair comparison with ordinary managers using native and Markowitz
factorization. This is the source/design continuation explicitly selected after
native-policy production integration. Master is26e2291745999f485a74f643298ca997d65c7205;
diagnostic baseline iscb757325ff6fe34e94479f7e622d6620fa7c1c8a. Rebind refs before
future preparation. This request creates documents and independent review only.
No Julia, candidate, test driver, loading, numerical run or production edit now.

The common export already exists in the frozen
`diagnostics/direct-lu-markowitz/reproduce/factor-export.jl`; the three initializers
and shared lower wrapper are in `direct-factor.jl`. Markowitz is already supported.
The corrected historical GREEN passed19,557 assertions under its exact old source.
That does not qualify a modified adapter on current master. Original cost1 failed
on ordinary native sparse96 DSE residuals and remains failed; its cost2 stays blocked.
The new work is separately labelled and does not reopen either attempt.

## Chosen design and alternatives

Use the current master ordinary module as a new isolated overlay, copy the frozen
export unchanged, and adapt only the private direct wrapper/factories to carry
`_NativePivotPolicy`. This reuses Markowitz export and all triangular algorithms.
Reference and candidate use the same current-master policy API. No global method
installer or nested full-module clone is used.

Reimplementing extraction separately for each prototype would duplicate algebra,
validation and ownership costs without a demonstrated need. Replacing packed
storage by dynamic rows/columns or CSR at the same time would confound the policy
and representation comparison; those remain separate future designs.

## Contract

Add immutable `pivot_policy::_NativePivotPolicy` intent to DirectLowerBackend.
Keep its R/F type parameters, normalization intent and typed ordinary fallback.
Pass policy into `_factorize_basis(B,backend,policy)` exactly once before export.
Copy retains the enum; refactor uses the stored enum to construct the private
replacement, including empty and direct→fallback→direct transitions. Failures
must preserve the old manager and all saved copies. Markowitz accepts only default
and rejects nondefault before any factorization, including empty/other-precision
requests. Other supported precisions use `Factor(B,backend,policy)` unchanged;
no arbitrary-precision direct export is introduced. Legacy direct signatures
forward default. This is a private diagnostic API, not a new public SolverOptions
value, manager default, factorization algorithm or threshold.

Preserve P*S*B*Q=L*U and the existing original-row multiply/divide convention.
Markowitz's sparse/dense core permutations and unit scaling are unchanged.
Normalization validates owned U before mutation; unsafe normalization leaves a
valid unnormalized direct representation. Unavailable export retains the one
already constructed ordinary backend; singular/malformed/unexpected errors escape.
Successful export retains no ordinary backend, temporary CSC U or native controls.
Copies share only existing read-only Float64 exported data, while scratch/upper
state and prepared/history ownership remain private under their existing contract.
No new full scans, allocations, controls or policy checks on each solve/update.

Native threshold_one sets pivot tolerance1 and IRSTEP0 through the integrated
helper; other control values, including strategy, remain defaults. Capture actual
strategy rather than asserting unsymmetric pivoting or a universal row-pivot bound.
Direct native solves still omit combined-solve UMFPACK refinement. Equal requested
policy does not prove equal numerical robustness or full native trajectories.
Controls must be checked on the real backend before extraction releases it; a
stored enum alone is not evidence that native controls were applied.

## New qualification and comparison

Qualify all three managers across native/default, native/threshold_one and
Markowitz/default. Preserve the seven old fixed input definitions, exact residual
bounds and lifecycle ordering in new tests. Add policy-specific sensitivity,
copy/refactor/fallback/empty and pre-factorization rejection assertions. Use fresh
labels and outputs; old executables and records are never rerun or overwritten.

For performance, compare native/threshold_one against native/threshold_one and
Markowitz/default against Markowitz/default. Native/default remains a compatibility
and correctness arm, not a silently substituted failed cost1 baseline. Existing
n32/96 sparse/dense fixture tokens and eight-update/two-refactor schedule are reused
as immutable inputs in a NEW comparison. Measure complete construction/export/
normalization/packing/refactor cost, not solves alone. Keep native strategy/fill,
compile/recompile, GC, bytes/events, timing dispersion and reachable-memory results.
No window retains diagnostic backend captures. Private direct refactors still
rebuild a whole manager while ordinary managers can reuse native spares; charge
that asymmetry honestly rather than optimizing it inside this adapter change.

One process at a time, Julia/BLAS1, heap hint2GiB, VM8GiB, available RAM>=6GiB,
swap<=1GiB. Each future bounded phase starts with inclusive300s/inner292s. A pure
process timeout alone receives one separately sealed/admitted600s/inner592s repeat
under the user's standing timing instruction. Preserve the failure; unchanged code,
inputs/options/runtime, no extra warmup or tuning. Mixed/numerical/resource/integrity
failure stops. Fixed5s public solver deadlines remain unchanged. No hours-long run.
Exact drivers, counts, output paths, immutable launch manifests and fresh independent
admission are required later; this design is not executable admission.

Production promotion is not authorized by a good microbenchmark. Original-model
certification and outer recovery remain intact. CIoff, HH reuse disabled,
automationpaused; full-suite and broad native-memory accounting remain open.
