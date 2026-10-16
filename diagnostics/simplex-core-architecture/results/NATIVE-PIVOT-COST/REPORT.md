# Native pivot policy component-cost qualification

The sole admitted run completed with exit0 and all admitted integrity/oracle gates true. It compares default C and threshold-one P within the unchanged native Float64 candidate; no public solver, direct prototype or production integration is qualified. The numerical attempt is consumed. This report and exact saved evidence require independent result review before closure.

## Correctness and work

All88windows completed:24warm and64measured, with88constructions,176refactors and4224selected solves (2816forward/1408transpose). Source-derived176fresh native LU+88lu! is not a full native-internal operation ledger. Inputs and owners survived, original control and private-spare lifecycle checks passed. All320 measured region records have zero compile/recompile. The saved default outputs match every original C token; no unexplained mismatch.

All2112 threshold-one equations pass the unchanged exact residual bound. Default passes1936/2112: the176 failures are the repeated sparse96 DSE-RHS/FTRAN results,352/528pass in that fixture, with max residual/bound18.861415966018026. Threshold-one sparse96 has528/528pass and max ratio0.00006079091255693325. All4224 residuals are nonzero. Original false default accuracy is preserved and allowed by the admitted diagnostic design; it is not relabeled a pass. No tolerance, precision or safeguard changed.

## Timing and allocations

Each cell below reports eight measured paired P/C ratios; lower is faster. These are small windows in one process. All raw paired ratios and samples are in the original audit and summary.json. Total includes its four inner regions; never add them again. No sample, GC spike or outlier is excluded.

| Fixture / region | Ratio median | MAD | Min–max | C/P median us | C/P median bytes | C/P median events |
| --- | ---: | ---: | --- | --- | --- | --- |
| sparse32:construction | 0.951193 | 0.188332 | 0.507205–4.282443 | 14.0000/15.9500 | 63184/63216 | 80/80 |
| sparse32:refactor_fresh | 0.951468 | 0.157925 | 0.673575–1.741935 | 12.7500/13.0000 | 63144/63160 | 79/79 |
| sparse32:refactor_spare | 0.980833 | 0.057796 | 0.892857–1.320000 | 7.8500/7.9500 | 47216/47232 | 31/31 |
| sparse32:solve | 1.002009 | 0.056952 | 0.927152–3.007299 | 27.0000/27.4500 | 0/0 | 0/0 |
| sparse32:total | 0.963886 | 0.136371 | 0.725431–2.576244 | 62.8500/66.9500 | 174216/174240 | 194/194 |
| dense32:construction | 1.001936 | 0.033409 | 0.939597–1.061776 | 26.7500/27.1000 | 179288/179288 | 86/86 |
| dense32:refactor_fresh | 1.009645 | 0.029241 | 0.961538–1.362934 | 26.0000/26.0500 | 179248/179240 | 85/85 |
| dense32:refactor_spare | 1.011081 | 0.011494 | 0.952632–1.054054 | 18.0000/18.1000 | 125024/125024 | 33/33 |
| dense32:solve | 0.978688 | 0.036741 | 0.651943–1.025424 | 37.7000/36.9500 | 0/0 | 0/0 |
| dense32:total | 1.000939 | 0.033464 | 0.831547–1.072451 | 110.6500/109.0000 | 484256/484224 | 208/208 |
| sparse96:construction | 0.962179 | 0.025924 | 0.548013–1.025788 | 35.2000/34.6500 | 134728/134744 | 82/82 |
| sparse96:refactor_fresh | 0.956648 | 0.049901 | 0.745455–1.033435 | 33.4000/32.3500 | 134680/134696 | 81/81 |
| sparse96:refactor_spare | 0.968037 | 0.020132 | 0.852000–1.143519 | 21.9000/21.2000 | 92208/92208 | 31/31 |
| sparse96:solve | 0.970433 | 0.036789 | 0.820370–2.146018 | 45.2500/44.2500 | 0/0 | 0/0 |
| sparse96:total | 0.971995 | 0.029126 | 0.740700–1.136444 | 137.5500/134.6000 | 362288/362320 | 198/198 |
| dense96:construction | 0.980105 | 0.047076 | 0.876712–54.631470 | 180.2000/174.7500 | 1.06956e+06/1.06956e+06 | 85/85 |
| dense96:refactor_fresh | 0.998858 | 0.057589 | 0.589427–1.343452 | 172.0500/173.7000 | 1.06951e+06/1.06951e+06 | 84/84 |
| dense96:refactor_spare | 1.016005 | 0.058595 | 0.921739–31.377834 | 119.2000/126.6500 | 647904/647904 | 32/32 |
| dense96:solve | 1.012013 | 0.014549 | 0.746786–1.038539 | 200.1500/202.8500 | 0/0 | 0/0 |
| dense96:total | 1.013807 | 0.116691 | 0.811489–15.607371 | 678.6500/711.1500 | 2.78765e+06/2.78765e+06 | 205/205 |

Total paired medians range from0.963886 to1.013807; this does not establish a consistent speedup or a universal no-regression guarantee. Every measured solve region has zero recorded bytes/events for both policies. Total median bytes change by+24 sparse32,-32 dense32,+32 sparse96,0 dense96; paired byte deltas and all event counts remain explicit in summary.json and raw, without rounding differences into equality or declaring allocator noise. Median total event counts match, but **not every individual allocation event count matches**.

Two P dense96 measured windows contain GC: round4 construction10.035801ms with9.274901msGC, construction ratio54.63147 and total ratio15.60737; round10 spare refactor3.7371ms with3.5218msGC, spare ratio31.37783 and total ratio6.31276. These are four nonzero nested-region GC records for two windows, not four collections. Round4 construction has725events versus85C and total845versus205; round10 spare139versus32 and total312versus205. Both compile/recompile remain0. GC overlaps much of those spikes, but actual policy-specific causality and the allocation-source breakdown are unproved; no subtracting GC or waiving the extra recorded traffic. Additional GC-free ratio flags include sparse32 construction4.28244, solve3.00730, total2.57624; sparse96 solve2.14602; dense96 spare4.63492. Their causes remain unknown. All eleven descriptively flagged series/rounds are retained; flags are not rejection or exclusion filters.

The observed benefit is reliable residuals on the targeted sparse96 fixture with similar central timings and unchanged solve-region allocation counts, accompanied by small median setup byte differences and the retained GC/event spikes. It is not a demonstrated general performance improvement. C/P measures a selected-policy tradeoff in one candidate, not overhead against the old binary. Legitimate fill/accuracy costs were not subject to an invented speedup cutoff. No automatic retry, tuning or extra warmup is warranted by these results.

## Memory, numerical strategy and measurement work

| Fixture | C/P L entries | C/P U entries | C/P Julia graph bytes | C/P native numeric bytes (Info units*16) | C/P strategy |
| --- | --- | --- | --- | --- | --- |
| sparse32 | 83/83 | 83/83 | 7408/7408 | 5072/5072 | 1/1 |
| dense32 | 528/528 | 528/528 | 37072/37072 | 11616/11616 | 3/3 |
| sparse96 | 234/234 | 248/263 | 16656/16656 | 14288/14336 | 1/1 |
| dense96 | 4656/4656 | 4656/4656 | 302288/302288 | 82784/82784 | 3/3 |

Sparse96 threshold-one adds15U entries and48reported native numeric bytes; final native peak Info units match within each pair. Active/spare W and Wi lengths remain n on both arms. Sparse cases use actual strategy1(UNSYMMETRIC); dense cases3(SYMMETRIC), where the unchanged symmetric-pivot control remains relevant. Equal Julia graph size does not imply equal native memory, and these Info fields are not an allocation/free ledger.

Output+Info payload2,297,856bytes is retained equally before timing; observed diagnostic graph2510224bytes includes containers. Per-solve four Info writes, counters, timing tuples and lifecycle identity checks remain included as specified. Token formatting/serialization, control records and eight factor/graph snapshots are outside regions, yet can affect later GC. No observer-neutrality, native-release or complete import/backend-work claim. No unnecessary NEW production work or memory is introduced by this result step: actual production/test source is unchanged, and the frozen candidate only adds scalar policy metadata/private fresh controls without new F/B/update-loop scans or solves. Observed GC allocation spikes are explicitly unresolved measurement traffic, not proven necessary production overhead or silently erased.

## Execution integrity and continuation

One45second inclusive allowance was used; inner37 guard. Actual inclusive launcher elapsed7.040155750000849seconds includes loading/compilation/output and is NOT a benchmark. Six resource samples: availableRAM minimum21,975,460KiB, swap0; terminal22,346,308KiB; childRSS high-water533,368KiB. No timeout/kill and exit0. Runner254592/start14997081 and child254593/start14997132, boot284d2228-1d9a-4c5f-913c-b9f1098b5838. Fresh216PGIDs AND SIDs/noJulia closure passed. Inaccessible system executable links remain a visibility limit.

Seal1001files, exact admission1002bindings, launch1004pins, original audit156bindings; new postcheck17PASS/10bindings is POST-EXIT supplemental, not a launch pin. Exact-stage review preserved three reviewer-only schema-assumption failures and separate corrections; no numerical retry. Every raw output, false accuracy result and historical failed GREEN/directcost1 remains frozen.

Next, only after independent result acceptance: prepare Task3 OFFLINE public integration candidate/tests and concrete work budget, then review. The accepted plan specifies eight tiny public solves (four ordinary managers x two policies) and one separate PFI recovery-trial fixture; full constructor/solve/callback counts must be frozen before a separately admitted<=60s run. No public integration or new Julia is run by this closure, no production merge or direct-prototype promotion. Existing short-run permission remains; exact-stage admission is still mandatory. Olddirectcost2 remains blocked, CIoff/HHdisabled/automationpaused/master6f68e24 unchanged.
