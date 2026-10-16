"""One-shot report from saved summary only; no numerical execution."""
from pathlib import Path
import json
D=Path(__file__).resolve().parent;s=json.loads((D/'summary.json').read_text())
text='''# Native pivot policy component-cost qualification

The sole admitted run completed with exit0 and all admitted integrity/oracle gates true. It compares default C and threshold-one P within the unchanged native Float64 candidate; no public solver, direct prototype or production integration is qualified. The numerical attempt is consumed. This report and exact saved evidence require independent result review before closure.

## Correctness and work

All88windows completed:24warm and64measured, with88constructions,176refactors and4224selected solves (2816forward/1408transpose). Source-derived176fresh native LU+88lu! is not a full native-internal operation ledger. Inputs and owners survived, original control and private-spare lifecycle checks passed. All320 measured region records have zero compile/recompile. The saved default outputs match every original C token; no unexplained mismatch.

All2112 threshold-one equations pass the unchanged exact residual bound. Default passes1936/2112: the176 failures are the repeated sparse96 unit-RHS/BTRAN results,352/528pass in that fixture, with max residual/bound18.861415966018026. Threshold-one sparse96 has528/528pass and max ratio0.00006079091255693325. All4224 residuals are nonzero. Original false default accuracy is preserved and allowed by the admitted diagnostic design; it is not relabeled a pass. No tolerance, precision or safeguard changed.

## Timing and allocations

Each cell below reports eight measured paired P/C ratios; lower is faster. These are small windows in one process. All raw paired ratios and samples are in the original audit and summary.json. Total includes its four inner regions; never add them again. No sample, GC spike or outlier is excluded.

| Fixture / region | Ratio median | MAD | Min–max | C/P median us | C/P median bytes | C/P median events |
| --- | ---: | ---: | --- | --- | --- | --- |
'''
for k,z in s['comparisons'].items():
 t=z['summary'];b=z['bytes'];e=z['events'];text+=f"| {k} | {t['median']:.6f} | {t['mad']:.6f} | {t['minimum']:.6f}–{t['maximum']:.6f} | {z['Cmedian_us']:.4f}/{z['Pmedian_us']:.4f} | {b['Cmedian']:g}/{b['Pmedian']:g} | {e['Cmedian']:g}/{e['Pmedian']:g} |\n"
text+='''
Total paired medians range from0.963886 to1.013807; this does not establish a consistent speedup or a universal no-regression guarantee. Every measured solve region has zero recorded bytes/events for both policies. Total median bytes change by+24 sparse32,-32 dense32,+32 sparse96,0 dense96; paired byte deltas and all event counts remain explicit in summary.json and raw, without rounding differences into equality or declaring allocator noise. Median total event counts match, but **not every individual allocation event count matches**.

Two P dense96 measured windows contain GC: round4 construction10.035801ms with9.274901msGC, construction ratio54.63147 and total ratio15.60737; round10 spare refactor3.7371ms with3.5218msGC, spare ratio31.37783 and total ratio6.31276. These are four nonzero nested-region GC records for two windows, not four collections. Round4 construction has725events versus85C and total845versus205; round10 spare139versus32 and total312versus205. Both compile/recompile remain0. GC overlaps much of those spikes, but actual policy-specific causality and the allocation-source breakdown are unproved; no subtracting GC or waiving the extra recorded traffic. Additional GC-free ratio flags include sparse32 construction4.28244, solve3.00730, total2.57624; sparse96 solve2.14602; dense96 spare4.63492. Their causes remain unknown. All eleven descriptively flagged series/rounds are retained; flags are not rejection or exclusion filters.

The observed benefit is reliable residuals on the targeted sparse96 fixture with similar central timings and unchanged solve-region allocation counts, accompanied by small median setup byte differences and the retained GC/event spikes. It is not a demonstrated general performance improvement. C/P measures a selected-policy tradeoff in one candidate, not overhead against the old binary. Legitimate fill/accuracy costs were not subject to an invented speedup cutoff. No automatic retry, tuning or extra warmup is warranted by these results.

## Memory, numerical strategy and measurement work

| Fixture | C/P L entries | C/P U entries | C/P Julia graph bytes | C/P native numeric bytes (Info units*16) | C/P strategy |
| --- | --- | --- | --- | --- | --- |
'''
for name in ['sparse32','dense32','sparse96','dense96']:
 c=s['factors'][name+':C'];p=s['factors'][name+':P'];text+=f"| {name} | {c['lnz']}/{p['lnz']} | {c['unz']}/{p['unz']} | {c['graph_bytes']}/{p['graph_bytes']} | {c['numeric_units']*16:g}/{p['numeric_units']*16:g} | {c['strategy']:g}/{p['strategy']:g} |\n"
text+=f'''
Sparse96 threshold-one adds15U entries and48reported native numeric bytes; final native peak Info units match within each pair. Active/spare W and Wi lengths remain n on both arms. Sparse cases use actual strategy1(UNSYMMETRIC); dense cases3(SYMMETRIC), where the unchanged symmetric-pivot control remains relevant. Equal Julia graph size does not imply equal native memory, and these Info fields are not an allocation/free ledger.

Output+Info payload2,297,856bytes is retained equally before timing; observed diagnostic graph{s['diagnostic_graph_bytes']}bytes includes containers. Per-solve four Info writes, counters, timing tuples and lifecycle identity checks remain included as specified. Token formatting/serialization, control records and eight factor/graph snapshots are outside regions, yet can affect later GC. No observer-neutrality, native-release or complete import/backend-work claim. No unnecessary NEW production work or memory is introduced by this result step: actual production/test source is unchanged, and the frozen candidate only adds scalar policy metadata/private fresh controls without new F/B/update-loop scans or solves. Observed GC allocation spikes are explicitly unresolved measurement traffic, not proven necessary production overhead or silently erased.

## Execution integrity and continuation

One45second inclusive allowance was used; inner37 guard. Actual inclusive launcher elapsed{s['inclusive_seconds']}seconds includes loading/compilation/output and is NOT a benchmark. Six resource samples: availableRAM minimum21,975,460KiB, swap0; terminal22,346,308KiB; childRSS high-water533,368KiB. No timeout/kill and exit0. Runner254592/start14997081 and child254593/start14997132, boot284d2228-1d9a-4c5f-913c-b9f1098b5838. Fresh216PGIDs AND SIDs/noJulia closure passed. Inaccessible system executable links remain a visibility limit.

Seal1001files, exact admission1002bindings, launch1004pins, original audit156bindings; new postcheck17PASS/10bindings is POST-EXIT supplemental, not a launch pin. Exact-stage review preserved three reviewer-only schema-assumption failures and separate corrections; no numerical retry. Every raw output, false accuracy result and historical failed GREEN/directcost1 remains frozen.

Next, only after independent result acceptance: prepare Task3 OFFLINE public integration candidate/tests and concrete work budget, then review. The accepted plan specifies eight tiny public solves (four ordinary managers x two policies) and one separate PFI recovery-trial fixture; full constructor/solve/callback counts must be frozen before a separately admitted<=60s run. No public integration or new Julia is run by this closure, no production merge or direct-prototype promotion. Existing short-run permission remains; exact-stage admission is still mandatory. Olddirectcost2 remains blocked, CIoff/HHdisabled/automationpaused/master6f68e24 unchanged.
'''
with (D/'REPORT.md').open('x') as f:f.write(text)
print('Report saved from preserved summary')
