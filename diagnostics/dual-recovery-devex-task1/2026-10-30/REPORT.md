# Task1 source preparation: opt-in refinement refusal provenance

**SOURCE PREPARATION ONLY — Julia syntax, dispatch, RED/GREEN, runtime correctness, compilation and allocations are UNEXECUTED/UNQUALIFIED.** This implements only the next Task1 text candidate and prospective tests from the reviewed plan. No actual src/test/environment/CI/master change, no pricing/fallback implementation, new numerical allowance, driver or launcher. Tasks2–4 and runtime completion remain pending.

Plan: docs/superpowers/plans/2026-10-30-dual-recovery-devex-fallback.md. Spec: docs/superpowers/specs/2026-10-30-dual-recovery-devex-fallback-design.md. Diagnostic baseline24a79f0babfba545387bad65939b5d1b51767f56; production master c0fa748ffa61ccb7c1caaf248c40324f60bc737b. Existing attached isolated native-quality-scans worktree reused. Fresh boot/process/ref record checks all727 previous groups AND sessions and no Julia. Production71source files byte-equal to master.

## Candidate and interface

`simplex_numerics.jl` is the complete unchanged production file plus one insertion after SolveQuality: a private UInt8 `_RefinementCause` enum, fixed-size `_BasisRefinementOutcome{T}(quality,cause,invalid_seen)`, and inline result/finish adapters. SolveQuality and workspace/scratch fields are unchanged. The outcome contains no vector, cache, mutable ledger or retained workspace/factor reference. `not_observed` is a metadata-only sentinel for future consumers; it does not assert that a numerical solve was skipped.

`simplex_recovery.jl` is the complete unchanged production file except the refinement entry/kernel boundaries:

* Existing public `refine_basis_solve!` retains its signature and SolveQuality return. It passes Val(false) into a common checked entry and numeric kernel.
* New `_refine_basis_solve_outcome!` passes Val(true), returning the original quality plus the actual terminal cause and sticky invalid-proposal marker.
* The old private eight-argument kernel entry remains a strict quality-only forwarding method.
* The common entry retains all dimensions/alias checks, buffers, basis assembly, stored-precision handling and `_record_refactor_quality!` effect. One dispatch adapter records the quality once and returns the requested result shape. No exception is caught or converted.
* The common kernel keeps every numeric expression, correction/cleanup, stop invocation, adoption, event and support invalidation in the original order. Its loop's original short-circuit return is expressed as equivalent ordered branches to distinguish reliable/nonfinite/stopped causes.
* A rejected nonfinite correction/trial/trial-quality returns the same old quality as before, with a hard cause in detailed mode. `invalid_seen` also remembers a discarded nonfinite cleanup quality or nonfinite restored trial quality; it does not infer safe provenance from final finite quality. Its scope is refinement-level observed proposals, not internal range fallbacks already handled by unchanged quality evaluation.

Val(false) adapters return the quality directly and do not construct outcome objects. New sticky updates are guarded by compile-time Report. This is a source structure/optimization intention, **not a measured zero-boxing or zero-overhead result**. Julia specialization, inference and allocations must still be qualified later on the admitted normal-path comparison.

## Prospective ordinary tests

The initial main test file was written before initial candidate generation. Assertions were statically refined before review; no test was executed or observed RED/GREEN. A test name or static source check is not a runtime pass.

Canonical `refinement_outcome_tests-reviewed.jl` contains ordinary Test testsets in its own module and a top-level invokelatest entry after definitions. It covers Float32/Float64, both orientations, sparse and densely populated CSC bases; reliable initial/zero-limit points, one genuine repair including last-iteration reliability, unchanged/not-improving/limit returns, initial Inf/NaN, nonfinite correction, addition overflow, finite trial with nonfinite quality, stop before work/adoption/wide quality, original correction/stop/observer exceptions, and sticky invalid cleanup provenance. Small BigFloat/Rational API/precision smoke cases and dimension/alias guards are included. These do not claim all backend/precision coverage.

Both APIs are compared for quality fields, destination/RHS, model/basis preservation, stop/solve/event/observer counts, scratch/model/basis array identities and refactor-quality state. Expected causes/counts and simple solution values are literal fixture expectations. The small dense solve uses the unchanged policy tolerance for numeric solution comparison; metadata/default execution must agree exactly. Exceptions retain original identity/cause and no outcome is returned on throw.

Private `CorrectionProbe` methods add dispatch only for that new test type. They count before a genuine delegated LU solve, then may declare a zero/negative/half/nonfinite/huge output or throw. These controls exercise the real refinement/quality code; they are not backend numerical-fidelity experiments. Each fixture constructs one delegate LU, not one per API call inside a solve. There are no global production-method replacements or custom test recorders.

The extreme-range discarded-cleanup case explicitly uses an identity delegate that is **not** a factor of its quality matrix, then replaces its correction with zero. For an original quality matrix with first equation `-L*x1+x2+x3=0`, x=(1,L,L), L=2^127 or2^1023, the initial residual has finite magnitude L. Cleanup removes x1, creating a residual2L that cannot be stored in the working type; whole-quality rejection restores the original trial. This deliberately faulty factor/proposal tests sticky invalid metadata using actual quality/cleanup arithmetic, not the fidelity or factorization of that extreme matrix. No new solver fixture is promoted.

`reference.jl` contains only the two exact original refinement functions, qualified to unchanged JSimplex helpers in a bounded local module. It is not a full solver/module clone and defines no production external methods. `reference_comparison_tests.jl`, included after the main tests, compares this original numeric execution with ordinary and detailed candidate APIs on the same independent fixtures. Candidate source files must be installed in a separate ordinary source overlay before using JSimplex in a future process; never include them into an already loaded production module or reinterpret old cache/source pins.

## Static source evidence and limitations

The new Python source-check was executed once:87checks/155bindings PASS. It independently reverses each permitted return/control-status edit and recovers the **exact original kernel**, then restores the original checked entry, whole recovery file and numerical file. It also unqualifies the bounded reference and recovers both original functions exactly. All71 actual production sources still equal master. This proves the constrained textual transformation, not Julia parsing, dispatch, arithmetic execution or allocation behavior.

Readtime source-pins bind ten baseline/spec/plan inputs. The builder is preserved before execution and refuses existing candidate paths. The host/ledger preparation script is copied after execution and is not a retroactive self-input pin. The plan's private progress ledger records the Task1 preparation scope and the explicit ruling that approved no-Julia constraints override generic skill runtime/task-done commands. No runtime completion line is written.

## Computational work and retained memory review scope

Candidate normal refinement adds a compile-time result-mode entry and adapters, not a new basis solve, quality pass, full-vector/matrix scan, workspace field, scratch array, mutable status sink or extended lifetime. Basis validation/assembly remains O(N+m+nnzB) per call, with N=m+n. Corrections and optional wide residual/cleanup work remain exactly the original policy-bound work. Default short-circuit stop calls and exception/publication prefix must remain identical.

Detailed mode adds only fixed-size result/cause metadata and scalar checks on existing quality fields; a local sticky Bool is live only for that call. BigFloat/Rational qualities retain their existing scalar owners, without copying them or a vector. Outcome boxing/return ABI and adapter inlining remain unmeasured and must be reported rather than assumed. This Task1 creates no Devex resets, pool scans, fallback revalidation, callbacks or logger calls.

Prospective test instrumentation is deliberate extra work: fresh tiny owned workspaces/caches, one LU per fixture, arrays of dimension at most3, pre-entry solve counters and standard bounded diagnostics. Fault injection adds only declared test-type behavior. It is not production work or a performance benchmark. No timings/allocations, global speedup or native-memory conclusion is available.

Next accepted step, if source review is clean, is Task2 isolated weight classification/private-state preparation. Actual RED/GREEN and all numeric/normal-path cost gates remain Task4 under a new concrete immutable admission. Earlier rejected KLU weight/cleanup evidence stays rejected and frozen; this task supplies no waiver or production integration.

## Review correction and canonical selection

The initial independent review rejected one prospective fixture (F1): the initial zero point in `nonfinite_wide_quality` made the compensated evaluator skip Inf*0. No numerical test was run. The canonical main tests are now `refinement_outcome_tests-reviewed.jl`, with only that fixture initialized to [0.5,0]. Initial ordinary quality is finite/unreliable (relative error 1/3); poisoning the diagonal before wide quality evaluates Inf*0.5 and supports the original hard-cause/zero-solve/one-stop expectations for both orientations. All original expectations and candidate numerical code remain unchanged. This is a source-derived argument, not an executed pass.

The original tests, 87-check/155-binding source proof and initial rejected review remain frozen. A provisional clean reviewer assessment that missed this issue is also preserved separately; it is not acceptance. Initial review bindings of REPORT.md resolve only to the byte-identical REPORT.md.before-review. Separate review-fix.json verifies the single-line correction, unchanged original bindings and prospective checks. The bounded reference comparison still imports the same test module name after including the canonical reviewed main tests. No additional driver or launcher is introduced.
