"""Generate non-overlapping tables from audited census and reference reports."""
from pathlib import Path
import json,tomllib,statistics,re
root=Path(__file__).resolve().parents[1]
records=json.loads((root/'results/summary.json').read_text())
assert len(records)==4
lines=['# Measured time budgets','','One paired reference and census per slice; sampling completed only for prefixes. A second dual-origin cleanup reference is retained with the stalled attempt. No speedup claim.',
       'All times are seconds. GC is included in wall time. Allocation bytes are cumulative, not peak memory.','',
       '| Slice | Steps | Reference | Sampling | Census | Reference GC | Reference allocated GiB | Read / deserialize | Process peak RSS GiB |',
       '|---|---:|---:|---:|---:|---:|---:|---:|---:|']
for row in records:
 case=row['case'];folder=root/'results'/case
 p=tomllib.loads((folder/'plain.toml').read_text())
 peak=re.search(r'Maximum resident set size \(kbytes\): (\d+)',(folder/'run.log').read_text())
 assert peak
 sampling=f"{row['seconds']['profile']:.3f}" if 'profile' in row['seconds'] else 'unavailable'
 steps=p['iterations']-p['phases'][0]['iteration'] if case.startswith('cleanup') else p['iterations']
 assert steps==(256 if case.startswith('cleanup') else (2000 if case.endswith('primal') else 4000))
 assert all(v==0 for v in row['compile_seconds'].values()),(case,row['compile_seconds'])
 lines.append(f"| {case} | {steps} | {p['seconds']:.3f} | {sampling} | {row['seconds']['census']:.3f} | {p['gc_seconds']:.3f} | {p['bytes']/2**30:.3f} | {p['read_seconds']:.3f} | {int(peak[1])/2**20:.3f} |")
lines += ['','Process peaks include loading, warmups, compilation and all completed modes.',
          'All reference/profile/census timed regions report zero compilation (asserted during table generation).',
          'Warmups and complete process timings are retained in each case directory.','',
          '## Exclusive census seconds','',
          'Columns partition the complete census timer, including setup and observer.',
          'Buckets classify exclusive function bodies, not chronological phases. Basis work includes entry and ordinary solves/refactors; projection_other excludes nested basis work. Weight_updates excludes lazy weight construction inside selection and its nested solves.',
          'Unwrapped work and timer bookkeeping remain in the containing bucket.',
          'The numerical bucket is not the total cost of safeguards: unwrapped checks can remain in iteration/reconstruction buckets.','',
          '| Category | '+ ' | '.join(x['case'] for x in records)+' |',
          '|---|'+'---:|'*len(records)]
keys=sorted(set().union(*(r['exclusive_groups'] for r in records)))
for key in keys:
 lines.append('| '+key+' | '+' | '.join(f"{r['exclusive_groups'].get(key,0):.3f}" for r in records)+' |')
lines.append('| Total | '+' | '.join(f"{sum(r['exclusive_groups'].values()):.3f}" for r in records)+' |')
for r in records:
 case=r['case'];folder=root/'results'/case;p=tomllib.loads((folder/'plain.toml').read_text());c=tomllib.loads((folder/'census.toml').read_text())
 lines += ['',f'## {case}','',f"Reference allocation events: {p['allocations']:,}; census: {c['allocations']:,}.",
           'Phases: '+', '.join(f"{e['event']} at {e['iteration']} (+{e['offset']})" for e in p['phases'])+'.','',
           '| Function | Calls | Exclusive s | Inclusive s (overlapping) | Exclusive GC s | Exclusive allocated MiB |',
           '|---|---:|---:|---:|---:|---:|']
 for f in r['top_functions'][:18]:
  lines.append(f"| `{f['function']}` | {f['calls']:,} | {f['exclusive_seconds']:.3f} | {f['inclusive_seconds']:.3f} | {f['exclusive_gc_seconds']:.3f} | {f['exclusive_bytes']/2**20:.3f} |")
 if len(p['windows'])>1:
  window_ms=[w['seconds']/128*1000 for w in p['windows'][1:]]
  lines += ['',f"After excluding the first window (which includes setup), the {len(window_ms)} full 128-step windows have median {statistics.median(window_ms):.3f} ms/step, range {min(window_ms):.3f}–{max(window_ms):.3f} ms/step. These are windows of one trajectory, not independent repetitions."]
(root/'RESULTS.md').write_text('\n'.join(lines)+'\n')
