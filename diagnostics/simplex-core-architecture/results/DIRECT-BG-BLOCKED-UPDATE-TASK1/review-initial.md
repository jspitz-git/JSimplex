# Independent Task1 source review — initial rejection

Scope: BG blocked U Task1 offline candidate. Result: NOT ACCEPTED, pending one bounded source/test correction pass for R1–R3. No Julia executable, query, parser, import, compile, tests, numerical simulation or measurement was run. No old auditor was rerun. Review performed by a separate reviewer from candidate authorship.

## Findings

### R1 P1 — Successful arithmetic-to-commit coverage is conditional and support-fill/reuse coverage is absent

diagnostics/direct-bg-blocked-update/reproduce/panel-tests.jl:150-177,186-210

The only full arithmetic->commit->dense/incidence comparison accepts :store_budget instead at lines158-170. Thus a regression rejecting every ordinary applied panel bypasses the promised representation checks. Later positive commits force phase=0x02 without running arithmetic; the single changed-support accepted test deletes a slot. Require a deliberately bounded successful arithmetic commit unconditionally, positive fill-in with exact sorted stable-ID incidence, and a second successful panel using the workspace. Assert unchanged owners and exact changed-array lengths/owners, outside-band preservation, and one merge per affected column.

### R2 P2 — Predecision, history-action, touched-mask and signed-zero structural oracles are incomplete

diagnostics/direct-bg-blocked-update/reproduce/panel-tests.jl:46-74,113-148

The independent dictionary oracle records only row/swap/multiplier, not current predecision a/z bits. The test omits last field and never checks forward/transposed action of recorded history or touched masks. Both carrier and oracle discard all exact input zeros; the subnormal test checks a nonzero output, not signed/underflow-zero behavior. Add independent per-step predecision capture in cold/probe mode only, validate chronological original-format history action including last, compare both masks, and add focused absent-source target-preservation and signed/underflow-zero cases. Full original-B/lower/API tests stay Task2.

### R3 P2 — Exact movement-guard and complete source-work tests do not exercise computed commit counts

diagnostics/direct-bg-blocked-update/reproduce/panel-tests.jl:91-92,178-210

The exact-cap and cap+1 tests invoke _bgb_store_budget directly. They cannot detect a wrong planned-store formula in _bgb_commit!. Existing long-prefix tests are not exact boundary fixtures. Require constructed real commits at exactly 2*h*w and one store above, with no reserve/mutation/allocation on refusal; verify actual/planned stores, copied prefix/suffix reads, all-column merges, and eligibility/gather separate traversals with independently derived expected counters. Existing counters assert selected fields only; h*w incidence-mask and scratch checks require concrete coverage rather than source comments.

## Source correctness and Task1/Task2 boundary

The inspected kernel reads current private pivot values at each chronological step; zero diagonal rejects the whole private panel before any swap, so Task2 can invoke unrestricted original pure-lookahead from the original boundary. It checks every FMA result and division for finiteness and reports a sticky-failure obligation through decision.finite. Structural visitation uses current presence and skips a zero multiplier; exact computed zeros become absent +0. Stable logical row lookup and final order.order mapping are consistent with UpperRowIndices; the shared row order is not also permuted. Prefix/suffix IDs and values are copied verbatim. One ascending stable-column-ID pass rebuilds h incidence rows.

No confirmed arithmetic/row-ID kernel bug was found by static inspection. That is not runtime correctness acceptance. The allowed FMA arithmetic differs from scalar old-m*value; future independent original-B residual/history checks remain mandatory.

Original begin/finish, zero-tolerance validation, prepared two-RHS provenance, single-rejection latch, scalar suffix, actual history publication, copy/refactor/busy state and allocation-failure cleanup are explicitly future Task2 work. Structural Carrier does not subtype ComposedRowFactorization: its invalidation reaches the generic no-op _invalidate_dense_upper! at triangular_factorization.jl:708. Its commits therefore provide no production cache/provenance evidence. Real factors reach triangular_rows.jl:120 and invalidate prepared destinations via triangular_spikes.jl:93. No tests of these adapter obligations are claimed here. Same-upper external mutation is forbidden by the future exclusive-update contract; owner identity alone does not detect it. A failed gather/exception requires wrapper scratch discard. Commit invalidates before reserve and propagates exceptions; successful partial panel commit must not publish whole-update prefix safety.

## Computational-work and memory verdict

No production code changes are present, and this review found no proven unnecessary full-factor scan/copy, basis solve, conversion, unbounded history allocation, or cubic accepted packed rewrite in the isolated candidate. Source accounting confirms separate O(w log n + stored band) eligibility and gather traversals; h*w value zeroing and 2*h*w mask writes per gather; <=b chronological steps, <=sum(w-t) FMA calls and optional 2*w coefficient swap stores per step; two support traversals at commit; h*w reserve mask probes; a single ascending n-ID incidence pass plus h*w mask inspections. Constant-width repeated panels have O(n^2 log n/b) lookup work, O(n^2) arithmetic/admitted stores, and O(n^2/b) ID visits. Sparse preflight and bounded replay can regress total work; no speedup is claimed.

The planned explicit packed write cap is checked before sizehint!/fresh arrays, and counts full changed-column prefix/suffix stores. Same support writes values in place. Changed support allocates two requested-exact-length whole-column arrays sequentially; old/new coexistence and unreachable old buffers awaiting GC remain additional. Scratch has one n-by9 Float64 tile, two masks and eight fixed steps; the stated checked charge is bounded at supported n. Owner release avoids intentional retention of the full upper vector after success/rejection. Touched-mask writes are currently not consumed by the kernel; they are a bounded design-mandated observability cost, not demonstrated numerical necessity or a speedup.

The principal work-budget defect is insufficient executable test coverage in R3, not a proven counter formula failure. Counter13 increments only after a pair of allocation requests succeeds, and counter14 is logical payload, not native/RSS peak; the ledger correctly limits these claims. Counter9 includes early-rejected attempts, so it cannot by itself be an exact division count. Complete allocation attempts, capacity, GC, compilation, timing and whole-factor graph limits remain unqualified. No before/after measurement was permissible under the explicit no-Julia/no-measurement scope.

## Declined to judge

Julia syntax/dispatch/type-inference validity, actual test pass or assertion totals, actual zero-allocation cheap rejection, native capacity/boxing, runtime alias/failure behavior, independent original-B residuals, actual factor/history API composition, whole-update fallback/cache lifecycle, all other precisions/backends, end-to-end solver correctness, time/allocation/RSS gates and performance acceptance. The reviewed experiment is Float64/Int only; no production integration is approved.

## Evidence binding

review-initial.json binds full SHA256 bytes of every repository file consulted (source portions may have been inspected rather than every line), candidate/test/ledger/map, accepted plan/spec, author/entry/tests-first records, this report, and the saved writer. The writer performs only file hashing and text/JSON serialization. Initial rejection artifacts remain immutable for the correction pass.
