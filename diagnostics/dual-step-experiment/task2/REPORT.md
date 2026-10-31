# Task2 factor solves, pricing and complete residual checks

Implemented only Task2 of the approved experimental dual-engine plan, on codex/dual-step-experiment from42d88ae5. Production master remains9940bdabe149e922afa60b5364227a7e7393bc75. No src/test/environment/CI change, public solver route, pivot/ratio/commit/recovery controller or production promotion. Tasks3–6 remain open.

## Behavior and ownership

basis_solve! uses existing native Float64 PFI forward/transpose operations for FTRAN, BTRAN and aggregate BFRT, with attempt counters before forwarding, including exceptions. Each result receipt binds phase owner, value/basis generation, per-slot RHS ticket, output owner/support capture and current factor object ID. Dense native results undergo one complete finite/support capture. A stopped or failed call does not become a valid ordinary step. Foreign exceptions retain identity; numerical factor failures invalidate the factor and all dependent evidence.

price_row! consumes the existing once-built immutable RowAccess, selecting indexed pricing at q<=nnz(A)/4 and CSC otherwise. Nonordered CSC falls back to CSC. Both paths check finite products/sums, track exact support and clear tracked values on failure. No per-call row-index construction, support sorting, coefficient copy or separate full tableau support scan is added.

check_row! deliberately retains the complete production _dual_row_residual_ratio criterion. check_direction! accumulates original-B residuals and absolute scales in ascending nonzero basis-coordinate order, checking the marked union of nonzero RHS rows and every visited basis-column row, including canceled-to-zero residuals. Existing zero/pivot/256eps thresholds are retained; nonfinite scales/residuals are rejected. Native factor solving remains dense; neither the row check nor the producer capture is claimed removed.

The phase and scratch are private. Coherent owned writers invalidate evidence. Unknown direct scratch/index/model mutation requires invalidation, discard and fresh import from an unmodified source; numeric invariant rebuild alone repairs only committed membership. No arbitrary external-mutation/cache-confinement proof is claimed. This Task2 contract narrows the earlier generic invalidate/rebuild wording for kernel metadata. See WORK-MEMORY.md.

## Observed verification

One independently admitted RED process: exactly6 expected missing-interface failures,0errors,exit1,5.251752785s inclusive. No implementation existed for those interfaces at RED. No RED rerun.

One independently admitted GREEN process:371/371 ordinary Test assertions,exit0,14.238110294s inclusive. This includes106 unchanged Task1 regression assertions and265 new Task2 assertions: original-basis solves/pricing78, both pricing routes10, complete residual/scale90, provenance/alias21, attempt/stop18, indexed union/overflow24, nonordered CSC5, receipt identity/lifetime19. Cases cover sparse/banded/dense n8/n64, known dyadic equations, cold BigFloat residual auditing, subnormal/signed-zero/cancellation, near-threshold comparisons to the full production criterion, zero-RHS ordinary receipt rejection, canceled-row scales, finite-input overflow cleanup, aliases, generations/tickets/wrap and actual owner replacement.

Test-only throwing/perturbed factor types prove dispatch/attempt accounting and rejection sensitivity. Perturbed solves forward the genuine native operation before injection. They do not prove a real native defect, rollback, general factor lifecycle, callback neutrality or full solve correctness.

All149 exact GREEN launch pins remain unchanged. New postexit auditor passed498 checks, including historical exact source mappings, actual commands, original failure preservation, resource samples and current production-source equality. Postexit scripts/reviews are separate evidence, not retroactive launch pins. Fourteen GREEN resource samples had minimum available RAM21874848KiB, swap0; process child maxRSS650700KiB. Terminal full792 process groups ANDsessions are absent and no Julia remains. Inclusive wall times include loading/compilation/setup/checks and are not kernel benchmarks.

## Review and cost scope

Initial140-pin source review was rejected for an overbroad unknown-writer recovery claim and missing adversarial cases. The rejected review and all initial bytes remain in before-coverage-review. Revised147-pin tests still lacked one explicit indexed canceled-row witness; those bytes remain in before-canceled-row. No initial/revised GREEN attempt ran. Final149-pin source/numerical admission accepted38 checks, with no unresolved findings and no unnecessary new hot full scans or growing memory found. Independent postexit result review is stored separately in RESULT-REVIEW.md/result-review.json.

Relative to Task1, three private RHS value/index buffers add48m bytes of payload on64bit plus fixed receipt/counter metadata. Ordinary hypothetical no-flip work is1BTRAN+1FTRAN, their2m RHS-copy/finite entries and2m dense-output finite/support capture entries, indexed-or-CSC pricing, the retained full row residual criterion, and marked direction residual/scale checks. External RHS comparisons add a declared m-entry pass; passing the saved private owner avoids it. Failure-only full capture cleanup and stamp wrap remain bounded. No growing logs or old factor graph retention are added to kernels. Test setup/BigFloat audits remain outside any claimed hot-path measurement. Task1's redundant cold N-entry inverse zeroing pass remains deferred unchanged.

There is no speedup, lower-allocation, native-retention or end-to-end work-budget claim. This slice establishes kernel correctness/ownership and exposes work for later integrated measurement. Review found no unnecessary new computational work or retained memory in the coherent private kernel path; the required RHS copies/captures and retained row check are explicit costs, not performance savings.

## Frozen evidence and continuation

All Task1 raw/scripts/reviews and Task2 admitted run evidence are preserved; never rerun old scripts against changed experimental sources. Task1 historical source bindings resolve through task1-before-map.json. The original README binding of Task1 closure resolves only through continuation-map.json/README.md.before-Task2. qualified-sources.json binds the exact Task2 source/test bytes. No master merge or push is included in Task2 completion.
