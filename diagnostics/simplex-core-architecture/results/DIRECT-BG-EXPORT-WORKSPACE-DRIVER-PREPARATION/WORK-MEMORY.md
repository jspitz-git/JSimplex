# Work and memory accounting for prepared correctness driver

Implementation work and retained-memory formulas are the frozen Task1
work-memory-ledger.md and Task2 composition-ledger.md, both pinned in full. The
wrapper adds cold O(1) budget/busy/type/hook checks, one setup holder, two references
and Bool; no extra hot solve scan/copy/conversion. Fused import removes one8u
normalization temporary and2u stores on successful normalization only. Retained
scratch policy is512+8*cld(n,64), optionally+32n, at most min(1MiB,P0/16),
P0=16(l+u)+8(n+1). This is a policy charge, not a physical-memory bound. Original
factor, prepared destinations, histories, capacities, old/new refactor coexistence,
backend/extraction/import temporaries and GC/native retention remain chargeable.

RED invokes only six isdefined checks plus loader/Test/recorder. GREEN executes
Task1 workspace, importer, then Task2 lifecycle entries exactly once. Task1 has14
original fixture exports (seven fixtures/two policies), plus synthetic invariant,
normalization, allocator and orientation cases. Task2 repeated path has56 manager
setups,384 updates,96 refactors,2984 valid explicit solve entries. Failure matrix
reaches bounded n8 cold allocation prefixes (native25/Markowitz21), six seam failures,
wrong type, five synthetic scratch failures, reentrancy, publication and genuine
warm64 owner-reuse cases. Warm witnesses add two candidate/two reference setups,
four candidate refactor entries, four updates, two copies and34 explicit solves.
Copy and dimension/fallback paths run once per original arm/mode, as fully listed
in the frozen composition ledger; no old suite, public solver or cost loop runs.
Internal orientation/update/backend/import work is additional. These source counts
are not complete PREforward/native-call or allocation measurements.

Tests retain bounded graph snapshots of reachable owners and detached bits, input
and output vectors, copied factors, CSCs, exact-rational residual scratch, synthetic
64x64 orientation fixtures and failure sentinels. Graph traversal scales with
n+l+u+history+cache and has IdDict/tuple/array overhead; physical capacities and
native memory are not inferred from graph snapshots. Repeated groups use bounded
per-step state, not a growing trajectory log. Recorder stores11 child summaries
and only failure text; successful Test.Pass leaves increment counters, not a list
of7935 records. Failure diagnostics and exception backtraces can allocate. Raw TOML
and exact-tree final check occur after tests. Output serialization is correctness
driver overhead, never an allocation/speedup measurement. Resource guards bound the
process, not an asserted full live-object graph. Cost comparisons remain deferred.

No extra numerical oracle calls were added to frozen tests. The newly added driver
only invokes the three planned entries and source/thread checks. This source review
finds no unnecessary new production work or memory; no production code is changed.
Runtime correctness, actual counts, dispatch/compilation and performance remain
unverified until separately admitted Julia runs.
