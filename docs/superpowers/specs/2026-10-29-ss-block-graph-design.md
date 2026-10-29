# Block-aware factorization and graph-local direct SS: design for review

Status: source/design only; no implementation or Julia run authorized by this document. User selected this direction after the realistic-sequence study; the concrete design below is proposed, including the subsequent question about KLU. Implementation follows approval of this document and a separate implementation plan.

## Purpose and decision

Reduce the total work of factorization, updates and solves on the same recorded basis exchanges. Prefer meaningful elapsed-time improvement over small allocation differences; report both. Start with Float64/Int64 private direct SS, preserving current numerical admission and residual/growth checks. Keep FT and BG-local as external comparators, not simultaneous implementation projects.

Separate two independently rejectable changes: factor ordering/backend and graph-local SS. Do not replace U storage, simplex pivot selection, the refactor controller or certification. The first local SS candidate retains physical packed row indices and exactly the existing SS row rotation and numerical pivot sequence. Its purpose is to avoid global discovery and inactive elimination visits, not to claim the entire geometric rotation disappears.

KLU is a serious alternative to forcing UMFPACK to respect blocks. First qualify its ordinary factorization and FTRAN/BTRAN on the same bases without flattening its coupling matrix into U. This is an additional backend comparison, not a claim that KLU can already initialize direct SS. The two gates are distinct: a faster KLU backend need not yield a cheaper exported direct factor.

## Evidence and constraints

Baseline: diagnostic commit cb68b71975ecb8aafffe501e5c6076026348bb3d; master c0fa748ffa61ccb7c1caaf248c40324f60bc737b. `diagnostics/realistic-basis-structure/2026-10-29/REPORT.md` records runtime bases with 28,453 rows, largest BTF blocks 3,675–4,666, and roughly half of B NNZ in inter-block couplings. Full spike matching/SCC cost about 4–6 ms and 9 MiB per runtime sample. None of that graph work may be inserted at every exchange and then excluded from timing.

The spiked-U SCC is a structural opportunity, not a safe skip set. BTF is computed at construction/refactorization only. After an exchange old BTF labels are descriptive hints, never permission to omit work: columns can merge blocks and removing entries can split them. Local numerical updates use the current U incidence, not stale BTF boundaries. No dynamic SCC/matching maintenance is required in the first candidate.

All exact nonzeros, including tiny coefficients, remain. An imported U containing any stored explicit zero is ineligible for the first local route: detect this during the initial incidence/diagonal scan, retain the original SS representation and behavior, and use ordinary SS until a later refactor produces an eligible U. Do not drop, normalize or repair these entries to gain admission. This avoids assuming that a literal rotation of incidence lists reproduces the original explicit-zero handling. Candidate packers/setters on an eligible U remove exact zeros, so local mutations do not introduce stored zeros. No tolerance, arithmetic precision, finite/residual/growth safeguard or public acceptance rule changes. Other precisions/backends continue through existing implementations. A different factor order may change numerical trajectories; that must be distinguished from update-kernel savings.

## Approaches

1. **Block-aware factorization plus local traversal of existing SS storage (proposed first).** Reuse packed U, solve/history implementations and numerical SS pivot rule. Maintain a private reverse index. This isolates work removal from another storage experiment. Remaining O(rotation length) permutation/map work is explicit.
2. **KLU with its native block representation (proposed backend gate).** Keep `L*U + F`, with F holding inter-block couplings, for ordinary basis solves. It naturally tests whether the observed BTF is useful without materializing cross-block fill. It introduces a dependency and different factor-pivot/scaling semantics; it is not an interchangeable direct-LU export.
3. **A new fully block-native SS manager with separate coupling storage and dynamic block splitting/merging (defer).** Potentially avoids more work, but requires a new factor identity, update-history algebra, coupling solve/update kernels and copy/failure proof. Do not disguise this project as an exporter change or implement it alongside the first candidate.

Calls made here are the author's proposal, not previously approved numerical results. Neither fewer U entries nor smaller blocks alone selects an approach.

## Factorization boundary

### UMFPACK experiment

At construction/refactorization, obtain exact-pattern matching and SCC blocks, with an explicit structural-work limit. Produce a topological column order and an AMD ordering within each nonsingleton diagonal block; singleton blocks need no AMD call. Use the installed SuiteSparse AMD wrapper, checked status and canonical zero-based owned input; no extra numeric LU to discover an ordering. Count every block extraction, symmetrization, ordering call and allocation. All inter-block entries remain in the original B passed to the one numeric factorization.

Pass the resulting one-based q through Julia's existing `lu(B; q, control)` API using the original selected native control vector. In particular, do not change numerical pivot thresholds or pretend `FIXQ` guarantees Qinit: UMFPACK symbolic analysis can alter the supplied order, and FIXQ concerns later numeric refinement of the symbolic order. Check the exported actual p/q and factors before describing the result as block-preserving. Acceptance requires each pivot's original row and column to belong to the same original BTF block and block ids to occur contiguously in a valid topological order. A rejected ordering is recorded as unavailable; ordinary factorization remains usable and is timed separately, never silently labeled a successful ordered arm.

The first source/candidate task must confirm the AMD wrapper and exported permutation convention. If the native symbolic transformations defeat this route, stop that arm after its bounded qualification. Do not add undocumented native controls, repeated LUs or a new block factorization to rescue it automatically.

Compose accepted p/q into existing `BasisLUExport.rows/columns` and `DirectLowerBackend` maps. No extra RHS gather/scatter pass per solve and no retained second whole B. Existing scaling-orientation, normalization, underflow, finite and diagonal checks remain. New publication is candidate-first; failure leaves the old factor valid under its existing contract.

Markowitz is an unchanged comparator on fast0507 only in the first numerical stage. Making it block-constrained changes candidate enumeration (including singleton/doubleton queues and dense-core crossover), so it requires its own design; restricting only the general pivot loop would be incomplete. No large-runtime Markowitz factorization is inferred to fit the present budget.

### KLU gate, prompted by the user

KLU performs BTF plus within-block ordering and represents the permuted/scaled matrix as `L_b*U_b + F`. Native forward and transpose solves include F; extracting only L/U would solve a different matrix. The current private direct exporter instead requires a multiplicative L/U identity. Algebraically an equivalent multiplicative upper would contain `U_b + inv(L_b)*F` (with all row/column/scaling conventions applied consistently). Forming this can add coupling fill and work and is explicitly excluded from the first KLU comparison.

Use an isolated diagnostic environment, pinned KLU.jl/SuiteSparse version, and ordinary KLU solve APIs first. No project/manifest edits, installation or import in this source-only task. The repository currently has no KLU dependency. Float64 native input is the initial supported scope; no automatic Float32-to-Float64 promotion is presented as a Float32 optimization.

Record exact BTF/ordering/scaling/diagonal-preference controls. Use KLU's own BTF analysis once, not our full matching/SCC followed by the same work inside KLU. Set a positive `maxwork` in the later admission (default zero is unlimited); report partial matching/coarser blocks rather than treating the work limit as numerical singularity. KLU's diagonal-preference tolerance is not assumed equivalent to UMFPACK's pivot policy. Any comparison with different admission is labeled backend-policy comparison; preservation of the stricter selected pivot requirement needs a source-backed mapping and numerical qualification before use by SS. Keep original solver tolerances and independent residual/growth checks. No reused symbolic object across changed basis patterns; `klu_refactor!` is not a replacement-column update and its fixed-pattern/pivot behavior requires a separate contract.

Measure ordinary factor/build/export-free solves before considering direct export: factor time, native solves, NNZ(L)+NNZ(U)+NNZ(F), Julia allocations and process/native-memory limits. Julia `summarysize` alone does not count native payload. Do not repeatedly request K.L/K.U/K.F inside windows: the reviewed upstream wrapper extracts/allocates and may sort native data on these accesses. Check ownership from the pinned source, not comments/docstrings alone; inputs and copied factors must not share mutable native scratch inadvertently.

If KLU wins, choose between a base-backend integration using its solves and a separate block-native direct-SS design. Do not flatten F merely to fit today's interface. KLU does not itself implement SS column updates, simplex pricing, ratio tests or certificates.

## Graph-local SS boundary

Use a private adapter around the existing Float64 direct SS factor. Do not overwrite production methods. All mutable incidence/frontier buffers are private; copied factors get independent metadata and solve scratch. Upper numeric storage, update history and its existing shared-prefix ownership rules are unchanged.

Maintain reverse storage incidence `row -> stable basis-column ids`, private reusable row lists with logical lengths, epoch-mark arrays, an affected-column list and a min-heap of active pivot positions. `column_order/positions` remain the authoritative column maps. For an eligible U, a stored coordinate appears exactly once in its row list. Reject imported explicit zeros/invalid packed ordering before enabling this metadata; do not construct a locally eligible index for such storage. Cache the total stored U entry count and update it at every insertion/deletion, avoiding another full sum each update. Retain high-water capacities until refactorization/disposal; do not physically shrink reusable scratch on every call.

One construction/refactor scan O(n + stored_NNZ(U)) builds incidence and validates finite nonzero diagonals, sorted unique coordinates and absence of stored explicit zeros. Ineligible storage follows original SS unchanged; this is local-route admission, not a new original-factor rejection. BTF metadata is not part of hot-path correctness. Existing dense/prepared spike preparation and its alias/provenance checks remain. Where it already scans the spike for packing, collect support and finiteness in that pass; do not add a second full scan solely for the graph.

An update does the following, preserving the ordinary SS arithmetic per target and ascending pivot order:

1. Prepare the spike and compute the same leaving position/last exact nonzero. Before mutating U, gather columns incident to rows in that geometric interval, plus the replacement column. Budget discovery visits, list shifts and frontier work. Admission may conservatively choose the original prepared SS body; it must not prepare the spike twice.
2. Apply the same column/reference rotation and map updates. Relabel packed rows only in gathered columns; an untouched column contains none of the rotated row ids and is unchanged. Rotate row-list references and rebuild the moved row's list from the affected columns. Include trailing columns beyond `last`: they can contain the moved row. Do not clip the coupling writes to the pivot interval.
3. Clear the original entering-spike support after packing before reusing scratch as the row spike. Unvisited scratch values are otherwise stale; sparse discovery is not a license to read them. Seed the frontier from the moved row's nonzero entries. Epoch marks reset only touched positions, with a rare explicit wraparound reset counted separately.
4. Pop the smallest active pivot position; update only incident trailing columns. Each changed spike entry may enqueue a later pivot, so reachability includes fill created during elimination, not just initial support. Preserve `swapped = finite(spike) && finite(diagonal) && abs(spike)>abs(diagonal)`, multiplier expression, exact-zero cleanup and update records. Skip a zero-spike pivot only while its diagonal is proved finite and nonzero. Otherwise execute the original scalar path, including 0/0/nonfinite behavior, before any skip.
5. For a row swap, gather the union of pivot-row incidence and current row-spike support before writes. Update both numeric storage and incidence at each store, including cross-block/trailing destinations. Use the original arithmetic per target; operations on different targets need not share traversal order, but order within each target and pivot order do. Keep the full original SS path as a conservative alternative when local maintenance grows expensive.
6. Maintain the final moved-row stores for every touched trailing column, and publish finite/cache eligibility only through the original begin/store/finish protocol. Reuse existing row-operation history and prepared-spike invalidation. A failure must not publish valid graph/cache metadata.

Reserve sufficient row-list, heap and affected-list capacity before each mutating phase: replacement/rotation, each complete pivot (including swap), and final moved-row publication. Use structural upper bounds from the collected targets; do not compute numerical updates twice just to estimate fill. If a phase cannot reserve under the metadata cap, fall back before its first store. A dense fallback after local mutation may continue only from these explicit phase boundaries, with the completed rotation, next pivot, accumulated indices/multipliers/swaps, scratch and touched-tail state passed to the original prepared-body remainder, not by replaying the whole update. No fallback is permitted halfway through a row swap or partially published coefficient list. Invalidate the reverse index and use original SS for the rest of that chain; rebuild once at the next scheduled refactorization. Never rebuild a full index at every subsequent pivot. A local budget refusal before mutation calls the original prepared body once. Numerical failure is not converted into budget fallback or swallowed.

This first algorithm does not search for permutation-only updates on zero-diagonal spiked matrices. Such cases stay within the original SS numerical path/fallback, with matching used only at factor construction. It therefore does not assume that every spiked component is nonsingular or that initial BTF blocks survive exchanges.

## Work and memory ledger

Let n be dimension, e stored U entries (including explicit zeros), d rotation length, r gathered incidence visits, z spike support, h emitted history entries, s total shifted index/list entries and w target coefficient visits. These are logical work quantities, not measured machine instructions.

| Frequency | Added work | Work actually targeted |
|---|---|---|
| construction/refactor | bounded matching + SCC; block AMD calls; one reverse-index build/diagonal validation; actual-permutation validation | less factor fill and more local later updates; no guaranteed saving |
| every replacement | O(z+r+d+s+w), frontier up to O((z+w) log n); membership/map lookups, copied old/new column support, exact incidence maintenance | global column discovery, relabels in unaffected columns, zero-spike pivot visits and dense trailing searches |
| every FTRAN/BTRAN | existing solves/history; no graph traversal or new vector pass | cheaper U/history only if achieved |
| copy | O(n+e) metadata duplication plus existing factor copy | no claim of free copies |
| fallback/recovery | spent local work plus original remaining work; graph disabled until refactor | no repeated rebuild tax; recovery rules unchanged |

The first candidate uses physical rows, so O(d) map/list rotations remain. Sorted row lists can cost O(degree) shifts per edit; charge those shifts rather than call incidence updates O(1). If that cost dominates, reject this candidate before designing another index layout.

Proposed initial guard values, to be frozen with the implementation plan: 50,000,000 structural edge visits per factor build; at most 5,000,000 stored factor/history entries (same diagnostic storage guard); 128 MiB additional typed graph/ordering workspace per live factor; local discovery/maintenance work allowance `2*(n+e)` integer/list/edge units per exchange before dense continuation/disable. Budget exhaustion changes algorithm choice, never drops numerical entries. Limits are admission safeguards and cost controls, not proofs of speed.

Track allocated capacities, not just logical lengths: reverse-list integer payload is 8 times the sum of row-list capacities; include all n list headers, row lengths, heap, stamps, affected columns, support buffers and temporary old/new supports. Each buffer is geometrically grown (next power of two, minimum 4), so capacity is below twice its high-water demand (minimum exception included). At the hard cap refuse growth before the store and take an already proved dense continuation boundary. Copies, simultaneous candidate publication, shared old history and ordinary fallback factor are all part of peak retained memory. Native symbolic/numeric memory and allocator retention remain separate from Julia payload accounting.

## Tests and measurement decisions for the later plan

Use ordinary Test and warmed whole-function/cycle measurements. First prove incidence equivalence against a freshly rebuilt oracle after every mutation in small tests, including copies independently mutated/refactored, zero spike diagonals, actual row swaps, explicit ±0, exact cancellation, tiny/subnormal inputs, nonfinite/zero diagonals, budget fallback before and during mutation, cache eviction and prepared-buffer aliases. An adversarial upper chain must create fill outside initial spike support and a coupling column beyond `last`. Test unchanged output/exception behavior against ordinary SS on the same initial factors, not merely final residuals. In particular construct an imported stored zero at the leaving row followed by a stored row+1 entry: assert local admission refusal and compare the original fallback outcome/representation. Do not silently repair a duplicate-index consequence in the original path as part of this optimization.

Factor-order tests independently validate perfect matching, SCC order, actual exported p/q, scaling orientation, input immutability and multiplication/solve identities; do not use the candidate's graph as its own oracle. A singular diagonal block, one irreducible block, all-singleton coupled triangular matrix and backend-reordered q must have explicit results. KLU additionally tests F nonempty, transpose solves, singularity, input ownership and strict pivot-control semantics; source documentation is not numerical qualification.

Compare four direct-SS arms on identical preserved exchange tapes: ordinary order/original SS, block order/original SS, ordinary order/local SS, block order/local SS. Report unavailable/fallback ordered arms honestly. Keep factorization frequency/RHS/exchanges identical; evaluate speed first with bytes/events/full retained payload alongside L/U/history/index counts. Factor trajectories may differ across orders; local SS versus original SS on identical order must match the intended unchanged arithmetic. An independent KLU backend comparison is reported separately and cannot claim an SS-update improvement.

Use runtime-30000, runtime-40000 and fast0507 tapes already hashed in the realistic study; retain sparse and dense synthetic controls. No new LP solve or large-medium numerical experiment is needed. Prepare exact warmups, alternating measured pairs (at least five), residual/fresh-factor/growth oracles, compilation fields, call counts and resource/deadline gates in a separate reviewed admission. Include ordering, incidence maintenance, preparation and fallback costs in whole-cycle time; show update/solve decomposition only as subsets. No post-result threshold tuning, omitted GC windows, hidden graph reconstruction or automatic production promotion.

## Next deliverables and stop conditions

After design approval: an implementation plan with independent deliverables for block-order/KLU interface qualification, a private graph-local SS candidate, ordinary differential/lifetime tests, then a separately reviewed short four-arm measurement. Candidate work remains isolated from src/test/env/CI/master until numerical qualification and a later integration decision. Stop an individual arm if its interface, numerical safeguards or bounded work cannot be satisfied; do not begin an equivalent inventory to evade the stop.

This document introduces no production work or memory. The proposed candidate does add index maintenance and retained metadata; its benefit is explicitly unproved and must survive whole-cycle comparison. No numerical run or new allocation/speedup result is reported here.

## Sources read for this design

- Local: src/triangular_factorization.jl (spike preparation, SS, row pivoting, stores/eligibility); src/triangular_rows.jl; src/triangular_indices.jl; src/bartels_golub_rows.jl; src/factorization.jl; src/markowitz_factorization.jl; the last study's direct-factor.jl/factor-export.jl and REPORT.md.
- Installed Julia 1.13 SparseArrays/src/solvers/umfpack.jl (lu q/control API and qsymbolic call), wrappers.jl (AMD wrapper). Newly read sources are not retroactive numerical launch pins.
- [KLU guide](https://raw.githubusercontent.com/DrTimothyAldenDavis/SuiteSparse/dev/KLU/Doc/KLU_UserGuide.tex): BTF, within-block ordering, separate coupling representation.
- [UMFPACK guide](https://github.com/DrTimothyAldenDavis/SuiteSparse/blob/dev/UMFPACK/Doc/UMFPACK_UserGuide.tex): supplied ordering and FIXQ limitations.
- [KLU.jl source](https://github.com/JuliaSparse/KLU.jl/blob/master/src/KLU.jl), [package metadata](https://github.com/JuliaSparse/KLU.jl/blob/master/Project.toml): upstream only, not installed/pinned runtime evidence. Exact sources and hashes used for this review are saved separately. The KLU.jl snapshot is revision 2975044cb3ac1f76f9d3eeef7ee6deedfe8375a0; the SuiteSparse guides are revision 0f41a7786b08d3399c6fd6cf7033714bc7f019f3. Neither is proof of the installed native library version.
