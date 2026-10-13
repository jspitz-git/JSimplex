# MA-G: control regressions and a bounded routing decision

2026-10-14. SOURCE/EVIDENCE ONLY. MA-F correctness remains qualified; its overall
performance gate remains NOT ACCEPTED. No Julia, candidate modification, numerical
rerun, production/test/environment/CI change or integration occurred in MA-G.

## Decision

Prepare ONE separate routing-only candidate offline, specified by
[MA-H](../../docs/superpowers/plans/2026-10-14-ma-markowitz-routing-preparation.md).
Restore the original inline upper loop for every non-target scalar and avoid the
MA helper when the sparse pivot count is zero. Keep the existing helper arithmetic,
eligibility, scalar ownership and fallback checks byte-identical. This removes
source-visible exposure of control paths to the MA helper; it does not establish
the cause of all six regressions or promise to pass a future cost gate.

Do not tune the frozen MA-E candidate or rerun MA-F. No threshold, tolerance,
precision, fixture or outlier selection changes are justified by this analysis.

## Preserved measurements

`results/MA-G/analysis.json` independently recomputes all 48 full-forward median,
range and faster-pair results from the fourteen original raw files for measured
pairs 4–10. All 48 agree with the frozen summary. All six target gates pass;
exactly six of 32 control gates fail. All measured compile/recompile fields are
zero. Raw GC windows and outliers remain included.

The table uses median paired C/R ratios. Times are separate side medians of the
four-call windows divided by four, in microseconds; their quotient need not equal
the median paired ratio. Upper/reset includes copyto!, so it is not isolated
arithmetic cost. These are previously measured data, not new measurements.

| Control | Full C/R | Upper/reset C/R | Full reference → candidate µs/call | Upper/reset reference → candidate µs/call |
| --- | ---: | ---: | ---: | ---: |
| star8 sparse Float32 | 1.097561 | 1.000000 | 1.075 → 1.125 | 0.350 → 0.350 |
| star8 dense Float32 | 1.166667 | 0.666667 | 0.150 → 0.175 | 0.075 → 0.050 |
| star32 dense Float32 | 1.125000 | 1.000000 | 0.200 → 0.225 | 0.100 → 0.100 |
| star32 dense Float64 | 1.166667 | 1.000000 | 0.175 → 0.200 | 0.100 → 0.100 |
| core32 sparse Rational{BigInt} | 1.176005 | 1.333333 | 235.425 → 291.975 | 0.075 → 0.075 |
| core32 dense BigFloat128 | 1.088816 | 1.666667 | 228.100 → 247.750 | 0.075 → 0.125 |

All four hardware controls have zero bytes/events in both windows and no GC in
these measured windows. Their upper/reset ratios do not corroborate an upper-loop
slowdown. The tiny windows make timing variation material; no timer-resolution or
compiler-inlining cause was captured. The code extraction is a hypothesis, not a
measured function-call overhead.

Both core controls have S=K=E=0 in recorded metadata: no upper pivots, stored upper
terms or eligible rows. Rational upper/reset has zero bytes/events on both sides;
whole-forward side medians are 683192 → 683408 bytes and 17733 → 17733 events.
That 216-byte difference is not explained by a nonexistent upper arithmetic loop.
Its full-forward regression cannot be attributed to MA scalar updates from these
data. No GC appears in its fourteen full windows.

BigFloat128 core upper/reset changes from 0 to 32 bytes and 0 to 2 events per call;
the same differences appear in full-forward side medians (266464 → 266496 bytes,
8330 → 8332 events). Source enters the rounding comparison before the empty loop.
This association motivates bypassing that call, but does not identify a specific
allocator or explain the full time difference. Candidate pair4 and reference
pair9 full windows contain GC (0.014656 and 0.0139135 seconds respectively), and
remain in the comparison. No GC-stripped result replaces the admitted gate.

## Source contract and work

The exact forward-function inverse restores the reference by replacing one helper
call with the original descending upper loop. Before/after code is otherwise
identical. The whole factor source differs only by that replacement and the helper
block including its introductory comment. Reference/candidate hashes are bound in
the source supplement; other import/dependency differences in the broader overlay
are outside this factor-file inverse.

Hardware types use the generic original-arithmetic helper; they never execute MA
eligibility. BigFloat calls the effective/global MPFR rounding comparison before
the typed helper. Rational goes directly to that helper. Scratch starts as nothing
and is allocated only upon the first eligible row; zero-pivot core controls create
no MA scratch. Standalone helper calls remain part of existing semantic tests.

The proposed forward call-site route adds a scalar exact-type condition and, only
for a target type, one pivot-count test per full solve. Compiler elimination of a
constant type condition is expected but UNVERIFIED. Non-target types execute the
original inline loop; target zero-pivot inputs execute its empty range. All other
prefix/lower/dense-core/suffix work remains exact. No extra vector scan, basis
solve, conversion, copy, cache or persistent memory is proposed. Target nonempty
calls retain O(K) eligibility traversal, original operation order, lazy private
scratch (two BigFloat objects or twelve BigInt leaves), and ordinary division
publishing independently owned scalars. No eligibility, exception or numerical
safeguard is weakened. A retained-memory/native-free claim does not follow.

The proposal is permitted for offline preparation only. Performance and compiler
behavior require a separately admitted short experiment, retaining all 48 cases
and the original target/control thresholds. Existing numerical/work/memory
qualification is evidence for unchanged helper semantics, not a substitute for
qualifying the changed whole-forward route.

## Evidence integrity and limits

Fresh host entry checked diagnostic c4c90561, master6f68e24, remote refs, protected
user files, all90 old process groups AND sessions, no Julia and no actual-source
changes. Previous continuation bytes are preserved under results/MA-G before
editing. No historical audit or measurement was rerun.

Initial new analyze.py ran once and exited1: 58/61 checks passed. Three literal
selectors were wrong (upperfun versus target, whitespace in a helper call, and
an omitted introductory comment). analysis.json retains all three FALSE gates
and all computed data. A separate source-supplement.py ran once: 8/8 PASS,
correcting only those text checks with six hash bindings. The original false
result is not converted to PASS. Analysis has 25 read-time hashes, including its
saved-before-execution script and all fourteen measured raw files.

No new production work or retained memory was introduced by this diagnostic step.
The proposed constant checks require review and measurement; no general speedup,
causal allocation attribution, end-to-end solver benefit or promotion is claimed.
