# Independent MA-Y-FALLBACK review

The analysis is accepted as an examination of stored data and source text. MA-Y
remains NOT ACCEPTED. No critical, important, or minor substantive finding
requiring correction was identified. This review approves neither the candidate
nor any new measurement.

The new review-check.py was saved before its single execution. All 29 checks
passed; review-check.json records 622 SHA-256 bindings. No original script was
executed or imported, the author's analyze.py was not rerun, and no Julia, new
profiler, disassembler, or numerical experiment was used. Source and native
assembly files were only read; the native library was only hashed.

- Independent arithmetic verified all 480 control pairs, including 336 measured
  pairs, 48 process/case summaries, and the exact order and content of all 2,080
  stored journal records in each of the three processes. No sample or GC was
  excluded. Outputs, input/owner preservation, arm order, four calls per window,
  and zero measured compilation agree. Both arms' medians, paired statistics,
  value ranks, and the original auditor agree for all 16 controls in each process.
- All 36 readtime hashes, including 13 original launch pins, 514 source
  identities, six protected files, 74 previous publication hashes, and six
  preserved beforecopy bindings were independently verified. The exact native
  library and all three previous S4-O assembly texts match their saved identities.
  Readtime hashes are not represented as historical launch pins.
- Both complete seven-pair failure tables agree with the raw data. Process3
  BigFloat BTRAN has time medians of 299.575 and 351.150 us/call: the 51.575 us
  difference exceeds the original 29.9575 us allowance. The medians come from
  different pairs; the paired-ratio median of 1.007321966 does not replace the
  prescribed predicate. All 42 scoped BigFloat pairs have zero byte and event
  differences.
- Process3 Rational FTRAN has medians of 3,247,376 and 3,247,408 bytes/window,
  hence +32; the paired-difference median is +48. All seven pairs have 74,525
  events on both sides. Of all 42 Rational pairs, 20 have positive, 18 negative,
  and four zero byte differences; event differences are always zero. All 21
  FTRAN pairs have zero recorded GC. The 41 Rational pairs without recorded GC
  span -560 to +416 bytes; this descriptive check is not a filtered acceptance
  decision.

Text inspection of MA-U candidate.jl confirms that Rational exits at the first
BigFloat type test. Scoped BigFloat passes the type and dimension tests, looks up
the current scope, and falls back to reference because rounding modes differ.
Both branches return before the BigFloat scratch object and MA loops. MA-R
reference.jl calls the original ldiv!. The driver creates two separate deepcopy
bundles and resets the destination outside the timed window; serialization,
ownership checks, and journal flushing also occur outside the window and may
affect later state.

The timing.jl source distinguishes aggregate bytes from events. gmp.jl creates
fresh BigInt owners and attempts to install counted callbacks within try/catch.
Saved native instructions confirm malloc_usable_size use and separate accounting
of a realloc event from the nonnegative difference between new usable size and
the supplied old size. This mechanism permits equal event counts with different
bytes; it does not establish historical callback state, a particular request,
size class, or the cause of +32 bytes.

The current report explicitly acknowledges that varying whole-call times do not
isolate a possible fixed guard-cost component. It does not attribute changes to
scheduling, CPU frequency, cache, GC, or the allocator without evidence. No
remaining causal overclaim was found. The physical causes of individual durations
and native allocations remain unresolved and are correctly identified as such.
The original zero byte tolerance, time allowances, and rejection remain intact;
pooled acceptance was not calculated and aggregate.json does not exist.

Computational-work and memory review under AGENTS.md: no unnecessary new
production work or memory cost was found. git diff HEAD was empty and source hash
identities matched. This change consists entirely of a new offline analysis and
documentation. The existing fallback guard runs on every call; it adds type and
dimension conditions and, for scoped BigFloat, one lookup dependent on the scope
map, rather than a new factor scan, basis solve, copy, or conversion. It adds no
solver cache or retained native objects. Rational does not reach dimension tests
or the lookup. No material guard timing cost is established. Offline scripts
retain a finite amount of raw/journal data and scalar summaries; this is not a
solver hot-path change. A new benchmark is unnecessary for this analysis and was
explicitly prohibited. Numerical safeguards, precisions, and ownership assumptions
remain unchanged.

Declined to judge: subsequent updates to live STATUS/roadmap and final publication
are outside this review; their original contents are verified through the
beforecopies/map. Causal experiments were not performed because this task is
explicitly restricted to stored evidence. No other considered behavior was
silently excluded from assessment.

Language-only correction: the initial Czech review.md and review.json are
preserved byte for byte as review.initial-cs.md and review.initial-cs.json.
The canonical review is translated into English without rerunning the checker or
changing its numerical conclusions. The review-check.json field named failures
records the two original failed cost conditions; it does not report checker
errors or review findings.
