# Independent S3-F source/design review

**S3-F ACCEPTED.** Both findings are resolved. This accepts the source/design contract, bounded S3-G plan, continuation edits, and inspected single-use publication procedure; no production candidate, benchmark result, numerical launch, or broader S3 completion is accepted.

## Findings and evidence

F1 (P2), the understated support-access work count, is resolved. The final table accurately counts one matrix identity comparison, six scratch-buffer owner comparisons, and up to six lookup comparisons (two for row_solution). `src/hypersparse_pipeline.jl:14–39,71–83` supplies the source proof. The original report is preserved as `results/S3-F/report.before-review`; the five-check `review-fix.json` and all four of its bindings independently match.

F2 (P2), publication by directory enumeration, is resolved. The final unexecuted `publish.py` declares exactly fourteen evidence filenames and requires full directory-set equality and file membership before forming closure/publication or staging. Extra and missing artifacts fail this gate. It reads `review-final.json`, verifies its checks and bindings, checks exact staged names and bytes before commit, then exact committed names/bytes before push, and verifies both remote refs afterward. The original unexecuted script is preserved as `publish.before-review.py`, matching the rejected hash in `review.json`; the six-check `publish-fix.json` and both bindings match. Review did not execute either publisher. Successful publication is a subsequent result, not claimed here.

Initial rejection details remain frozen in `results/S3-F/review.json` and `review-initial.md`. The author corrected F1 before initial review-file creation; the initial record explicitly distinguishes preserved original-report bytes from the corrected report observed during record creation. No rejected evidence was erased.

All seventeen bindings in `source-contract.json` independently match. Its twelve literal/source checks agree with the inspected source but are not runtime validation. Both pre-F continuation copies exactly match their HEAD versions, and the four current-continuation hash entries in unchanged S2-E final closure/publication resolve to them. Older mapping records remain unchanged. Host records contain the same boot identity, all twenty-eight recorded groups and sessions, and empty matching-process lists. These are timestamped observations, not a continuing host guarantee.

## Numerical and support assessment

`update_duals!` (`src/dual_simplex.jl:566–591`) has mandatory cost repair and pricing-pool invalidation outside exact tableau support. Zero-row source tests in `test/partial_pricing_integration_tests.jl:75–85` and `test/dual_stagnation_cost_tests.jl:15–42` support that obligation, including the stated Float32/Float64/BigFloat/Rational{BigInt} cases. Existing tests were read, not executed; their presence is not new passed coverage.

`update_primals!` (`src/dual_simplex.jl:593–600`) updates the old basis in order and adds to the entering entry afterward, with no local alias, finiteness, or uniqueness rejection. Under IEEE round-to-nearest, (-0) - ((-1)*(+0)) is +0; omission leaves -0. The report correctly identifies this as an analytic scalar example, not a demonstrated reachable Julia trajectory. BigFloat stored precision/ambient rounding, general Rational overflow and nonfinite operands, and mutable BigInt ownership remain unproved admission conditions. `_is_exact` alone is insufficient.

Ordinary FTRAN returns row_solution, while residual validation writes tau/row_rhs and BFRT solves into tau; scalar updates precede pricing weights and basis replacement (`src/dual_simplex.jl:1259–1274,1407–1443`). The report correctly limits this local preservation statement: callbacks, refinement/recovery and aliases still require their own proof. Valid support can contain cancelled zeros (`src/indexed_vector.jl:1–7,42–55`), and `_pipeline_vector!` can construct/replace cache, rebuild values, or compact indices. It is not a read-only admission query. No whole-call ownership guarantee is inferred.

## Computational work and memory

**No unnecessary NEW production computational work, allocation, or retained memory was found.** The changed content is documentation and offline evidence; Git confirms an empty src/test/.github diff against master. There are zero newly introduced production scans, basis solves, copies, conversions, invariant checks, or persistent owners at setup, refactorization, iteration, candidate, recovery, or certification boundaries. Documentation-only changes require no benchmark, and none was requested or run.

Existing dual work is O(N); each reached primal-update boundary performs m multiply/subtract/store operations plus an entering addition. The corrected accessor count is constant owner checks plus an O(m) rebuild or O(s) compaction, with possible cache construction. A fresh O(m) support scan cannot count as eliminating the primal scan. BigInt bit complexity, scalar-object retention and fallback overhead remain future analysis obligations; no elapsed speedup or allocation saving is inferred. No update-chain or matrix-nonzero cost changes are introduced by this milestone.

## Bounded continuation

S3-G must produce a concrete ordered, read-only eligibility predicate for exactly Rational{BigInt}, or stop the consumer route if ownership/order cannot be established without new metadata or an O(m) admission scan. It explicitly analyzes direct-helper aliases/repeated indices/entering overlap, invalid or detached support, cancelled entries, callbacks/recovery, full support, and dense fallback. It preserves arithmetic order for executed entries and requires failure/ownership test oracles and a work ledger. This is a bounded decision, not implementation approval or another equivalent inventory stage.

The STATUS and roadmap edits accurately point to that decision and remap only the current S2-E continuation hashes to saved copies. S2-E remains unpromoted with its allowance consumed; the stopped DSE/HH/isolation/import/controller/cleanup routes remain closed. HH reuse remains disabled, CI remains off, and S6-AQ still requires genuinely new original evidence. No full-suite, x64, broad-S3 or performance acceptance follows.

No Julia execution, package import, compilation, numerical experiment, old-script rerun, source/test/env/CI/master edit, or messaging to other user chats occurred in this review. `results/S3-F/review-final.json` binds the final inspected files and this review, excluding only its own recursive hash.
