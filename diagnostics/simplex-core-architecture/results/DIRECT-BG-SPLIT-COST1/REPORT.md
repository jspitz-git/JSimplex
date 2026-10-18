# Split BG first matched cost result — fixed design stopped

The one independently admitted cost1-300 process completed with exit0. All8cells/160windows (48warm112measured), bitwise paired outputs/modes, unchanged inputs,4416exact residual comparisons and measured compile/recompilezero gates PASS. The admitted integrity/correctness audit and supplementary28checks PASS. Performance admission FAILS: only dense96/native and dense96/Markowitz pass all per-cell first gates; the all-eight gate is FALSE. No opposite-order process, tuning, selected-cell rerun or production integration follows. This is a scoped component cost rejection, not a solver defect or general impossibility claim.

## Saved paired statistics

Ratios are candidate/packed DIRECT BG reference. Time is median of seven paired ratios, not ratio of side medians. Full ranges/MAD/all samples are preserved, including GC outliers.

|Fixture|Backend|Paired time ratio|Range|MAD|Bytes ratio|Events ratio|Final graph ratio|Faster/7|All first gates|
|---|---|---|---|---|---|---|---|---|---|
|sparse32|native|1.096579|0.955826–1.141000|0.038637|1.004777|1.038462|0.983402|2|False|
|sparse32|markowitz|1.086134|1.023121–1.133841|0.022630|1.003043|1.017152|0.981546|0|False|
|dense32|native|1.004363|0.911584–52.433107|0.061692|0.985717|0.983619|1.060710|2|False|
|dense32|markowitz|0.979678|0.941093–1.059593|0.021641|0.971977|0.997350|1.060710|5|False|
|sparse96|native|1.153674|0.941156–1.179388|0.025714|0.979651|0.795464|0.880527|1|False|
|sparse96|markowitz|1.121739|1.096578–1.470676|0.006324|0.994173|0.965566|0.875880|0|False|
|dense96|native|0.763948|0.267520–0.921875|0.157927|0.966363|0.750808|1.094761|7|True|
|dense96|markowitz|0.772089|0.193710–0.949951|0.015958|0.951084|0.822391|1.094761|7|True|

All measured final and all88probe checkpoint factor graphs satisfy<=1.10reference. Sparse96 final graph falls roughly12%; dense96 grows9.476%. Sparse32 aggregate bytes and events increase, so it fails the allocation gate despite smaller final graphs. Dense32 fails the>=5%time threshold on both backends. Sparse32/96 are slower on paired medians. Dense96 is locally22.8–23.6%faster in this one process; it is not a repeatability/universal/end-to-end speedup. Reference remains packed DIRECT BG, not the old Block candidate; no claim of measured delta specifically versus the previous Block run is made.

GC is enabled. Five measured windows record GC: dense32/native candidate pair6; dense96/native reference pairs4,7,9; dense96/Markowitz reference pair8. Dense32/native candidate pair6 total16.1861ms includes14.9743msGC, ratio52.4331. These observations are retained without trimming or timing subtraction; no isolated arithmetic/allocator cause inferred. All112measured compile/recompile fields are zero.

## Structural work and memory

All fixed structural schedules and83counter/partition/backing checks pass. Repeated4:7free splits+1exact fit,32slots unchanged,K16,remainders28..4. Monotone32:5relocations,31live tuples moved/31old-capacity clears. Fragmented refill:finalC304,K36,4free splits18exact fits,2descriptor growths,1680Bnewmetadata/1120Bcopied/max1680Bmetadata coexist,15relocations93movedtuples93clears. These are source-instrumented operations outside timed windows, not allocation events or causal timing attribution. Initial structural helper setup is outside reset counters and remains recorded in initial storage/resources.

All11checkpoints/cell include full extent partition/free chains/active slack/backing lengths, upper and whole-factor graphs.83fixed integer counters belong only to renamed untimed probe; measured candidate remains exact GREEN. Explicit source call budget200constructions400refactors1472replacements2944FTRAN1472BTRAN, no factor copies/public solve/workspace; lower/backend/import/normalization work additional, not a complete observed native-attempt budget.349structural invariant checks,337sets9explicitreserve/claims; source70clockreads per timed lifecycle symmetric. Scratch, initial setup/export, refactors and current histories remain included. Allocation values are aggregate GC traffic, graphs are reachable Julia memory, RSS is process peak; none proves native frees/physical heap completeness.

Inclusive launcher elapsed16.076766221995s (not a kernel benchmark), guard elapsed15.503405316995s, peakchildRSS875740KiB. 15resource samples, minimum availableRAM22389776KiB, maxswap0KiB; terminalRAM23108240KiB. All246groups ANDsessions clear/no visible Julia; boot/start_ticks/command bound.

Fresh admission454checks passed after one preserved reviewer-only substring-count failure; exact1832input/nineevidence bindings. No author/driver/candidate fix and no numerical retry. Runtime result is now subject to separate independent numerical/work/memory review. Existing preparation scope no-execution statements are historical, not revised; the new explicit user allowance authorizes this sole run. All old evidence remains frozen. Master26e2291745999f485a74f643298ca997d65c7205 and src/test/env/CI/STATUS/roadmap unchanged. Broad acceleration plan remains open; this fixed split-block cost design is stopped.
