# Task3 qualified pending dual proposals

Task3 of the approved experimental dual-engine plan is implemented and component-qualified on codex/dual-step-experiment fromb2d74da078d5e8361fccaa4fc74e9f6abb750548. Master9940bdabe149e922afa60b5364227a7e7393bc75 and production src/test/environment/CI are unchanged. No public/default solver route, factor-update/numeric commit or recovery controller. Tasks4–6 remain open. PENDING.md and earlier admissions are historical checkpoints, superseded by this report and final evidence.

## Behavior

choose_leaving uses the exact maintained infeasible-basic set and robust current Devex scores with deterministic row-ID ties. Rejected rows expire on every committed generation change, including wrap/rebuild collisions. At most8 rejected rows route to recovery; an exhausted selection is not a certificate.

Harris/BFRT candidates use complete nonzero tableau support, unchanged user feasibility/zero tolerances and base pivot cutoff. Candidate validation inspects every potentially changed price and pending mandatory/optional flip, bounded by8 mathematical validations. Preexisting dual_bad membership blocks entry even outside future tableau support. Sign-eligible tiny pivots, nonfinite arithmetic, underflowed capacity and uncertain exhaustion remain conservative outcomes.

Entering FTRAN, original complete row residual, complete direction residual/absolute scales and _pivot_agrees are checked before planning. Flips remain pending; a nonempty set forms one aggregate RHS and at most one additional BFRT FTRAN with its independent residual check. Nonzero raw flip products that underflow to zero are rejected before BFRT. No coefficient cutoff or precision/tolerance relaxation is added.

The proposal plans changed primal values, reduced prices, entering cost shifts, Devex weights and entering/leaving/flip states into preallocated owned arrays with field masks and a unique affected union. Exactly unchanged values are omitted after validation. Complete Devex reference terms and direction-support weight updates retain positivity/finiteness. No committed numeric vector, basis/state map, invariant summary or mathematical factor base/update chain is published. Native solve work/cache necessarily changes and is counted; no whole-factor-graph immutability or rollback is claimed.

Proposal validity is generation/owner/factor/RHS/output/ticket-bound. Explicit rejection expires its stage; a completed-stage query additionally requires valid=true. A kernel call cannot revive an invalidated completed proposal through still-matching unrelated receipts. Failed validation/planning expires its stage; repeated queries do not repeat hidden solves or partial writes. Shared scalar deadline checks remain in place; no user callbacks execute inside E.

## Observed tests

Three independently admitted RED processes were executed once each: initial missing interfaces4fail/0errors/exit1; raw flip underflow1fail/0errors/exit1; lifetime regression3setupPass+4fail/0errors/exit1. Their exact source/pins/reviews/raw logs remain preserved through strict before maps. Earlier193/242/249GREEN reviews never launched. No frozen Task1/2 script or old numerical audit was rerun.

Final independently admitted GREEN: **555/555 ordinary Test assertions**, exit0, including371 unchanged Task1/2 assertions and184 Task3 assertions. Counts are observed from ordinary summaries, not a custom recorder. The whole component suite covers genuine and degenerate pivots; ties; free/fixed/upper/boxed states; mandatory/optional/multirow flips; BFRT-only and canceled rows; absent/tiny/underflowed candidates; actual8candidate/rejected-row exhaustion; outside-support invalid prices; pending cost/weight/state changes; proposal invalidation, generation/stamp wrap, stopped calls, physical capacities and unchanged source/committed snapshots. Sparse/banded/dense n8/n64 cases compare full-row reference decisions and full simulated-application equations. A tiny general2x2 basis includes nonzero old multipliers reconstructed exactly;64row slack multipliers use closed form, not dense rational factorization. Four cold native probes validate the live factor against committed B independently of reference aliases.

| Ordinary testset | Pass |
|---|---:|
| Task1 eligibility and frozen policy | 13 |
| Task1 private phase ownership and retained capacity | 41 |
| Task1 source invalid state is rejected | 8 |
| Task1 exact maintained violation sets | 31 |
| Task1 reusable sparse sets and stamped support | 13 |
| Task2 original-basis solves and pricing | 78 |
| Task2 both pricing routes on one matrix | 10 |
| Task2 complete direction residual and scale coverage | 90 |
| Task2 provenance alias and mutation boundaries | 21 |
| Task2 failed attempts and stop accounting | 18 |
| Task2 ordinary indexed residual union and overflow | 24 |
| Task2 nonordered CSC falls back without rebuilding | 5 |
| Task2 receipt identity and ticket lifetime | 19 |
| Task3 ratio eligibility and pending flips | 46 |
| Task3 uncertain is never an infeasibility certificate | 12 |
| Task3 maintained membership and leaving scores | 8 |
| Task3 bounded candidate and rejected-row exhaustion | 7 |
| Task3 rejected-row generation cannot collide after wrap | 2 |
| Task3 complete planned union and proposal lifetime | 15 |
| Task3 cost shift and changed weights stay pending | 7 |
| Task3 full-row eligibility reference and equations | 36 |
| Task3 receipt expiry, real weight writes, capacity and stop | 12 |
| Task3 general basis and nonzero original multiplier | 7 |
| Task3 multirow BFRT-only and canceled basic writes | 11 |
| Task3 scaled raw flip underflow requests repair before BFRT | 8 |
| Task3 completed proposal invalidation stays closed | 13 |

New postexit auditor: 2248 checks accepted, including all actual290GREEN pins, exact prior-source mappings, original failure preservation, actual commands/admissions, resource bounds and current production-source equality. Postexit scripts/reviews are separately bound evidence, not retroactive launch pins. Independent source/numerical admission and result review are stored in GREEN-REVIEW.md/RESULT-REVIEW.md and their exact JSON bindings.

| Run | Inclusive seconds | Resource samples | Min available KiB | Max swap KiB | Child maxRSS KiB |
|---|---:|---:|---:|---:|---:|
| red | 5.240704256 | 5 | 22143496 | 0 | 517080 |
| underflow-red | 8.332746656 | 8 | 21952832 | 0 | 669556 |
| lifetime-red | 9.281141042 | 9 | 21832776 | 0 | 666568 |
| green | 18.257440875 | 18 | 21763940 | 0 | 679740 |

These inclusive times contain process startup, loading, compilation, fixture setup and cold oracles; they are not kernel benchmarks. Final fresh host closure checks every actual known process group ANDsession and noJulia; exact group count is recorded in postcheck-host.json/closure-host.json. No native peak/live/free accounting or observer-neutrality proof is claimed.

## Review corrections and work budget

Initial review caught raw flip-product underflow and incomplete general-basis/multirow/factor coverage. The separately observed underflow RED preceded its source fix. Final coverage also exercises unsuccessful coefficient visits, all8 candidate validations, generation-wrap exclusion expiry and the completed-stage lifetime defect; its separate observed RED preceded the scalar proof/stage correction. Review-service builder failures interrupted this work; after service recovery a fresh independent reviewer admitted the exact261pin lifetime RED, then reviewed the new290pin full GREEN. No prior accepted-but-superseded approval was reused.

Nominal newly retained payload versusTask2 is **50N+28m bytes** on64bit, plus headers/scalars/allocator slack:18N proposal metadata (current UInt8 state),32N newly materialized J scratch capacity,12m RHS support metadata and16m rejected-row sets. Existing32N planned value payload,8N candidate capacity and8m row_rhs payload are reused. Physical buffers are never shortened per proposal; no old/new numeric workspace/factor copy or growing trace is added. Setup overlap/cold resizing is explicit, not a hot-path claim.

Ordinary successful no-flip proposal:1BTRAN+1FTRAN; flips require1BTRAN+2FTRAN. Each native dense result still has a complete finite/support capture and each RHS is copied/checked. The original full row residual is retained. Direction/BFRT residuals check the complete visited-row union/scales. Leaving selection scans at mostm infeasible entries; ratio validation visits support s at most8times, with explicit in-place breakpoint/group/optional sorting. Planning enumerates direction/BFRT/flip/price support and writes each changed field once. No per-candidate fullN scan or repeated row index construction. The flip_rhs_terms counter includes entering-column and rejected BFRT coefficient attempts, not just successful flips. Extra factor probes/exact oracles are cold test work only. Task1's deferred redundant cold inverse-zeroing pass remains unchanged.

No speedup, lower-allocation, native-retention or end-to-end solver improvement is established here. The review checks numerical correctness and identifies the actual work/storage budget for later integrated measurement. Required receipts/captures/sorting/residual checks remain explicit costs; no avoidable new full-vector scans, full-size per-proposal allocations or growing retained storage were found by source review in the qualified private proposal path. Small view/closure allocation behavior is not measured. Final result review records its precise evidence and limitations.

## Continuation

Old Task1/2 evidence remains frozen. Task2 source bindings resolve only through task2-before-map.json to its qualified copies; its original README closure binding maps through continuation-map.json/README.md.before-Task3. The pending Task3 README bytes are separately preserved in completion-before-map.json. All other old mappings remain unchanged. qualified-sources.json binds this exact component-qualified source/test set. Task3 closes by exact local commit only; no master merge/push or Task4 execution is included.
