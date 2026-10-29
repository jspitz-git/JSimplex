# Structural options for SS, FT and BG

Investigation completed in the requested order: SS, then FT, then BG. The first guarded process passed 4,852 ordinary tests and 235 offline checks across 96 cold trajectories and 480 measured windows. A second private localized-BG spike passed 1,368 tests and 113 checks; see the linked report. No production code, permanent test, environment, master or CI change.

## SS first: results and decisions

**SS already implements the useful endpoint-limited rotation.** Its replacement column/row move stops at the last exactly nonzero spike row, and its already-triangular fast path avoids elimination. Merely shortening ordinary FT to this endpoint repeats the strategy already available as SS.

**A general permutation precheck adds no observed elimination saving to SS on this dataset.** For each interval there are 2,048 inspected SS updates. Structural eligibility counts at intervals 128/64/32/16 are 3/5/9/16; every one already has zero newly stored nonzero elimination multipliers in ordinary SS. This is not a universal impossibility result, and applying a different permutation could change later trajectories. The diagonal-zero matching case is not implemented by the probe; all observed probes happened to satisfy its zero-free-diagonal preconditions.

**Earlier refactorization changes whole-cycle cost materially, but is not allocation-neutral.** The table compares interval64 against128 for the same input, backend and manager. Both include actual explicit basis assembly, constructors/export/normalization, every scheduled refactor, all entering/RHS FTRAN and BTRAN, fresh buffers, midpoint copy, finite guards and nested timers. A full256-exchange cycle has3 refactors instead of1. Ratios below1 favor64.

| Input | Backend | Whole time ratio | Allocated bytes ratio | Allocation events ratio | Final reachable graph ratio |
|---|---|---:|---:|---:|---:|
| band | native | 0.650 | 0.871 | 1.270 | 0.358 |
| band | markowitz | 0.618 | 0.899 | 1.593 | 0.357 |
| blocks | native | 0.702 | 1.278 | 1.356 | 0.541 |
| blocks | markowitz | 0.743 | 1.404 | 1.712 | 0.584 |
| sparse | native | 0.689 | 0.890 | 1.161 | 0.357 |
| sparse | markowitz | 0.698 | 0.967 | 1.639 | 0.385 |
| dense | native | 0.703 | 1.205 | 1.195 | 0.408 |
| dense | markowitz | 0.709 | 0.978 | 1.177 | 0.414 |

On band and general sparse cases, interval64 saves about30–38% whole time and3–13% allocation traffic. However, allocation EVENTS increase16–64%; on blocks events increase36–71% and bytes28–40%. Thus lower byte traffic must not be described as fewer allocations. All eight paired timing ranges for64 lie below1, but only five repetitions in one process were measured. Intervals16/32 sometimes run faster while allocating substantially more; selecting the fastest interval after this sweep is not an out-of-sample policy validation.

**This does not establish a better production default.** Current SolverOptions defaults refactorization_interval=20, not128. NumericalPolicy adaptive_refactor defaults according to simplex_strategy==:adaptive; existing RefactorizationState has numerical residual/growth, fill and cost reasons. These component experiments bypass the public controller and compare deliberate fixed schedules. They show the cost of long histories, not a defect in the existing controller or a justification to replace its defaults.

**Further narrowing of SS column visits needs real metadata.** On interval128 blocks, the median pre-update union of columns containing a rotated row is32 versus40 suffix columns currently visited; on band/general sparse/dense it is64 versus64. This is only a structural proxy, not a safe omission predicate: swaps, newly generated entries and trailing-column values remain obligations. A persistent row incidence index requires O(n+nnzU) integer storage, updates on insertion/deletion/rotation and pivot swaps, plus refactor reset and copy ownership. Rebuilding it per exchange would shift work into a full scan; we have not admitted such an index or removed any visits. The observed block-only headroom does not justify another storage rewrite before realistic traces.

## FT and BG

FT endpoint localization corresponds to existing SS; no duplicate FT implementation was built. General permutation feasibility was also inspected read-only for FT and BG. Each has3/5/9/16 eligible observed updates per2,048 at intervals128/64/32/16. Of those,3/3/7/12 still perform nonzero elimination, storing19/19/37/60 new nonzero multipliers at those steps. These counts are not total future solve operations avoided, and counterfactual permutations might alter later fill.

The cold prototype builds a fresh graph, performs reachability and an independent Kahn acyclicity check. Median overhead across inspected calls is about11–12 microseconds and34KiB per probe; interval128 SS cases have32.9–64.4KiB medians. This is deliberately an expensive diagnostic, not an admitted production precheck. A cheap route would need a correctly owned structural reach set from existing work; numeric zeros in a BTRAN result do not prove structural unreachability. No unconditional graph scan or threshold-based coefficient dropping is proposed.

BG already batches simple pure-swap runs and keeps stable row identities. We therefore tested a different remaining opportunity: consistently limit column rotation, adjacent elimination and pure-swap batching to the actual spike endpoint. This private candidate is a contiguous-region variant, not a complete graph-local/Reid elimination implementation. [Localized BG results](../../bg-local-rotation/2026-10-29/REPORT.md) show a real block-structured improvement; generic sparse and dense cases show no convincing gain.

## Coverage of the proposed options

| Option | SS | FT | BG |
|---|---|---|---|
| Limit update region by last nonzero spike row | Already implemented; source and trace confirmed | Existing SS supplies this strategy | Private coupled-endpoint candidate tested successfully on blocks |
| Recover triangularity by permutation alone | No extra observed elimination saving | Rare observed opportunities; expensive current probe unqualified for production | Same rare observed opportunities; existing pure-swap batching already present |
| Preserve blocks / visit only actual affected graph | Current shorter spans help; more omission requires maintained incidence/copy/invalidation proof | Would require more than renaming SS or initial reordering | Endpoint-local variant tested; general graph-local variant remains a larger unimplemented design |
| Earlier refactorization | Faster fixed schedules, with allocation-event tradeoff | Similar tradeoff; some byte savings | Faster, generally greater allocation traffic |
| Better initial ordering alone | Not sufficient evidence | Not sufficient evidence | Not sufficient evidence |

The previous band experiment started from a sparse U and nevertheless filled its triangular envelope, so a nicer initial ordering alone does not demonstrate lasting prevention of update fill. No new Markowitz/initial ordering or basis-column-selection policy was changed.

## Numerical, work and memory scope

Float64 only, n64, four exact dyadically dominant column-pool patterns, native threshold_one and Markowitz default, normalized direct adapters. Every cold direction/FTRAN/BTRAN is checked against explicitly selected input columns with directed256-bit enclosures and the unchanged128*n*eps*max(1,norm_inf(B)*norm_inf(x),norm_inf(rhs)) bound, using norm1(B) for transpose solves. Backend arithmetic precision/tolerances unchanged; selected RHS coverage is not an all-RHS conditioning proof. Cold normalized-U magnitude guard is not a global conditioning certificate. Hot runs match their own cold factor/history/output fingerprint and midpoint values; different intervals may change representations and rounding. No complete hot-prefix capture or observer-neutrality proof. Initial fingerprints match across all managers/intervals per backend/input, and all input hashes remain unchanged.

Exact main budget:672 replays,4,368 refactors,5,040 underlying builds,172,032 updates,344,064 FTRAN and172,032 BTRAN entries; measured480 replays,3,120 refactors,3,600 builds. Backend/export/scaling internals are additional, not a complete PREforward/native ledger. Cold graph/oracle/summarysize work and final fingerprints are outside hot windows, cold factor owners released before prewarmGC. Actual basis assembly is inside whole time, with median interval64 SS assembly cost about4–10 microseconds per cycle.

All480 measured compile/recompile values are zero. Two measured windows contain GC and remain included: SS dense/native/16/r5 has10.135ms GC in18.681ms whole time; BG dense/native/16/r5 has12.458ms GC in26.635ms. No samples were discarded. Manager order is SS→FT→BG; only intervals within a manager are rotated, so cross-manager timing is descriptive.

Qualified process112.07s inclusive, maxRSS1,067,848KiB, minimum availableRAM21,766,556KiB, swap0. Reachable graph bytes exclude allocator spare capacity and native allocations; processRSS includes compiler/oracles/retained diagnostic traces and cannot be assigned to an individual manager. After the first run707 historical/new groups AND sessions absent; after the BG follow-up709 absent and no Julia.

## Decision

For SS, do not add the current graph probe, duplicate its existing limited rotation, or change production refactor defaults from this benchmark. Its most useful finding is the explicit time/traffic/event tradeoff of long histories. For FT, use SS as the already available limited-region comparator. For BG, the private contiguous-region candidate is worth a separately designed realistic/lifecycle qualification; do not promote from these synthetic cases. General graph-local elimination remains a possible larger direction, not implemented or claimed proved here.

No unnecessary NEW production work or memory was introduced. Diagnostic full-graph scans are explicitly expensive and unqualified; refactor counts and allocations are fully charged. The localized BG block results demonstrate avoided existing update/history work, not permission to drop numerical coefficients or safeguards.

All earlier evidence is frozen and was not rerun. New artifacts: results-1.toml, analysis-1.json, summary.csv, driver/reused-prefix, pins90, admission and independent result review. The analyzer is postexit and not a launch pin. Original PLAN typo plus624? means624 cold refactor records. Startup has3 structural_probe calls and4 Test assertions; reviewer initially counted4 calls, corrected explicitly in the final review.

Primary theorem source: [Schork and Gondzio2017,Theorem3.1](https://optimization-online.org/wp-content/uploads/2017/07/6119.pdf).
