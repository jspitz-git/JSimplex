# Planning decisions and source evidence

The latest human explicitly requests plan plus independent review in one turn and forbids implementation/Julia. This supersedes generic skill requests to stop between drafting spec and plan. Architectural brainstorming and writing-plans are applied as document preparation only; no implementation approval is inferred. Existing inline implementation / fresh independent-review workflow remains the future method.

Chosen panel bounds8steps/9rows, finite dense band, n64..4096, half occupancy, width64, minimum4steps. Explicit FMA/reordered independent columns is permitted only inside the proposed route. Packed representation and backend policies stay original. GEMM composition, persistent dense U, rejected workspace tuning and public solver changes excluded.

Read source: BG replace_column!1097+, _last_pure_bartels_golub_swap57+, stable row order and incidence, _track_upper_value!397 (nonfinite eligibility, NOT a general growth accumulator), _prepare_spike! and original DirectLowerBackend. The pure-swap lookahead may cross panel boundaries. A current nonzero diagonal rules that fast path out at its first check; zero diagonal therefore aborts the private panel and uses original scalar suffix from panel start. No stale pivot reads or untracked hidden nonfinite intermediate allowed.

Dense tile stores each logical U row contiguously across columns. Panel commit keeps row-order identities fixed and maps logical rows back through existing order; history still records mathematical swaps. These are deliberate representation differences, not promised bitwise equivalence. Explicit zeros/invalid bands fall back; generated zeros require presence/touched tracking.

Cost evidence is existing frozen Task3 first result (only2/8 timegatespass), not a fresh profile or permission to rerun. Dense96/Markowitz update share55.5% derives from saved within-window phase ratios. No end-to-end speedup forecast. Full-source pins in entry.json are read-time evidence, not retroactive launch pins.

Self-review: each of five failure classes maps to named Task1/2 tests or Task3 gates; math/policy, exact basis references, output ownership, fallback work, bulk splice cost, sparse preflight cost, cold/reused/shrunk scratch and all memory classes are explicit. Fixed numerical bounds retain128*n*eps. Proposed future workloads and counts still require concrete driver admission; no speculative exact assertion count. Review may reject this design before any code exists.
