# S4-P: nonsymmetric history and inclusive lifecycle cost contract

SOURCE/EVIDENCE ONLY; no Julia, numerical factorization, native calls, library loading,
hooks, compilation, production/test/environment changes or accepted-script reruns.
One separate prospective S4-Q plan freezes new input bits and bounded work. No current
performance result, native retention proof or production enablement is claimed.

## Result and exact input qualification

[Future measurement plan](../../docs/superpowers/plans/2026-10-12-hh-history-lifecycle-cost-measurement.md)
defines sparse/dense nonsymmetric48 fixtures (142/2304 nonzeros), six column replacements
[3,17,31,31,17,3], two refactors at stages3/6, and no factor copies. Full bits are in
results/S4-P/exact-inputs.json (SHA25685874a35de281a9de4ce4d49c7f17f176d37a1597fc557ae64469202fcfd9b06).
The input generator constructs exact Fractions only:10 checks pass, all19,138 stored
coefficient/RHS/incoming/solution entries round-trip exactly through binary64. No
floating or rational factorization was needed. Initial row dominance margins are
765/128 (sparse) and12241/2048 (dense); every stage has margin>5. Positive diagonal
and strict row dominance prove nonsingularity. Matrices remain nonsymmetric and same
pattern; after six replacements B6=B0, while each transition changes a complete column.

For incoming a, B_old^-1*a=e_j+B_old^-1*delta. The row-dominance inverse bound yields
pivot>=1-||delta||inf/margin>39/40. Each delta is nonzero and not proportional to the
old column: its row j-1 is zero whereas the old column has a nonzero at that row.
Thus directions are not unit vectors in exact arithmetic. The proof qualifies inputs,
not rounded HH outputs or an executed prepared-cache path. The frozen64eps scaled
exact residual oracle must validate each future output; no tolerance/precision change.

## Work and ownership boundary

Per lifecycle:1 constructor,6 updates,2 refactors,6 prepared and9 ordinary FTRAN,
9 BTRAN (24 direct solves). Two runs of history lengths0,1,2 at incoming solves and
1,2,3 at post-update F/B give30 _hh_apply! entries, plus6 update-internal unit
transposes. Native numeric/extraction entries3 and orientation validation solves<=3
are source-derived bounds, not measured native counts. Warm8 plus measured32 lifecycles
freeze40 constructors,80 refactors,240 updates,960 direct solves (600F/360B),120
numeric/extraction entries,60 reference plus20 candidate-initial symbolic entries,
40 candidate pattern scans and<=120 orientation solves. The plan details all counts.

The outer window owns one complete factor history and explicit full GC after a
non-inlined owner function returns nothing. Inner refactor windows are subsets, reported
separately without addition/subtraction attribution. No old native owners/base/history
snapshots are retained. Outputs are preallocated numeric vectors (46,080 Float64
values across40 lifecycles); no factor can escape in timer values or records.
Ownership release is a source property, not proof of finalizer/native-free completion.
Natural/explicit GC and allocator behavior can affect timings. Inputs/outputs survive
outside these windows, so the experiment does not claim whole-process memory lifetime.

Diagnostic state/control/equality checks, attempt counters and nested timer records
have bounded work included in outer timing, identical architecture on both sides.
Explicit additional direction scans:6x48 per lifecycle; runtime residual evaluation
24 matrix-vector products per lifecycle is outside timing; exact post-exit validation
adds no solver calls. Packed update work/pool memory scales with factor fill/support;
retirement bookkeeping scales with3 records per refactor, not just n. The plan explicitly
counts internal prepared copies, validation scans and unit reachability/sorting. No
avoidable production work or memory is introduced: this step changes documentation
and exact offline diagnostic data only. Benchmarking documentation would add no evidence.

## Evidence reuse and metric limits

Reuse G publication/history qualification only with current HH and factorization source
hashes matched against G launch pins; no generic lifecycle rerun. G establishes its own
small cases, not new48-fixture numerical correctness. M's32 accepted windows and raw
samples remain untouched and are not this inclusive-history gate. O's installed runtime
counter analysis remains a separate interpretation: Julia aggregate GC allocation fields
can include native jl_* work; they are not exclusively Julia objects or a live-native
balance. No O trace, H caller inventory or L metric inventory is repeated.

Native retention remains OPEN; flat RSS, completed GC, vanished roots and graph sizes
cannot prove successful frees or complete allocation balance. No allocator hooks are
proposed. Candidate guard remains O(n+nnz); same-type conversion may be identity but
wrapper CSC copies/extraction remain. Paired output differences must remain visible;
no isolated symbolic attribution, universal speedup or native-memory savings claim.

## Acceptance and continuation

S4-P freezes an offline contract only. S4-Q must implement exactly this schedule,
preflight/inverse clone/pins and resource guards, then stop without retries if any
measured compile/recompile field is nonzero or another runtime/exit/oracle gate fails.
Source, test, CI and master remain unchanged. HH reuse stays disabled. Other consumers,
controls, precision/platform coverage, native retention and broader S4/S6 stay OPEN;
S2-A, S6-J and whole S6-AF remain rejected/not accepted.
