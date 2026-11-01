# Task4 journaled publication and bounded flat recovery

Task4 of the approved experimental dual-engine plan is implemented and component-qualified on `codex/dual-step-experiment`, based on `bf4b8656e909bfaaa80e08d0bc77a8c78d51272b`. Master `9940bdabe149e922afa60b5364227a7e7393bc75` and production src/test/environment/CI are unchanged. This is an opt-in experimental Float64/native-PFI/fixed-Devex component. No public/default solver routing, original-model certificate, master merge or push. Tasks5–6 remain open.

## Publication and failure behavior

`commit_step!` requires a complete generation/owner/factor/RHS/output-bound proposal, deadline/iteration/update-ceiling eligibility and fixed journal capacity before mutation. It gathers first-write old values only for the planned affected union, forwards the real factor replacement, writes checked numeric values/states, updates basis/inverse/selective membership and scalars, and ends the journal. The ordinary route admits no caller code in the write interval. Completion events carry immutable scalar data and run after commit outside the numerical/rollback handler; their original exceptions propagate while the already committed state remains committed.

An unsuccessful update may partially change a native factor. The journal restores private numeric vectors, states, basis/inverse and selected scalar values in their original containers; all factor/summary evidence becomes invalid. The old factor is never used for another solve. This is value restoration, not native factor rollback. Pre-refusal does not mutate a factor. Timeout after a damaged update stops without forcing late repair or returning an unverified solution payload.

## Recovery and boundaries

`run_phase!` owns one flat loop with Normal, CorrectRow, CorrectDirection, RebuildBasis, Reprice, ResetDevex, LegacyBoundary and Terminate stages. `recover!` performs one stage action. There is no recursive public solve or whole dual retry. Up to three genuine same-precision correction solves per failed equation/round use the complete original-B residual and fresh quality checks. A corrected row invalidates dependent pricing/ratio/direction; an entering-direction or BFRT correction retains valid independent dependencies. Nonfinite or partially assembled residuals cannot enter a correction solve.

At most two rebuild/reprice rounds belong to a stuck decision, with eight entering candidates per row and eight rejected leaving rows per basis generation. Generation changes do not reset the rebuild episode; only an accepted pivot does. Rebuild assembles the current committed basis, attempts refactor before publishing validity, stages primal/price values in existing proposal arrays, then publishes and resets Devex/classifies once. Cost-only restoration stages the working-model objective and reprices with one BTRAN, without unrelated FTRAN/refactor/reset. All attempts, including throws, are monotone counted work.

The original scalar deadline/start, phase offsets, local remaining iteration limit and requested update ceiling are preserved. A factor ceiling or zero-step stagnation requests synchronized maintenance before more ordinary work. A terminal or iteration-limit decision avoids unnecessary maintenance. Exhaustion returns at most one synchronized owned working workspace, or honest no-payload termination. A transferred workspace consumes named engine entry points. Private raw aliases remain subject to the ownership-use contract. Task5 must normalize legacy scratch, implement the actual handoff/cleanup and obtain the original-model certificate; Task4 `PrimalFeasible` is a working-model boundary, not OPTIMAL.

## Observed tests and preserved failures

Tests were written before implementation. The independently admitted missing-interface RED observed six expected failures, zero errors, exit1. First GREEN failed during loading before any test: reserved Julia keyword `export` was used as an argument name. Original source,344 pins, approval and raw exit1 are preserved. A separate minimal five-site rename to `export_workspace`, with unchanged tests/expectations/policy, received a new367-pin admission before GREEN2. Neither an old launcher nor a numerical auditor was rerun.

Final GREEN2: **709/709 ordinary Test assertions**, exit0: **555 unchanged Task1/2/3 assertions plus154 Task4 assertions**. No custom recorder or manual Test stack. All source/driver/runtime pins stayed unchanged. Genuine same-precision equation tests are separate from forwarding fault-injection accounting. The tests validate partial actual update then exception; real write then first/middle/last sentinel; capacity/stale/deadline refusals; wrap; postcommit exception identity; immutable event data; invalid-factor no-solve; bounded failed refactor/correction recurrence; one honest exhaustion boundary; offsets/local limits/update ceiling; cost-only restoration; aliases and consumed owners. BFRT recovery specifically retains row/entering output tickets and counts1BTRAN+1enteringFTRAN+2BFRTFTRAN including one actual correction. Cold full-scan membership, exact tiny equations, independently simulated numeric application and native factor probes check outcomes.

| Task4 ordinary testset | Pass |
|---|---:|
| Task4 commit equals independent simulated application | 26 |
| Task4 factor failure preserves point but never claims rollback | 13 |
| Task4 first middle last numeric failures restore all fields | 21 |
| Task4 refusal deadline wrap and postcommit exception | 18 |
| Task4 real same-precision correction equations | 10 |
| Task4 correction reuses successful dependencies | 14 |
| Task4 bounded recurrence invalid factor and honest boundary | 15 |
| Task4 ceiling offsets local limit and cost restoration | 14 |
| Task4 correction aliases and consumed publication owner | 11 |
| Task4 BFRT correction retains row and entering direction | 12 |

A first331-pin source review rejected missing BFRT recovery coverage before any GREEN launched. Original rejection and source/tests are preserved; the test-only forwarding mode and slot3 dependency/count/oracle test closed that finding. Independent review also approved the later five-site loading fix and its new concrete run. The initial source review missed the reserved-keyword syntax error; the failed process is retained rather than relabeled a numerical result.

New postexit checker: **1080 checks accepted**, covering all367 actual GREEN2 pins, exact initial RED and rejected331/failed344 bindings via strict before maps, all observed ordinary summaries, commands/admissions/resource bounds and fresh full process groups ANDsessions/noJulia. Postexit scripts/reviews are separately hashed evidence, not retroactive launch pins.

| Process | Inclusive seconds | Samples | Min available KiB | Max swap KiB | Child maxRSS KiB |
|---|---:|---:|---:|---:|---:|
| red | 5.251853830 | 5 | 21984724 | 0 | 526732 |
| green | 5.257454594 | 5 | 22001232 | 0 | 522660 |
| green2 | 21.299166633 | 21 | 21678596 | 0 | 717272 |

Inclusive process time contains loading, compilation, setup and cold oracles; it is not a kernel benchmark. Controlled-clock injection proves branch/unwind order after a genuine factor call; it is not captured real deadline latency. The real time0 deadline and retained original start/offsets are separately tested. No actual backend defect, observer neutrality, native peak/live/free or historical CI cause is established.

## Work and memory

New nominal retained payload is **16N+8m bytes** on64bit plus fixed metadata, headers and allocator slack: one rejected-entering SparseSet and one correction vector. Existing journal, proposal value staging and indexed RHS/residual storage are reused; no whole factor/workspace copy per normal pivot or growing trace is added. Physical vector capacities do not shrink per step. First-write gather, numeric publication and selective classification each traverse the affected t-ID union/fields. The conservative failure-only undo restores even the unwritten gathered tail, an O(t) tradeoff that avoids another hot write-tracking pass/mask.

Original native PFI direction counting/packing, ETA allocations/retention, dense finite/support capture and row/direction residual work remain explicit. Rebuild/reprice performs full basis validation/assembly, one FTRAN, one cost BTRAN, complete equation checks and O(N+z) price/classification/reset work; those are cold recovery costs. No hidden backend/import/allocation/free budget is inferred from entry counters. Required correctness work is justified; independent source admission found no unnecessary new per-pivot full-vector scans, factor graph copies or unbounded retained state. The existing deferred redundant cold inverse zero/fill from Task1 remains unchanged. Allocations and total-solution performance are unmeasured here; no speedup claim. Task6 will judge integrated total cost.

## Evidence and continuation

`qualified-sources.json` binds the actual qualified component/test sources. Task3 previous live source bindings resolve only via `task3-before-map.json` to its frozen qualified copies. Its root README closure/publication/review binding resolves only to `README.md.before-Task4` via `continuation-map.json`; all older maps remain unchanged. Initial Task4 RED test/source versions use the preserved Task3 source or `before-green-tests`; initial331 review versions use `bfrt-before-map.json`; failed344 recovery source uses `parse-before-map.json`. Exact reviewed manifest copies originally named under /tmp map by byte hash to persistent original manifests via `review-copy-map.json`; no /tmp source is required for replaying evidence. All historical raw/scripts/reviews/checks remain frozen.

Final independent result review, fresh PASS closure and exact complete local staging/committed names/blobs are required before the Task4 local commit. No push/master change or Task5 execution is included.
