# Source assessment: accuracy needed by recovery steepest-edge weights

## Decision

Steepest-edge weights have a narrower consumer role than the dual vectors used in a ratio test or certificate: they rank eligible leaving rows and initialize subsequent weight maintenance. That distinction justifies a separate consumer contract, but **does not justify replacing the current refinement gate by finite/positive weights or a small normwise residual**. No new weight-accuracy bound or cheap conditioning certificate is established by the inspected sources.

The most concrete next direction is **an explicit existing-Devex fallback in a private recovery trial when only a finite weight solve is numerically inconclusive**, retaining all basis/value checks and subsequent pivot/certificate safeguards. This would accept a different pricing mode, not an unreliable steepest-edge weight. It requires a separately reviewed design and tests; it is not implemented or numerically admitted here. The shared precision-transfer caller must remain unchanged in the first narrow design.

No Julia/query/parser/import/compile/numerical experiment, candidate or production/test/environment/CI/master change. This is the requested source/analytic assessment after the failed homogeneous cleanup, not a repeated qualification or general impossibility proof.

## Evidence and immediate consumers

Relevant current sources are bound in source-evidence.json, with96 source/analytic/host checks and24 readtime hashes;71 current production files were byte-compared with master. Actual diagnostic HEAD aad722caf65fbefc09e9a38eca887ab2a1a89581, master c0fa748ffa61ccb7c1caaf248c40324f60bc737b. Fresh host identity inspection covers all727 prior process groups AND sessions and no Julia. There is no launcher or run authorization in this assessment. The source collector is copied after its execution as source-review.py; that copy is not a retroactive self-input pin.

| Boundary | Current source and behavior | Accuracy consequence |
|---|---|---|
| Private recovery basis | simplex_recovery.jl94–130 constructs independent factor/storage, recomputes, checks `_finite_workspace` and `_recomputed_basis_reliable`, then rebuilds weights | Weight failure is a distinct late gate after primal/basic-cost residual checks. Passing these earlier RHS checks does not validate every inverse-row RHS. |
| Weight reconstruction | simplex_recovery.jl133–150: each unit BTRAN must pass actual refinement, then `dot(direction,direction)`, finite/positive guard, floor1e-4 | The unit direction is local temporary data; only its scalar norm enters pricing_weights. Failed rebuild returns before publication; partial weights stay private. |
| Precision transfer | simplex_precision.jl217–218 also resets and calls the same helper, throwing on failure | A blanket helper change silently affects another lifecycle, all supported target precisions and budgets. Scope must be explicit. |
| Candidate ranking | dual_simplex.jl296–317 and simplex_pricing.jl462–501 compute current bound violation, then weighted score | Weights affect order, ties and selected path; row eligibility is evaluated from bounds/primal state. Finite arithmetic adds hazards described below. |
| Selected inverse row | dual_simplex.jl1609–1657 solves a fresh unit BTRAN, prices it, checks finite vectors and `_dual_row_residual_ratio`, with existing correction/refactor handling | Stored weight is not reused as rho or as the tableau row. The new actual row is independently checked before ratio testing. Native residual acceptance is a mixed absolute/relative check, not the same componentwise SolveQuality criterion. |
| Selected weight validation | dual_simplex.jl1659–1674, simplex_pricing.jl301–316 compare stored weight with `dot(rho,rho)`, switching/restarting with Devex on disagreement | A factor-two heuristic validation exists. Auto validation and fixed floating DSE paths differ; it is not an independent bound on the unknown exact norm. |
| Weight propagation | dual_simplex.jl903–917 and975–995 use old stored weights plus tau from `:weight_ftran`; Devex uses a different reference update | Approximation is not confined to a one-time ranking: errors can propagate to later weights. Selected validation does not inspect every stored weight on each step. |
| Pivot and result | dual_simplex.jl1680–1900 retains ratio cutoff, infeasibility proof, FTRAN residual, pivot agreement/validation and finite-step checks;2293–2337 retains original-model feasibility/optimality certification | Ranking weights do not directly prove a pivot or result. These safeguards must remain unchanged; final certification does not excuse unsafe selection, missed candidates, cycling or excessive work earlier. |

The current `_rebuild_recovery_weights!` has two literal production callers: `_recovery_trial` and `_transfer_precision`, in addition to its definition. This is a source caller inventory, not a guarantee about arbitrary external/private API calls. Ordinary same-basis refactorization preserves existing steepest-edge weights (simplex.jl436–442); it does not invoke this rebuild.

## Why small normwise residual cannot certify the scalar weight

Let the exact inverse row y satisfy `B' y=e_i`, and let yhat be computed. With `r=e_i-B' yhat`, the exact error is `y-yhat=B'^(-1)r`. A bound on the residual alone is insufficient without information about the inverse/conditioning. This is also the distinction made in the [LAPACK error-bound discussion](https://www.netlib.org/lapack/lug/node81.html); its forward-error estimate involves an inverse action and is not just BERR.

An analytic exact counterexample, **not a solver fixture or numerical run**:

* `B=diag(2^-80,1)`, `rhs=e2`, exact `y=(0,1)`.
* Proposed `yhat=(2^20,1)` has residual infinity norm2^-60, below current Float64 solve tolerance2^-44; normwise residual normalized by `||B||inf*||yhat||inf` is2^-80.
* Exact squared weight is1, while the proposed squared norm is2^40+1. Its homogeneous first equation has componentwise error1 and is caught by the current criterion.

This does not say that the captured runtime basis has that conditioning. It disproves the general implication “small normwise residual means an accurate weight.” The existing componentwise criterion itself is also a backward-error check, not a universal forward-error certificate.

A sufficient alternate mathematical route would bound `delta >= ||y-yhat||2`. If Y is an enclosed computed norm, the exact squared norm lies between `max(0,Y-delta)^2` and `(Y+delta)^2`, with outward rounding and dot/norm rounding included. Obtaining delta from `||B'^(-1)||2*||r||2` requires a justified inverse bound; an unqualified rcond estimate is not automatically such a bound. No inexpensive bound is present in the inspected consumer. Repeated solves or an inverse/condition computation could cost as much as the work this route aims to save.

The1e-4 storage floor also matters: stored weight already intentionally differs from an exact squared norm below that floor. Therefore the selected factor-two test is a fallback heuristic, not a universal definition of acceptable reconstructed norm error. Any new formal scalar-error contract must state whether it bounds the unmodified norm or the floored pricing value.

## Why “any finite positive weight is harmless” is too strong here

In exact arithmetic, a positive weight changes ranking among eligible rows without changing the bound-violation predicate. The current fixed Float32/64 path nevertheless computes `violation^2/weight`, starts at score0 and accepts only a strictly greater score. A squared violation or quotient can underflow to0; if all eligible scores are0, leaving_row stays -1. Extremely large finite weights can therefore prevent the selected-row validation from being reached. Overflow/Inf scores can also change ties and ordering.

For example, the source-derived IEEE Float32 expression with violation2^-23 and weight2^120 gives mathematical score2^-166, below the minimum Float32 subnormal2^-149. This is an analytic range observation, not a new executed Julia case or a claim about the captured RHS. Auto uses the existing scaled-score/first-eligible path; partial_pricing_edge_tests.jl85–108 statically covers extreme scores in auto, not every fixed-pricing route. A new consumer contract must account for these distinctions rather than claim all positive arrays preserve selection behavior.

Also, a fresh selected rho may be approximate and its weight comparison is not an independent exact oracle. Weight errors can alter subsequent update chains, fallback/reset events, recovery work, callback observations, iteration limits and degeneracy behavior. No identical trajectory or bounded iteration increase follows from changing the weights.

## Concrete narrow follow-up: decline DSE, retain the valid basis with Devex

The source already supports this mode change. `_switch_dual_pricing_to_devex!` (dual_simplex.jl917–935), `_reject_auto_weight!` (simplex_pricing.jl229–237), reset_devex! (simplex.jl217–223), and `_effective_pricing`/`_weight_pricing` handle mode flags, reference reset and temporary pricing. Existing tests include inaccurate selected weights, nonfinite DSE recovery and update-overflow fallback. These are relevant existing tests, not new execution or coverage of reconstruction-time fallback.

A separate first design should be restricted to Float32/Float64 **private dual-recovery `_recovery_trial` reconstruction** when its original basis/primal/basic-price checks passed and the weight unit result is finite but not reliable. It should:

1. Keep the strict DSE solve/refinement and all original tolerances. Never publish a failed weight as steepest-edge.
2. Distinguish finite numerical inconclusiveness from stop/deadline, callback/logger exception, nonfinite direction/quality, invalid basis or other work failure. The current Bool return alone does not distinguish these causes; blindly treating any false as permission to fall back is unsafe.
3. Clear any partial DSE prefix by a complete owned Devex reference/weight reset, preserve the correct mode/temporary-return fields, invalidate affected pricing pools, and keep ordinary Devex update validation. Do not silently reinterpret partial DSE values as Devex.
4. Preserve stop/exception provenance and recovery publication ordering. `_recovery_trial` shares progress/diagnostics with live state; calling the existing switch helper is not by itself proof of private event/log/callback behavior. `_publish_recovery!` observers occur before state adoption; copied pricing flags and cancelled/throwing publication need explicit tests.
5. Leave primal recovery, shared precision-transfer behavior, exact/multiprecision types, ordinary refactorization and all ratio/pivot/certificate/cleanup paths unchanged in the first scope. The first design must identify the actual dual-recovery route explicitly; it must not infer that solely from configured options or a possibly absent/stale pricing state across phases. Temporary Dantzig still maintains its saved weight mode: `_weight_pricing` can differ from current selection.

This follows an existing numerical policy of falling back to a heuristic rule rather than pretending to have accurate steepest-edge geometry. It does not prove that a public solve will finish faster or succeed on the captured problem. The failed KLU complete-weight benchmark remains rejected; a Devex run would be a different pricing workload and cannot count as successful steepest-edge qualification.

Prospective tests should include finite-unreliable first and late rebuild rows, a partial weight prefix, a valid completed steepest-edge rebuild with no fallback, stop/throw before and after the failed row and before publication, mode/state copying for fixed/auto/temporary pricing, unchanged precision-transfer behavior, truly invalid basis/primal/dual directions staying rejected, pool invalidation and no missed eligible rows. Whole public native iterations and final original certificates remain necessary before integration. No new candidate/test/driver or numerical admission is created here.

## Work and memory budget

Current complete rebuild of m rows performs m initial unit BTRANs, up to3m correction BTRANs under the pinned default max_refinements=3 (in general at most m*policy.max_refinements; not an observed universal count), per-row `_basis_matrix!` validation/count/fill O(m+nnzB), residual quality passes, RHS zeroing, norm dot and stop checks. Generic residual scratch/caches and wide fallback are additional; this is not a complete native/import/observer work budget. In the saved rejected runtime case only the first row was actually attempted, with one correction; nominal128 rows were not completed.

A lower-cost scalar qualification could save work only if its estimate and validation are cheaper than these passes. A full inverse or repeated condition-estimation solves would add memory/solves and could merely move the cost. No such optimization is admitted.

A finite-unreliable-to-Devex fallback after k attempted rows would retain all already consumed work; it could avoid the remaining m-k unit solves/refinements. Reset costs O(N+m): reference false fill, m basic reference writes, weight-one fill and framework/cache bookkeeping; invalidating a pool retires its indices, and diagnostic/log callbacks remain. Existing buffers suffice; mode/reason metadata can be scalar and no persistent inverse, graph cache or per-row error array is inherently required. This is a source-derived prospective budget, not a measurement or exact allocation promise. Different later Devex pivots may add iterations, updates, refactors or recovery; net runtime and allocations remain unknown.

No new production work or retained-memory cost is introduced by this source-only assessment. No runtime allocation/time benchmark is warranted for the documentation. If a fallback candidate is later prepared, review must cover work at reconstruction failure, each later Devex iteration, reset/pool scans and exception/publication retention, with a short end-to-end comparison that labels the changed trajectory honestly.
