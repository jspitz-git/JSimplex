# Fixed-GC RED result closure

The single admitted `redgc300` attempt completed with exit 1 and exactly the three expected allocation failures. The saved auditor accepted the expected RED outcome; this is not GREEN acceptance or production promotion.

All 60 windows, 1,440 saved outputs, 30 paired comparisons and three preparation records were preserved. All 42 observed windows had zero compilation/recompilation and zero in-window GC. Independent review passed 29,224 checks, including exact residual bounds, paired bits, preparation schemas/counters and all 262 process groups and sessions. It found no unresolved findings and no unnecessary new production work or retained memory cost.

The RED side named `candidate` is the old workspace implementation. Median allocation events increased from 1,274 to 1,279 (sparse32), 1,282 to 1,291 (dense32), and 2,513 to 2,514 (sparse96). Median bytes decreased in each case, but all three event predicates correctly failed.

The guarded execution took 9.638859276 s, the supervisor 10.304104766 s, and the enclosing invocation including checks 28.485984178 s. These are distinct inclusive scopes, not additive benchmark components. The limit was 300 seconds. Preparation GC expression times were 0.091324099, 0.053518699 and 0.050528599 seconds. The first preparation contained 0.0058142 seconds of compilation. Preparation records exclude helper-entry compilation and record construction/I/O; the enclosing process includes that work. This does not establish native-memory release, observer neutrality or a general speedup.

Admission review passed 7,135 checks before release. The result review binds exactly 81 run files and 17 evidence files. No Julia retry, GREEN run, source/test/environment/CI change or master integration occurred. Historical failures remain preserved. Separate closure and exact publication records govern diagnostic publication.

The next numerical step is a separately sealed GREEN invocation with fresh host preflight and independent exact-stage admission using this accepted RED predecessor. No GREEN allowance is consumed here.
