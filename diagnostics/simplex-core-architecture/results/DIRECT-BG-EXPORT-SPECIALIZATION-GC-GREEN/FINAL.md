# Fixed-GC GREEN accepted for Task2

The single admitted 300-second GREEN attempt passed all 8,640 assertions, all three allocation nonincrease predicates and the complete saved auditor. It completed in 30.376844236 seconds of supervisor time (guard 29.660820036 seconds; outer including integrity checks 51.047715557 seconds). No retry occurred.

| Fixture | Median events reference → candidate | Median bytes reference → candidate |
| --- | ---: | ---: |
| sparse32 | 1,274 → 1,263 | 295,016 → 292,424 |
| dense32 | 1,282 → 1,263 | 755,520 → 741,912 |
| sparse96 | 2,513 → 2,498 | 663,544 → 657,048 |

The reference is packed DIRECT BG and the candidate is the specialized export/import workspace. All 60 windows and 1,440 outputs are preserved; 42 observed windows have zero compilation/recompilation and zero GC. Three complete 17-field preparation records and their raw counters passed. Each preparation includes only the measured GC expression; helper-entry compilation and record construction/I/O remain additional whole-process work. Process-wide GC is not a native-memory release proof.

Correctness and allocation are accepted at this Task2 boundary. Time is not: paired time-ratio medians are 1.057496, 1.032527 and 1.005935, with three faster pairs out of seven per fixture. All three recorded timing gates remain false. Selected retained-result sizes increased by 24, 128 and 136 bytes; these measurements are not complete Task3 peak/graph qualification. No speedup, end-to-end acceptance or production promotion is claimed.

Fresh admission passed 7,513 checks plus final validation before release. Fresh independent result review passed 29,894 checks, accepted without findings and binds exactly 81 run files plus 24 evidence files. It verified all 1,440 exact residuals, 30 paired outputs, complete test tree, metrics and preparation records. No unnecessary new production work or memory cost was found. The first admission checker had a remote-ref ordering assertion error; the first result checker had an entry-summary schema error. Both original sources/results and separate corrected checks are preserved. Neither required a Julia rerun or candidate change.

All 265 prior/new process groups AND sessions were absent after return, with no Julia detected. The host process view retains its explicit limitation for inaccessible executable links; stat identities were readable. No production/test/environment/CI/master changes occurred. All run evidence is frozen. Separate closure and exact staging/committed-blob checks govern publication.

Next is separate preparation and independent review of the Task3 complete paired time/allocation/graph driver and launch conditions. Task3 remains open and no additional numerical process is authorized by this result record alone. Master remains 26e2291745999f485a74f643298ca997d65c7205.
