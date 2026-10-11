# S2-A: private audited-flip qualification

Status: REJECTED for the proposed unconditional eligible path; independent
review accepts closure. No production source, default option or API was changed.

## Numerical and process evidence

- Control census: 80 cases / 1,000 assertions, all five public managers, both
  native/Markowitz backends, Float32/Float64, four actually characterized paths.
- Intended work RED: six state checks pass, two solve-count checks fail (8/4
  versus proposed 5/1 FTRAN/BTRAN). Private GREEN: 12/12.
- Candidate matrix: 80 cases / 960 assertions. Flip chains, flip then pivot,
  scheduled refactorization and flip then unbounded certification pass.
- Safety: 139/139. Includes real infeasible/inconsistent predictions, forced
  certificate rejection, pre-write numerical exception/overflow, limits,
  observer/deadline exception provenance, injected reconstruction exception,
  owner mismatch, external input rejection, staged exclusion and original-path
  BigFloat/Rational Int64/BigInt behavior.
- Dirty entry: 26/26. Nonfinite and actually out-of-bound points reconstruct
  before continued optimization; an expired budget publishes no successful point.
- Existing primal update, point, equation, recovery, storage and direction-price
  regressions: 10,381/10,381, normal compilation, nine files.
- Cost: 128 samples and 64 separate warmups, 16 groups. Three interleaved plain
  pairs and a distinct counted pair per group. All plain samples have zero
  reported compilation. Within each group all final primal hashes and objectives
  match; each returned point passes original-model feasibility and certification.

All attempts have final process reports with unchanged pins. Host runner, child
and driver absence was separately checked after each report. Raw sources/logs
and failed attempts remain in .superpowers/simplex-core-architecture/S2-A.

Preserved diagnostic failures: work-green-1 failed at module loading (Symbol
Pair syntax); safety-contracts-1 omitted recompute!'s generation invalidation
in its expected count (111 passes / 7 failures); dirty-entry-1 used -1 as an
alleged violation of a (-Inf,5] bound (21 passes / 1 failure). Only diagnostic
syntax/expectations/fixtures changed. The corrected dirty test asserts its guard
precondition explicitly. No numerical failure was hidden by these corrections.

## Cost and memory

Each case executes exactly 64 bound flips under fixed Dantzig/native/PFI policy,
with either no factor updates or eight genuine prepared pivot updates. Sparse
matrices have 256 rows; dense matrices have 64 rows. Both are synthetic, dyadic,
well-conditioned histories. Preparation temporarily changes owned costs only
before the invocation, restores final costs and reconstructs independently.
Plain optimizer time excludes construction, warmup, final certificate/hash checks
and retained-size inspection; these are separate in the raw report. Full point
certification and required endpoint reconstruction are inside candidate time.
Both harness variants create an unused/used private context during setup, so
setup comparison does not estimate an eventual production controller's overhead.

Ratios below are candidate/control medians of three plain samples, not a universal
speed ratio. Times are short (roughly 0.4–2.2 ms per 64-flip sample), with visible
noise: one Float64 sparse/history8 paired ratio was 1.568 despite a median 0.739.
Retain all samples; do not select only favorable pairs.

| Type | Matrix | Updates | Reject every audit | Time ratio | Extra optimizer bytes |
| --- | --- | ---: | --- | ---: | ---: |
| Float32 | sparse | 0 | False | 0.526 | 2640 |
| Float32 | sparse | 0 | True | 1.105 | 2640 |
| Float32 | sparse | 8 | False | 0.472 | 2688 |
| Float32 | sparse | 8 | True | 1.165 | 2688 |
| Float32 | dense | 0 | False | 1.282 | 1040 |
| Float32 | dense | 0 | True | 2.003 | 1040 |
| Float32 | dense | 8 | False | 1.219 | 1088 |
| Float32 | dense | 8 | True | 2.124 | 1088 |
| Float64 | sparse | 0 | False | 0.753 | 4896 |
| Float64 | sparse | 0 | True | 1.427 | 4896 |
| Float64 | sparse | 8 | False | 0.739 | 4976 |
| Float64 | sparse | 8 | True | 1.407 | 4976 |
| Float64 | dense | 0 | False | 1.302 | 1808 |
| Float64 | dense | 0 | True | 2.202 | 1808 |
| Float64 | dense | 8 | False | 1.300 | 1888 |
| Float64 | dense | 8 | True | 2.191 | 1888 |

Accepted skips reduce 128 FTRAN / 64 BTRAN to 65 / 1, including the mandatory
endpoint refresh. Reject-all retains 128 / 64 and adds 64 full certificates,
64 current-point copies and prediction work. No solve-count reduction is labeled
an elapsed saving by itself. The one-flip unbounded fixture instead increases
its direction/refresh work from 3/1 to 4/1; scheduled refactorization saves nothing.

Source accounting: each reconstruction visits all nonbasic states, every stored
coefficient of nonbasic structural columns for its RHS, every stored coefficient
for reduced costs, and row/basic vectors. Accepted skips remove 63 such direct
reconstructions in these fixtures but add 64 independent certificates. Each full
certificate scans finite state and all bounds, copies n primal entries, traverses
A for row enclosures, checks row consistency and may invoke exact fallback.
The existing flip kernel also makes two m-sized prediction/update passes. These
are source-derived work descriptions; matrix-element visit counters were not
instrumented and no exact-fallback timing attribution is claimed.

Additional optimizer allocations are 1,040–4,976 bytes and 8–10 events per run,
depending on type/dimensions/history. Candidate point buffers retain 968–4,872
bytes versus no point-buffer allocation in these controls, measured immediately
after optimization before diagnostic final certification. This retained-size
comparison covers that scratch graph, not total workspace or process RSS. The
local context contains fixed scalar counters and one owner reference; no global
workspace registry or per-step retained history is introduced. Endpoint/fallback
copies reuse the owned trial buffer. Existing safeguards cause the added work;
removing them would not be an accepted optimization.

## Decision and limits

Reject the proposed broadly eligible audited-flip path: all four dense accepted
cases slow down by 22–30% and reject-all is 1.1–2.2 times control, despite a useful
sparse signal. Sparse success does not justify silently adding a density threshold,
adaptive policy, weaker certificate or new default. Preserve this as a private
experiment. A future narrower path or cheaper equally strong certificate requires
its own concrete hypothesis and reviewed plan.

This is not completion of broad S2. Degenerate actual flip trajectories, strongly
ill-conditioned failed reconstruction, all-manager performance, long phase II and
both cleanup origins are not qualified by this experiment. It is sufficient to
reject this candidate without spending those broader acceptance runs. Existing
regressions protect helper semantics but do not execute the private cloned path
in every ill-conditioned case. No original-model long performance claim follows.

## Independent final review

Fresh read-only review independently reproduced all 16 cost groups, count and
compilation gates, result fingerprints and current source SHA values. It found
no critical/important blocker to closing this private experiment as REJECTED.
Static clone review found no double flip, skipped scheduled refactorization or
dirty successful endpoint. Additional full certificates/candidate copies and
point buffers are necessary for this design's safeguards; no further unnecessary
copy, growing history or global workspace retention was identified. The cost
regression supports rejecting the design rather than weakening its checks.
Two minor documentation issues (stale current status and an unbounded work label)
were corrected at closure. This review does not approve production promotion.
