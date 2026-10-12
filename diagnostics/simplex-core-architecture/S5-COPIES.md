# S5-C: consecutive restoration cost copies

Status: reviewed and integrated as mastere7014fb (production88a2411). Base master3220118,
diagnostic base83fab02. Only restore_perturbations! changes; no tolerances,
certificates, scans, reconstruction, bound-copy ordering or observer events change.

## Contract and cost

The first cost copy remains unconditional after the existing owner/activity checks.
The second is omitted only if active_costs === workspace.costs and a constant-time
predicate proves the source and destination byte ranges disjoint. Detached,
source-self and partly overlapping buffers retain both copies. Checking after the
first copy preserves failure/publication order. Unknown/union element layouts and
zero storage stride conservatively retain both copies. Empty concrete vectors need
no second no-op copy.

The predicate uses Base.elsize for actual concrete element storage (not sizeof(T)
for reference-containing scalars), checks length <= typemax(UInt) div stride before
multiplication, and subtracts pointers only in the nonnegative direction. It never
constructs a potentially overflowing end pointer. GC.@preserve retains both vectors
through pointer inspection. Valid contiguous Vector storage is required; no value
scan, scalar conversion, solve, scratch allocation or retained cache is added.

Execution frequency is cold journal restoration, not each pivot/candidate. The
eligible path removes one O(N) copy, N = length(costs), with constant-time checks.
Detached destinations short-circuit before the range predicate. Bounds remain at
four copies when active; interleaved writes forbid assuming their redundancy.
Rational/BigFloat buffers retain references and stored value precision as before.
No inference about natural perturbation frequency or whole-solver speedup follows.

## Completed evidence

- layout-1:184checks,48offset/direction pairs across6numeric types;9auditchecks,
  unchanged independently verified pins. Actual stride, partial overlap, adjacency,
  empty/disjoint cases and conservative abstract/union fallback checked. Diagnostic
  predicate only; no production result inferred before RED.
- work-red-1: unchanged source,462semantic checks passed,30work checks passed and
  12expected failures (2copies instead of1) for identity-aliased cost destinations.
  No errors; exit1 and pins preserved. Detached/self/partial overlap work passed.
- work-green-1: identical driver,462semantic+42work checks pass;8post-exit audit
  checks and independent pins/source verified. Six numeric types, original values,
  signed zeros/BigFloat precision, bound activity, foreign owner, inactive journal,
  short detached destination after first publication, changed problem objective,
  and throwing observer compared with the pre-change operation order.

- focused-1:1463/1463 assertions across9relevant current-source files, including
  empty storage, real production range predicate, unequal-length overlap/adjacency,
  unknown/union fallback, zero direct predicate allocation, original cost storage,
  actual stalled dual/primal retirement, partial pricing and basis recovery. Exit0,
  source/pins independently verified. This is not a passing full CI suite.
- cost-1:52fixtures/312samples, three alternating-order pairs each, all compile0 and GC0;
  six scalar types, N32/8192 and Float64 N262144, aliased/detached destination and
  active/inactive bounds. Setup excluded; timed region includes repeated journal
  rearming and complete restoration, with no observer. Actual work counts come
  from RED/GREEN, cost record copy counts are derived from that contract.

## Cost interpretation and limits

All156 paired allocation-event counts match. Allocation bytes differ in144pairs;
initial exact-byte-equality analysis assertion is explicitly rejected and preserved
in cost-1-initial-analysis-rejected.json. Byte deltas are retained per batch in
cost-1-analysis.json; cause is not established, and no whole-kernel byte equality
or byte-saving claim is made. The direct production predicate test allocates0Julia
bytes for each supported scalar; no cache or retained storage is introduced.

Across52groups, eligible large-vector side-median candidate/baseline time ratios
are0.4496–0.9354. Small aliased cases range0.7257–1.3140 (largest median added
time50.8ns per restoration). Detached controls range0.8451–1.1463, including
Float64 N262144 with active bounds at1.0863 (+46.3microseconds per restoration).
That detached path keeps the same copies and adds only the identity branch; the
observed timing spread is not attributed causally to that branch. Three warm pairs
are limited evidence; no universal speedup or absence of elapsed regression is
claimed. Bound-active kernels keep all four O(N) bound copies. Source-level benefit
is exactly one fewer N-element cost copy in the qualified identity path.

- trajectories-1:152exact selected-state/event pairs/153assertions, exit0,
  independent pins/source verified;9supplemental checks. Reused144S5-B fixture
  definitions on actual baseline/candidate plus8sparse/dense HH cases, both
  algorithms/backends.88original-feasible OPTIMAL,32TIME_LIMIT,16alien proof
  rejections,16preserved observer exceptions. No certificate transfer.

## Integration

Fresh independent numerical/work/memory review accepted without findings; see
S5-COPIES-REVIEW.md. Production88a2411 -> mastere7014fb; master-1 passed668/668,
all12audit gates/592pins, actual main source, accepted source equality and preserved
user hashes. Separate host absence verified for368680/368681/368668 on recorded
boot. Full historical CI remains unresolved and disabled; S6 is not passed.
Raw failed/rejected analyses remain preserved. Remote publication is recorded in
STATUS.md after verification. Broader S2/S3/S4/S5/S6 are not closed by this chunk.
