"""New post-exit report generation from immutable saved results. No numerical calls."""
from pathlib import Path
import json,tomllib,csv
E=Path(__file__).resolve().parent;D=E.parent/'DIRECT-BG-SPLIT-COST-PREPARATION';run=D/'runs/cost1-300';out=run/'output';a=json.loads((run/'audit.json').read_text());post=json.loads((E/'postcheck.json').read_text());p=json.loads((out/'process.json').read_text());inv=json.loads((run/'invocation.json').read_text());res=[json.loads(s) for s in (out/'resources.jsonl').read_text().splitlines()]
rows=[];gc=[]
for idx,cell in enumerate(a['cells'],1):
 s=cell['statistics'];r=post['cells'][idx-1];tr=s['seconds']['paired_ratio']
 rows.append([cell['fixture'],cell['backend'],f"{tr['median']:.6f}",f"{tr['minimum']:.6f}–{tr['maximum']:.6f}",f"{tr['mad']:.6f}",*[f"{s[k]['paired_ratio']['median']:.6f}" for k in ['bytes','events','retained_bytes']],str(s['faster_pairs']),str(s['time_median_gate'] and s['allocation_gate'] and s['memory_gate'] and s['faster_pairs']>=3)])
 for w in range(7,21):
  z=tomllib.loads((out/f'window-{idx}-{w}.toml').read_text())
  if z['gc_seconds']>0:gc.append(dict(fixture=cell['fixture'],backend=cell['backend'],pair=z['pair'],side=z['side'],seconds=z['seconds'],gc_seconds=z['gc_seconds']))
header=['Fixture','Backend','Paired time ratio','Range','MAD','Bytes ratio','Events ratio','Final graph ratio','Faster/7','All first gates']
with (E/'summary.csv').open('x') as f:
 wr=csv.writer(f);wr.writerow(header);wr.writerows(rows)
text='''# Split BG first matched cost result — fixed design stopped

The one independently admitted cost1-300 process completed with exit0. All8cells/160windows (48warm112measured), bitwise paired outputs/modes, unchanged inputs,4416exact residual comparisons and measured compile/recompilezero gates PASS. The admitted integrity/correctness audit and supplementary28checks PASS. Performance admission FAILS: only dense96/native and dense96/Markowitz pass all per-cell first gates; the all-eight gate is FALSE. No opposite-order process, tuning, selected-cell rerun or production integration follows. This is a scoped component cost rejection, not a solver defect or general impossibility claim.

## Saved paired statistics

Ratios are candidate/packed DIRECT BG reference. Time is median of seven paired ratios, not ratio of side medians. Full ranges/MAD/all samples are preserved, including GC outliers.

'''
text+='|'+'|'.join(header)+'|\n|'+'|'.join(['---']*len(header))+'|\n'
text+=''.join('|'+'|'.join(row)+'|\n' for row in rows)
text+='''
All measured final and all88probe checkpoint factor graphs satisfy<=1.10reference. Sparse96 final graph falls roughly12%; dense96 grows9.476%. Sparse32 aggregate bytes and events increase, so it fails the allocation gate despite smaller final graphs. Dense32 fails the>=5%time threshold on both backends. Sparse32/96 are slower on paired medians. Dense96 is locally22.8–23.6%faster in this one process; it is not a repeatability/universal/end-to-end speedup. Reference remains packed DIRECT BG, not the old Block candidate; no claim of measured delta specifically versus the previous Block run is made.

GC is enabled. Five measured windows record GC: dense32/native candidate pair6; dense96/native reference pairs4,7,9; dense96/Markowitz reference pair8. Dense32/native candidate pair6 total16.1861ms includes14.9743msGC, ratio52.4331. These observations are retained without trimming or timing subtraction; no isolated arithmetic/allocator cause inferred. All112measured compile/recompile fields are zero.

## Structural work and memory

All fixed structural schedules and83counter/partition/backing checks pass. Repeated4:7free splits+1exact fit,32slots unchanged,K16,remainders28..4. Monotone32:5relocations,31live tuples moved/31old-capacity clears. Fragmented refill:finalC304,K36,4free splits18exact fits,2descriptor growths,1680Bnewmetadata/1120Bcopied/max1680Bmetadata coexist,15relocations93movedtuples93clears. These are source-instrumented operations outside timed windows, not allocation events or causal timing attribution. Initial structural helper setup is outside reset counters and remains recorded in initial storage/resources.

All11checkpoints/cell include full extent partition/free chains/active slack/backing lengths, upper and whole-factor graphs.83fixed integer counters belong only to renamed untimed probe; measured candidate remains exact GREEN. Explicit source call budget200constructions400refactors1472replacements2944FTRAN1472BTRAN, no factor copies/public solve/workspace; lower/backend/import/normalization work additional, not a complete observed native-attempt budget.349structural invariant checks,337sets9explicitreserve/claims; source70clockreads per timed lifecycle symmetric. Scratch, initial setup/export, refactors and current histories remain included. Allocation values are aggregate GC traffic, graphs are reachable Julia memory, RSS is process peak; none proves native frees/physical heap completeness.

'''
text+=f"Inclusive launcher elapsed{inv['elapsed_seconds']:.12f}s (not a kernel benchmark), guard elapsed{p['elapsed_including_launch']:.12f}s, peakchildRSS{p['child_maxrss_kib']}KiB. {len(res)}resource samples, minimum availableRAM{min(s['available_kib'] for s in res)}KiB, maxswap{max(s['swap_used_kib'] for s in res)}KiB; terminalRAM{p['terminal_memory']['available_kib']}KiB. All246groups ANDsessions clear/no visible Julia; boot/start_ticks/command bound.\n"
text+='''
Fresh admission454checks passed after one preserved reviewer-only substring-count failure; exact1832input/nineevidence bindings. No author/driver/candidate fix and no numerical retry. Runtime result is now subject to separate independent numerical/work/memory review. Existing preparation scope no-execution statements are historical, not revised; the new explicit user allowance authorizes this sole run. All old evidence remains frozen. Master26e2291745999f485a74f643298ca997d65c7205 and src/test/env/CI/STATUS/roadmap unchanged. Broad acceleration plan remains open; this fixed split-block cost design is stopped.
'''
with (E/'REPORT.md').open('x') as f:f.write(text)
with (E/'gc-windows.json').open('x') as f:json.dump(gc,f,indent=2);f.write('\n')
print('Saved8cell report; measured GC windows:',len(gc));print(gc)
