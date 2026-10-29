# First rejected KLU weight RHS — bounded diagnosis

User request: identify why the weight experiment was rejected. This is one fresh diagnostic attempt, not a repeat or acceptance of the frozen weight benchmark. No production/test/environment/CI/master edits.

## Scope and invariants

Use only saved `runtime-30000` B0 and unit RHS row 1, matrix hash `7b6ab789d7f49d73ec163eee3e2c5c5e9207dadd5f66a3b31972755b367c6d5c`. Three private arms: unchanged native KLU, unchanged graph-local KLU, ordinary `lu(B)` UMFPACK. Existing vendor/export/FTRAN/shared-BTRAN files are byte copies of the frozen experiment. Factor input ownership is unchanged. KLU controls are unchanged (tol=1, BTF, AMD, sum scaling). Capture UMFPACK controls; installed Julia disables UMFPACK built-in refinement by default (IRSTEP=0). These backends do not have identical factorization controls.

Use actual production `refine_basis_solve!`, `solve_quality!` and default Float64 legacy policy: tolerance 256eps = 2^-44, max_refinements=3, solve_refinement=false. No threshold/pivot/tolerance/precision changes; no hidden cleanup, retry or extra correction. The algebraic `LinearProblem`/workspace is a holder for saved A/basis, not a new LP solve. There are no FTRANs, simplex iterations, model parses or benchmark windows.

A new diagnostic-only TraceFactor method records fixed preallocated before-point, correction RHS and correction output vectors for at most three correction BTRAN entries. It forwards exactly once to the original selected factor. No original method overwrite. Stop counter always returns false; no arbitrary callback. The refinement destination is explicitly bound to the trace's point field. Per-entry three O(n) vector copies are diagnostic overhead, not performance-neutral observation.

## Questions and oracles

For each initial/final point and each attempted correction, record actual SolveQuality fields, reconstruct plain/compensated/wide branch from unchanged sources, and assert exact quality/residual agreement. Reconstruct a trial after return using the original ordered scalar additions; compare input correction RHS bits with production residual. Record first applicable return gate and assert that actual subsequent/final point agrees with inferred adoption or rejection. Trial quality reconstruction is explicitly post-return diagnostic evaluation; it is not claimed as an instrumented production quality event.

Independently evaluate componentwise residuals in the same 137-bit residual-only precision chosen by production's wide oracle for this dimension; Float64 factor, corrections and destination remain unchanged. Select up to three equations per snapshot: maximum componentwise ratio, first ratio above unchanged tolerance, maximum absolute residual. Save their complete original CSC-column coefficient and solution bits, original basis variable and RHS bits. Python Fractions then recomputes these selected dot products and ratios exactly, independently of Julia quality routines; it does not certify every unselected equation. Global small normwise residual is not a substitute for componentwise correctness.

Ordinary Test verifies input/tape/library hashes, source-held policy, same B0 in the production workspace, trace capacity, reconstructed decisions and input preservation. KLU's expected unreliable return is a passing diagnostic expectation. UMFPACK outcome is recorded without requiring it to pass. Nothing waives previous failed controls or promotes a candidate.

## Work and memory bound

One saved tape load and B assembly. Exactly three initial factorizations (two KLU, one UMFPACK), three initial BTRANs and at most nine genuine correction BTRANs total. No extra basis solves in residual or exact-equation diagnostics. At most eight snapshots per arm (24 total); each calls actual quality, one explicit raw component pass, at most one compensated branch replay (and wide fallback if needed), then one 137-bit component pass and ratio scan. Actual refinement additionally evaluates initial and at most three trial qualities per arm (up to 12). These O(n+nnzB) diagnostic scans/conversions are deliberately charged and not proposed for production.

Trace storage: nine Float64 length-n arrays per active arm = 72n bytes, plus destination/initial/final/RHS, refinement scratch, selected-equation records and one post-return trial. Three retained witness arms keep initial/final plus at most nine copied trace arrays each: at most 264n bytes (~7.17 MiB for n=28453), plus basis/RHS (~0.43 MiB). Native factors are not serialized; each arm's workspace/factor is released before the next and GC is outside the actual refinement. Local graph/native context and ordinary UMFPACK memory are additional; no complete native ledger or zero-allocation claim. BigFloat residual arrays and intermediates are transient and bounded by this one sparse basis; resource guards remain authoritative.

Write portable TOML with selected complete equations and local plain-array Serialization witness, with hash/size. Input A/B/basis preservation checked after each arm. Preparation time/bytes/events are descriptive and include first-use compilation, never speedup evidence.

## Admission / execution / closure

Fresh boot+start_ticks+command identity check, all previous 723 groups AND sessions plus any new groups, no Julia, RAM>=6GiB, swap<=1GiB. Pin actual source/project/runtime/vendor/tape/command/review files. One process: Julia/BLAS1, gcthreads1,0, heap2GiB, VM8GiB, compiled-modules=existing, Pkg precompile off; common ceiling1800s. No old scripts rerun. Independent concrete admission must accept before launch. Result exit0 is necessary but not sufficient: check ordinary Test summary, complete three arms, exact selected fractions, actual gate/adoption consistency, guards/pins and process closure. Independent result/work-memory review follows. Preserve any failed attempt; do not silently retry or change the plan. Failfast exact staging/commit/push diagnostic branch only after PASS closure; master unchanged.
