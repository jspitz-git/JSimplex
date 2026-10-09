# Simplex data movement implementation plan

> **For agentic workers:** Use superpowers:executing-plans; execute sequentially with one numerical Julia process. Each accepted production change requires independent code/work/memory review.

**Goal:** Investigate four approved sources of unnecessary work without changing numerical behavior.
**Architecture:** Start with measured call counts and real states. Prefer call-local reuse over cross-iteration caches; preserve failure atomicity, all safeguards, arithmetic order and generic precision fallbacks. Reject experiments without representative benefit.
**Tech Stack:** Julia 1.13, Python guarded runners, TOML/JSON evidence.
**Spec:** User-approved four-point proposal in this conversation; prior evidence in diagnostics/dual-pricing-residual/README.md.

## Global constraints
- Baseline 495da30; existing codex/simplex-shared-work worktree. User files/environments stay untouched.
- One Julia/BLAS thread, one numerical process, 8 GiB VM, available RAM >=6 GiB, swap <=1 GiB. Bounded diagnostics; no forbidden large inputs.
- No changed pricing decisions, tolerance, precision, coefficient dropping or weakened certification.
- English artifacts; Czech communication. Verified fixes commit/merge/push under standing authorization; preserve worktrees and failed experiments.

## Review focus
- Callback/cancellation boundaries and borrowed scratch lifetime: no stale basis reuse.
- Signed zero, NaN/Inf, mismatched shapes and generic AbstractVector behavior.
- Recovery scratch aliasing, failure rollback, and nested recovery calls.
- All manager families and representative precisions; no HH-only generalization.
- Legacy snapshots are diagnostic states, not guaranteed current-version checkpoints; distinguish fresh refactorization from exact continuation.

## Task 1: Basis assembly during correction
Files: src/simplex.jl, src/legacy_dual_correction.jl; diagnostics/simplex-data-movement/reproduce/inventory.jl.
- [x] Measure assembly frequency/time, repeated unchanged bases within one iteration, and correction call paths in runtime dual and medium prefixes/cleanup.
- [x] If reuse is material and safe, write failing work-count plus stale-state/cancellation tests before a minimal call-local reuse change. Otherwise record a rejection with evidence.
- [x] Differential validation of numerical traces and native residual decisions; measure assembly/solve counts independently.

## Task 2: Prepared direction handoff
Files: src/huangfu_hall_factorization.jl, src/triangular_spikes.jl, src/triangular_factorization.jl, src/factorization.jl.
- [x] Compare native finite/equality/copy traversals on sparse/dense representative HH directions and the common FT/SS/BG path; retain already verified PFI direct-packing measurements without repeating unchanged kernels.
- [x] Test exact equality, signed zero, nonfinite rejection, aliasing, correction invalidation and generic fallbacks before adopting a fused pass.
- [x] Measure prepared hit/miss paths; accept only a supported improvement and preserve all existing checks.

## Task 3: Temporary recovery vectors
Files: src/primal_updates.jl, src/legacy_primal_point.jl, src/legacy_dual_correction.jl, workspace scratch definitions.
- [x] Attribute allocation to setup, ordinary pivots, native correction, and cleanup; identify actual hot copies before adding retained buffers.
- [x] Implement reusable scratch only after failing allocation/atomicity tests; explicitly account for lifetime, nested calls and retained bytes.
- [x] Verify equivalent rollback and final certificates; reject cold-path changes without a useful measured tradeoff.

## Task 4: Later medium states
Files: diagnostic harness and results only unless evidence supports a separate fix.
- [x] Inventory existing phase and postsolve snapshots and their provenance.
- [x] Profile bounded continuations from usable late states; separate restored factor history from fresh initialization and include both algorithm origins.
- [x] Compare per-iteration work, solves, refactorization, correction and allocation with early prefixes. Do not infer hours-long behavior from early prefixes or claim historical replay equivalence without proof.

## Final verification
- [x] Relevant targeted/generic/recovery regressions and broader semantic suite; record incomplete full-suite attempts honestly.
- [x] Full runtime dual and bounded medium comparisons; original feasibility/optimum when completed.
- [x] Independent numerical/work/memory review and compact English results.
- Integration procedure: commit verified changes, fast-forward master, run focused checks there and push under standing authorization; preserve the experimental worktree.

## Execution ledger
- Baseline/source inspection: cached CSC storage already avoids repeated allocation; it still validates/reassembles values. Native correction already reuses most quality buffers. Triangular prepared handoff does not have HH's separate whole-direction finite check. These existing features must not be claimed as new optimizations.

- Initial runtime inventory completed OPTIMAL at 54,591 iterations with original feasibility. It counted 11,430 basis assemblies and 394 same-iteration repeated basis-index sequences; 55 tableau recovery calls took 0.154 s inclusive. The instrumentation's strong workspace dictionary and a SIGUSR1 diagnostic profile peek contaminate performance timing, so this is call-count evidence only. The process exited normally; no termination signal was sent. The follow-up inventory uses weak keys.
- Initial prepared-direction timings are invalid: unconsumed predicate results permitted dead-code elimination. Preserve the attempt, consume predicate/copy results and vary one equal input pair on every repetition before interpreting timings.
- Native point certification's allocation-budget test failed as expected at 49,512 B (Float32) and 98,664 B (Float64) for 2,048 rows/columns. Inspection also found an unconditional activity slice and Bound array; defer those until fallback while preserving row checks.

- Completed all four corrected inventory cases and six historical factor replays. Late cleanup has 512 point certificates per512 steps (~55s inclusive under instrumentation); assembly is ~0.06s. Rejected new basis caching as unsupported here. Full-time inventories include profiling/GC and cannot be compared directly with isolated warmed kernels.
- Certificate scratch and unpublished triangular handoff changes pass148 and422 targeted checks respectively;15,689 broader semantic checks also pass. Native certificate allocation falls to32B in the conclusive synthetic cases. Late actual certificates retain existing native fallback allocations.
- Independent review found no numeric/ownership blocker, but identified HH early-mismatch work. First-entry mitigation removed index1 regression; a bounded-block prototype will cover early non-first mismatches before final acceptance.
- The initial Float32 certificate benchmark was stopped only in its own process group because a32,768-row synthetic initialization selected dense native LU. Its failure is retained; corrected benchmarks keep Float32 dimensions bounded.

- Final HH implementation stops prepared comparisons after a mismatching 128-entry block; redundant comparisons are bounded by127. Final120-case production benchmark consumes all outputs and confirms zero allocations. Large hardware vectors improve; tiny Float64 misses cost up to about3ns more and are documented.
- The fallback activity copy is removed with a view feeding an owned Bound vector. The regression budget failed at157,112B before the change and passes in the final252-assertion focused suite.14 traversal-budget checks and4,091 compiled manager/allocation checks pass.15,689 final semantic checks pass.
- Full-suite attempt hit300s guard in LLVM compilation; not counted as passing. An accidental compile=min manager run had3,558passes and2allocation failures; corrected normal compilation passed. Both attempts retained.
- Independent completed-evidence review verified source identity, frozen reference, measured ratios and work/memory accounting. Final100external solves, two cleanup-origin comparisons and full runtime comparison remain pending.

- All100external combinations pass with original feasibility and reference optimum; iterations/objectives/input hashes/status match prior certified runs exactly. Both final128-step medium cleanup origins match recorded baseline fingerprints. Current late certificate allocation36,236,184→18,784,280B; observed3–5%median timing change has overlapping samples. Independent review confirmed provenance and qualified the timing interpretation.
- First final runtime harness exited before solving because of a global soft-scope variable; preserved as runtime-final-invalid-v1.jl. Local-scope-only script correction is running in runtime-final-v2; production unchanged.

- Corrected final runtime completed OPTIMAL54,591iterations/194refactorizations with original feasibility and exact recorded state/event fingerprints. HH handoff54,434hits/503misses;501misses first differ atindices2–128. Final audit passes with input/reference/sourcehash checks and explicit unsuccessful-attempt classification. No whole-solver speedup is inferred from the single175.855s measured solve region.

- Final independent evidence review approved integration: all nine final jobs match current source hashes; archived reports/medians/provenance match raw evidence. Full-suite coverage remains explicitly incomplete.
