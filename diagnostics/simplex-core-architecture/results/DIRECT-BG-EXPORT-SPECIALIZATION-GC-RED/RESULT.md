# Fixed post-warm GC RED qualification

One independently admitted redgc300 process completed with exactly three expected allocation failures (Julia exit1, guard/outer success). Saved audit all_passed=true and pure_timeout=false; author postcheck12/12. Full 60windows/1440outputs,30paired comparisons and three17-field preparation records are present; raw attempted/completed GC counts3/3. Observed42windows have zero compile/recompile; no in-windowGC was observed in these42windows. Numerical/input/mode/residual gates passed; allthree allocation-nonincreasing predicates are false as required for RED.

## Expected old-workspace allocation regressions

The driver row named candidate in RED is the OLD workspace implementation, not the specialized GREEN candidate. Median of seven observed windows per side:

| Fixture | Reference events | Old workspace events | Reference bytes | Old workspace bytes |
|---|---:|---:|---:|---:|
| sparse32 | 1274 | 1279 | 294808 | 292872 |
| dense32 | 1282 | 1291 | 755328 | 742744 |
| sparse96 | 2513 | 2514 | 663592 | 657752 |

All three predicates fail on the event count increase despite lower byte traffic. The successful RED establishes detection under the amended schedule, not candidate improvement or a production integration result. Timing and retained-graph statistics remain descriptive; no speedup is claimed from this single process.

## Preparation cost and limits

- sparse32: GC-expression wall 0.091324099s, bytes 8672, events 240, GC time 0.085396399s, compile 0.005814200s, recompile 0.000000000s, pauses 1, full collections 1.
- dense32: GC-expression wall 0.053518699s, bytes 3840, events 240, GC time 0.053168699s, compile 0.000000000s, recompile 0.000000000s, pauses 1, full collections 1.
- sparse96: GC-expression wall 0.050528599s, bytes 3840, events 240, GC time 0.050173899s, compile 0.000000000s, recompile 0.000000000s, pauses 1, full collections 1.

Guard elapsed 9.638859276005s; supervisor elapsed 10.304104765994s; outer elapsed including pre/postchecks 28.485984177998s. These are distinct inclusive scopes, not benchmark differences. The inner preparation records exclude helper entry/first helper compilation, dictionary construction and serialization; these remain in whole-process time. GC/compile durations overlap and are not additive. Three calls do not bound whole-heap work or prove all finalizers drained/native frees or a specific compiled method. First preparation contains observed compilation, while observed lifecycle windows are compile-zero in THIS run only; no general cure/causal-method proof.

Resource samples 9: minimum available RAM 22290540KiB, maximum swap 0KiB; terminal guard also passed. Separate post-return closure covers262PGIDs AND sessions including actualouter129983 and new guard/child, all absent/noJulia. All source/stage/runtime/launch pins match. Original failed red300 and all frozen scripts/raw remain unchanged and were not rerun.

No GREEN or retry occurred. No production/test/environment/CI/master change. Independent result review is required before treating this as the accepted RED prerequisite for future greengc300. That future run needs its own fresh exact admission.
