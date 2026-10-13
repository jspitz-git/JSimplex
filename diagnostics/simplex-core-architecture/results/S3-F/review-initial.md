# Independent S3-F source/design review

Initial outcome: CHANGES REQUESTED (one documentation work-count correction).

The numerical decision and the bounded S3-G plan are sound for this source-only stage. No production candidate is accepted. The 17 source-contract bindings independently match their recorded SHA-256 values; source/test/CI differ neither from the recorded master nor through new edits. Existing test contracts were read, not executed. No Julia execution, package imports, compilation, LP experiment, or historical-script rerun occurred.

## Preserved initial finding F1 (P2)

The `Existing support access` row understates ownership checks as “Up to six owner comparisons.” In `src/hypersparse_pipeline.jl:14–39,71–83`, `_pipeline_vector!` first calls `_hypersparse_workspace!`, which checks matrix identity and all six scratch-buffer owners for a matching cache, then `_pipeline_buffer_index`, which checks up to six owners again. For `row_solution` the second loop stops at two: eight buffer comparisons plus matrix identity. The ledger needs this correction before acceptance. This is existing work, not a production regression.

## Numerical and lifetime assessment

`update_duals!` retains cost repair and pricing-pool invalidation outside exact tableau support (`src/dual_simplex.jl:566–591`). The zero-row tests in `test/partial_pricing_integration_tests.jl:75–85` and `test/dual_stagnation_cost_tests.jl:15–42` explicitly establish this source-level obligation for Float64 and the stated Float32/Float64/BigFloat/Rational{BigInt} cases. Their existence is not new runtime coverage.

The primal helper (`src/dual_simplex.jl:593–600`) visits the old basis in order and adds to the entering entry afterward, without local alias, finiteness, or uniqueness checks. Under IEEE round-to-nearest, (-0) - ((-1)*(+0)) is +0, whereas omission preserves -0. This is an analytic counterexample to a generic scalar omission rule, not a demonstrated reachable Julia solver trajectory. BigFloat precision/rounding and Rational overflow, nonfinite values, and BigInt ownership remain explicitly unresolved; `_is_exact` alone cannot admit them.

The ordinary direction occupies `row_solution`; residual validation writes tau/row_rhs, and BFRT solves into tau. The report correctly limits this to those writes: callbacks, refinement/recovery and aliases still prevent treating the whole producer-to-consumer path as proven. The normal caller updates scalar values before pricing weights and basis replacement (`src/dual_simplex.jl:1259–1274,1407–1443`). Support validity alone permits cancelled zeros (`src/indexed_vector.jl:1–7,42–55`); `_pipeline_vector!` can allocate/replace a cache, rebuild a full vector, or compact support. None is a read-only admission predicate.

## Work, memory and continuation assessment

There is no unnecessary NEW production computational work, allocation, or retained memory: this change is source/design documentation plus offline evidence, and Git confirms an empty src/test/.github diff against master. No added full scans, basis solves, copies, conversions, repeated runtime invariant checks, or persistent owners occur at setup, refactorization, iteration, candidate, recovery, or certification boundaries. No benchmark is required or requested for this documentation change.

Existing dual work is O(N); primal work is m multiply/subtract/store operations plus the entering addition at each reached update boundary. Accessor work includes the ownership checks in F1, an O(m) rebuild or O(s) compaction, and optional cache construction; BigInt bit complexity and constructor retention must not be inferred from unit-cost operation counts. No speedup or allocation reduction is measured or claimed.

The next S3-G plan requires one concrete ordered eligibility predicate or a stop decision. It explicitly rejects hidden full scans/new metadata, requires direct-helper/observer/alias and mutable BigInt analysis, keeps arbitrary Rational and floating types dense, and permits no launch. This is a bounded missing design decision, not acceptance of implementation or an endless audit inventory. Stopped DSE/HH/isolation/controller/import/cleanup routes and the consumed S2-E allowance remain closed.

Continuation edits and publication closure were not part of this initial review. Final resolution and binding status will be appended after verification; the initial finding and reviewed hashes remain in `results/S3-F/review.json`.

## Follow-up: F1 resolved; publication finding F2

The corrected table now counts one matrix identity comparison, six cache-buffer comparisons, and up to six lookup comparisons (two for row_solution). Its source backing is correct. Original rejected report bytes survive in `results/S3-F/report.before-review`; `review-fix.json` binds the correction and that original. The author corrected the report before initial review-file creation, so review.json records both the preserved original hash and the corrected bytes seen at record creation.

F2 (P2): the unexecuted `results/S3-F/publish.py` constructs the publication set by enumerating all files in S3-F. Exact staging-versus-that-set verification does not reject an unreviewed extra file that appeared before enumeration. Require a predeclared filename whitelist and exact directory-set equality before closure/staging. The rejected script hash is preserved in review.json. No script execution occurred during review.
