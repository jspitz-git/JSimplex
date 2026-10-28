# Complete-function epsilon, bound and auxiliary measurements

Baseline actual master235eedf33901fe8c4cc06a3d8c3508ef2fcbb718. Independent result review accepted A/B/C for production qualification, not yet production publication. OrdinaryTest only, no custom recorder/manual testset stack.

## Evidence and original failure

Initial attempt remains FAILED:55,626passed/1failed/2errors, exit1, no timeout. Source trace identifies unsupported original Rational auxiliary wrapper: `_precision_current_bits(ws)` calls undefined `precision(Rational)` before C's changed body. The real LP controller already excludes exact types. No production precision fix, added method, or numerical workaround was made. The original1,196 complete paired cells/21,528windows/1,232prep are frozen and accepted only by separate strict prefix audit. Previously missing30 B/RationalInt64 cells were completed once:1,428ordinarychecks passed/540windows/34prep, shared27.549373439s. Their conventional RationalC tests preserve MethodError and parent values/owners/budget. Eight originally planned RationalC cells are unmeasured and excluded, not silently passed.

The supported union has1,226cells/22,068windows/1,266prep across19contexts. Every measured compile/recompile count is zero;4GCwindows remain included. Each cell has3warm pairs and9alternating measured pairs. Fixture/reset/cold/warm/validation/consumption/GC preparation is separate. Per-cell full values, scalar limb alias graph, array ownership, precision/rounding, auxiliary status/solution/witness/work budget and unchanged inputs are checked. A covers floating types only; B covers BigFloat/RationalBigInt with unchanged native/fixed rational controls; C covers actual supported floating auxiliary routes, not Rational C execution.

## Statistics

The time column below is the median across cells of each cell's9paired time ratios (candidate/reference). This is not a pooled weighted end-to-end speedup. Event and byte columns are ranges of differences between per-cell medians; they are not bounds on individual paired differences. All slower cells, full paired ratios/extrema/MAD and allocation outliers remain in summary.json and both raw TOMLs.

|Arm|Context|Bounds/result|Cells|Time ratio|Cell time range|Events saved|Bytes saved|
|---|---|---|---:|---:|---|---|---|
|A|BigFloat|bad|180|0.941332|0.810811–1.000000|30–30|912–1200|
|A|BigFloat|good|180|0.951649|0.849315–1.404908|30–30|912–1200|
|B|BigFloat|box|90|1.000000|0.963922–1.068966|0–0|0–0|
|B|BigFloat|fixed|90|1.000000|0.918182–1.041801|0–0|0–0|
|B|BigFloat|free|90|0.573089|0.405063–0.655172|192–576|5376–20736|
|B|BigFloat|lower|90|0.891952|0.582160–1.017566|96–288|2688–10368|
|B|BigFloat|mixed|90|0.893845|0.866667–0.964384|96–288|2688–10368|
|B|BigFloat|native_free|90|0.573542|0.394444–0.640523|192–576|5376–20736|
|B|BigFloat|native_mixed|90|0.894977|0.845538–0.970310|96–288|2688–10368|
|B|Rational{BigInt}|box|6|0.970959|0.920054–1.027149|0–0|-48–16|
|B|Rational{BigInt}|fixed|6|0.995208|0.831169–1.132353|0–0|-16–32|
|B|Rational{BigInt}|free|6|0.596591|0.444444–0.684466|192–576|5376–16352|
|B|Rational{BigInt}|lower|6|0.920907|0.825581–0.956790|96–288|2656–8064|
|B|Rational{BigInt}|mixed|6|0.925370|0.861314–1.006494|96–288|2688–8064|
|C|BigFloat|good|60|0.998098|0.947537–1.076707|4–4|176–176|
|C|Float32|good|4|0.986842|0.866667–1.000000|4–4|176–176|
|C|Float64|good|4|0.990203|0.900000–1.051948|4–4|160–192|

A saves30allocation events and912–1200bytes per complete BigFloat direction residual call; native paths are unchanged controls. B removes0..2 unused zero constructors per variable, retaining finite-bound conversions and all original returned metric arithmetic/aliasing. Free/mixed bounds show benefit; fully bounded controls have no intended work change, including preserved individual counter/byte/time fluctuations with uncaptured cause.

C removes two duplicate basis vectors (m Int entries and m+n+k enum entries), retaining the first fresh copy/vcat and later independent workspace copies. Every supported cell median saves4GCcounter allocation events and160–192bytes; source constructor count is not a native allocation count. All72native pairs save4events; Float64 individual byte savings range0–320. BigFloat540pairs include537savings of4events,2savings of100,1increase of92; individual bytes range minus1360 to plus1712, while every cell median saves176bytes. C time is essentially unchanged with short-sample/GC outliers; no meaningful C speedup is established. Permanent C allocation gates therefore use native event reduction and median byte reduction, not a BigFloat all-pair event or timing claim.

Counters are Julia aggregate GC allocation traffic, potentially including native allocations, not a native malloc/free or live-retained-memory ledger. Source removes work without adding scans/solves/conversions/caches; B/C introduce cold method/code metadata whose native retention is unmeasured. No extra data field or persistent owner. Detailed work frequency/scaling/ownership is in source-review.json/result-review.json and WORK-MEMORY.md; route-review.json corrects the earlier overbroad all-precision C qualification premise.

These local helper gains do not establish solver-wide speedup. Source numerical order, tolerances, guards, callbacks/stop/repair/finally semantics remain unchanged. Production RED/GREEN/actualMASTER and exact publication remain separate next steps.
