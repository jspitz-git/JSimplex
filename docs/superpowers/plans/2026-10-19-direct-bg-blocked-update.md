# Experimental blocked DIRECT BG updates implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans for the preserved inline workflow, with a fresh independent reviewer at every boundary. Steps use checkbox syntax. This request prepares/reviews documents only; do not implement or execute Julia.

**Goal:** Test whether short dense row panels reduce packed BG update work without changing pivot policy or weakening numerical correctness.

**Architecture:** An isolated Float64/Int DIRECT BG wrapper gathers up to9 logical rows across the active suffix, performs up to8 chronological pivot/elimination steps with explicit FMA on contiguous row vectors, then bulk-writes packed columns and the affected incidence rows. Original scalar suffix handles ineligible/pure-swap/nonfinite cases; original factorization/export/import and solves remain unchanged.

**Tech Stack:** Julia/SparseArrays/LinearAlgebra existing dependencies only; no BLAS3, new package, native hook or global method overwrite. Offline preparation/review uses new Python scripts, never old exclusive checkers.

**Spec:** docs/superpowers/specs/2026-10-19-direct-bg-blocked-update.md

## Global constraints

- Planning only now. Preserve source/test/env/CI/master/global STATUS/roadmap and all frozen evidence. Entry a1cc1d768100f199a3e315c89bf39a28651e8970; master26e2291745999f485a74f643298ca997d65c7205. CIoff, HHreuse disabled, automationpaused, broader planopen.
- Float64/Int packed DIRECT BG; native threshold_one and Markowitz default. No new pivot thresholds, tolerances, precision, coefficient dropping, fast-math or threads.
- b=min(8,n-r), h=b+1, w=n-r+1; n64..4096, b>=4,w>=64, band presence>=h*w/2, finite nonzero stored admission values. First rejected panel disables further blocking in that update. A current zero diagonal or nonfinite intermediate rejects the private panel and executes original scalar suffix from its start; maximum8 repeated steps and one rejection/update, fully counted. All explicit commit index-plus-value stores must be<=2*h*w before allocation/commit; changed support uses fresh exact-length whole-column vectors, unchanged support writes in place. This source-store cap excludes hidden allocator traffic, which remains measured. No cubic packed rewrite.
- Scratch charge72n+16*cld(9n,64)+256+4096<=1MiB. No full-factor copy, second dense tile, per-pivot vector or unbounded ledger. Copies cache-empty; shrink/unsupported sizes drop scratch.
- Changed rounding and candidate pivot trajectories allowed; unchanged pivot POLICY and independent original-basis residual/certification requirements mandatory. All other scope and gates in spec apply verbatim.
- Generic RED/GREEN execution steps below are prospective: offline tasks create test text first; only later concrete reviewed admission may run it. No fabricated expected count before tests exist.

## Review focus

1. Stale pivot data / pure-swap lookahead crossing panel boundary: private panel fallback from its original boundary; Task1 policy/fallback tests.
2. Exact zero, signed zero, structural presence and nonfinite intermediate hidden by cancellation: masks and sticky invalidation; Task1 arithmetic oracle and Task2 failure tests.
3. Logical versus physical row IDs, sorted incidence and history action: bulk writeback with unchanged row-order map; Task1 representation and Task2 independent factor-relation checks.
4. Allocation failure, active/saved factor aliasing, prepared entering/DSE buffers: original conservative invalidation and explicit ownership; Task2 lifecycle tests.
5. Dense work/regression on sparse data, scratch first-use/shrink and deceptive kernel-only benefit: complete counters and whole-lifecycle gate; Task3.

## Task1 — OFFLINE panel kernel and structural tests

**Create later:** diagnostics/direct-bg-blocked-update/reproduce/{panel.jl,panel-tests.jl,work-memory-ledger.md,source-map.json}.
**Consumes:** original packed column/order/incidence definitions in src/triangular_factorization.jl,src/triangular_indices.jl,src/bartels_golub_rows.jl; spec's exact algorithm.
**Produces:** `BGPanelWorkspace` with values n-by9, two BitMatrices, bounded step scratch; `BGPanelDecision` containing start/count/accepted/reason/finite flag and counters. `_bgb_eligibility(inner,r)::BGPanelDecision`, `_bgb_gather!(ws,inner,r,b)`, `_bgb_apply!(ws,r,b,w)::BGPanelDecision`, `_bgb_commit!(inner,ws,decision)`; no abstract/Any fields in eventual hot workspace.

- [ ] Define structural tests before candidate: dimensions32/64/96/4096/4097; width63/64; steps3/4/8; exact half-density edge; checked overflow; no allocation on cheap-reject; no second eligibility attempt after rejection.
- [ ] Define independent small-panel oracle using explicit adjacent swaps/division and `fma`, with recorded predecision bits. Test greater/less/tie pivots, zero diagonal at first/middle/last step, pure rotation spanning boundary, zero multiplier, absent versus present entries, exact cancellation, subnormal/signed zero and nonfinite intermediate. Do not import candidate decision helpers into oracle.
- [ ] Define structural merge tests with nonidentity row/column order, outside-band sentinels, differing final support, fill/deletion, incidence sorted by stable column ID, all history transforms and masks, unchanged-support in-place writes and exact2*h*w movement-guard rejection before mutation. Assert one bulk column merge and only h incidence rows rebuilt, plus truthful scan/store/read counts. Test cap exactly at and one store above2*h*w, unchanged support versus changed support with long prefix/suffix, old/new live-array coexistence, and adversarial repeated panels. Verify separate eligibility/gather traversals, O(n^2 log n/b) lookup accounting, and ONE ascending n-ID incidence pass per panel O(n+h*w).
- [ ] Implement only isolated kernel text with typed interfaces. The decision record freezes numeric predecision values only in test/probe mode; hot kernel returns fixed scalars and uses bounded workspace, no per-pivot snapshots. Source policy predicates, zero-tolerance validation and fallback mapping are explicitly compared with original.
- [ ] Write complete work ledger including eligibility traversal, dense zero fill/masks, swaps/FMA, all fresh-column prefix/suffix copies, old/new coexistence and incidence growth; distinguish source element counts from hidden allocation capacity; source map identifies every copied helper and intentional departure. No whole-source inverse claim for the changed algorithm.
- [ ] Fresh independent numerical/work/memory source review. If source dependencies cannot satisfy policy or bounded memory, stop before adapter; do not silently replace the design with GEMM/dense persistent U.

## Task2 — OFFLINE adapter, lifecycle tests and numerical admission preparation

**Create later:** same reproduce/{factor.jl,lifecycle-tests.jl,numerical-tests.jl,fixtures.json,overlay-manifest.json}; separate results/DIRECT-BG-BLOCKED-UPDATE-HARNESS/{driver.jl,control.py,guard.py,audit.py,ADMISSION.md} only after candidate review.
**Consumes:** Task1 interfaces; ordinary packed DIRECT factor factory in diagnostics/direct-lu-policy-adapters/reproduce/direct-factor.jl and its native/Markowitz policies. Preserve its public forward/export paths.
**Produces:** `BGPanelFactor{I}(inner,workspace,busy)`; `_bgb_factor(B,backend,policy)`; `_bgb_replace!(factor,direction,row;zero_tolerance)` and ordinary forwarding methods; `_bgb_scalar_suffix!(inner,r,steps)` from original loop, sharing one begin/finish and one final update record with blocked route.

- [ ] Prepare independent-input/copy/prepared-two-RHS tests before adapter. Cover update success, no-op final row, rejected panel after previous committed panel, fallback after private arithmetic, zero pivot, injected allocation failure at gather/reserve/writeback, busy state, refactor same/shrink/unsupported dimensions and source-copy divergence. Do not demand full rollback the reference does not provide; failed caches must remain conservative.
- [ ] Prepare deterministic basis streams at96/256 from the old sparse/dense fixture generator and32 controls, with exact input files generated OFFLINE and pinned before any Julia. Add independent stress streams: near-tie pivots, cancellation/fill, large/small finite scales, near-singular matrices, explicit zeros/nonfinite fallback,8/32updates. Every fixture stores construction recipe, input bits and independent basis-column replacement sequence; no candidate-generated expected solution.
- [ ] Freeze fixture roster and finite exact solve/factor-relation criteria from spec; distinguish intentional singular/nonfinite negative tests from cases required to succeed. On separated exact fixtures require reference pivot agreement; on near ties require each side's predicate and residuals, not bitwise trajectories.
- [ ] Build ordinary isolated overlay with original reference and private candidate namespace. Resolve dispatch/world-age at top-level before main; prove stage/root include inverse for unchanged files. Do not run Julia to inspect methods or compile.
- [ ] Prepare named tests for original-B FTRAN/BTRAN residuals, factor-relation/history composition from H captured after spike insertion/column rotation (not old U), growth/minimum pivots, complete fallback and API-attempt counters, cache/alias invariants and matched input states. All per-update snapshots limited to correctness/probe runs; no such capture in timed route.
- [ ] Fresh independent candidate/tests review, then separate driver/admission review. Concrete driver must freeze actual assertion counts, positive route coverage, test/fixture order, total factor/update/solve/control budget, raw-before-aggregate behavior, fail-closed auditor and saved failure prefixes. No claimed expected RED count from this plan alone.
- [ ] Prospective RED: use original scalar route under the same harness; expect ONLY named blocked-route/counter coverage predicates to fail, mathematical correctness to pass. This demonstrates new path exercised, not a pre-existing solver defect. Freeze exact failing count in concrete reviewed admission before launch.
- [ ] Prospective GREEN: separately admitted candidate tests after accepted RED; all numerical/structural/negative tests and counters pass. If a correctness failure occurs, stop and preserve evidence; no tuning tolerances/fixtures. Pure timeout extension follows spec's separate admission, not automatic rerun.
- [ ] Review saved results independently and publish exact closure/name/blob evidence. Source-only preparation does not itself grant runtime or performance acceptance.

## Task3 — Separate complete cost preparation and conditional short execution

**Create later:** results/DIRECT-BG-BLOCKED-UPDATE-COST/{cost.jl,probe.jl,inputs.toml,ADMISSION.md,control.py,guard.py,audit.py,MEMORY-WORK.md}.
**Consumes:** accepted GREEN exact candidate and independent inputs; Task2 residual/policy/ownership oracles. Reference remains ordinary packed DIRECT; no export-specialization wrapper on either side.
**Produces:** matched whole-lifecycle/nested-phase/operation-counter/memory results with separate numerical and performance acceptance.

- [ ] Prepare8cells (sparse/dense96/256,two backends),3warm+7measured alternating pairs, original1constructor/8updates/16FTRAN/8BTRAN/2refactors each lifecycle. Timed totals160constructors/320refactors/1280updates/2560FTRAN/1280BTRAN per process. Concrete preparation adds explicit bounded policy/probe/control budgets before approval; these totals alone are not a backend-work cap.
- [ ] Probe original/candidate with exactly matched observation boundaries. Record eligibility scans/rejections, panels/steps, FMA, masks, gather stores, packed searched/moved entries, row-incidence work, allocation requests, scratch charge, final and old/new coexistence graphs. Operation counters are not GC events or hidden native-allocation proof. Kernel counters stay out of timed route.
- [ ] Freeze first-use and reuse/shrink/copy/failure controls and all output paths; measured time includes workspace construction, gather/commit/incidence/fallback. Capture whole-process RSS/availableRAM/swap and compilation/GC separately; no subtracting phases or dropping outliers.
- [ ] Fresh independent concrete driver/admission review. Numerical release later requires fresh refs/boot/start_ticks/command/full groups AND sessions/noJulia, exact immutable launch inventory, independently accepted receipt and one guarded process. Initial300s, oneJulia/BLAS1/heap2GiB/VM8GiB/RAM6GiB/swap1GiB.
- [ ] First cost gates verbatim: dense4 UPDATE<=.90,WHOLE<=.95,>=5/7faster; sparse4 WHOLE<=1.05; all8events/bytes<=reference, allwarm/measured/probe graphs<=1.10reference, matched transient<=1.25reference, measuredcompile/recompile0, allnumericalpass. Each dense lifecycle>=2panels andpositiveFMAwork. Report every individual result/fallback; first failure stops fixeddesign.
- [ ] Only allfirstgatespass allows separately admitted reversed-order process with samegates and dense>=10/14faster overall. No parameter sweep, old-rerun, block/density tuning or automatic production integration.
- [ ] Independently review outcomes and exact publication. A later public solver integration plan is separate and must preserve original-model certificates and assess status, residual/gap, robustness, recovery/refactors and total solve time across representative problems.

## Current handoff

This deliverable is a reviewed experimental design only. Next possible task is Task1 OFFLINE kernel/test preparation after the human requests it. No candidate, Julia text implementation, driver, numerical fixture generation, Julia parser/import/compiler/query, measurement or production change occurs now. The new arithmetic contract applies only to this proposed isolated BG route; previous accepted and rejected records retain their original contracts.
