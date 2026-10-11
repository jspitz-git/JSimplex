from pathlib import Path
import json,sys,tomllib,statistics,collections
r=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl');attempt=sys.argv[1];raw=r/'.superpowers/simplex-core-architecture/S2-A'/attempt
process=json.loads((raw/'process.json').read_text());assert process['returncode']==0 and process['pins_unchanged']
d=tomllib.loads((raw/'cost.toml').read_text());assert len(d['samples'])==128 and len(d['warmups'])==64
sets=collections.defaultdict(list)
for row in d['samples']:sets[(row['type'],row['matrix'],row['history'],row['reject_all'])].append(row)
summary=[]
for key,rows in sets.items():
 assert len(rows)==8
 plain={v:[x for x in rows if x['variant']==v and not x['counted']] for v in ('control','candidate')}
 counted={v:next(x for x in rows if x['variant']==v and x['counted']) for v in ('control','candidate')}
 for v,p in plain.items():
  assert len(p)==3 and sorted(x['pair'] for x in p)==[1,2,3]
  assert all(x['optimizer']['compile_seconds']==0 for x in p)
 assert len({(x['primal_hash'],x['objective']) for x in rows})==1
 b,c=(statistics.median(x['optimizer']['seconds'] for x in plain[v]) for v in ('control','candidate'))
 summary.append({'type':key[0],'matrix':key[1],'history':key[2],'reject_all':key[3],
 'ratio_of_medians':c/b,'control_seconds':b,'candidate_seconds':c,
 'paired_ratios':[next(x for x in plain['candidate'] if x['pair']==i)['optimizer']['seconds']/next(x for x in plain['control'] if x['pair']==i)['optimizer']['seconds'] for i in (1,2,3)],
 'bytes':{v:[x['optimizer']['bytes'] for x in p] for v,p in plain.items()},
 'allocations':{v:[x['optimizer']['allocations'] for x in p] for v,p in plain.items()},
 'work':{v:{k:x[k] for k in ('kernel_calls','audits','skips','fallbacks','direct_recomputations','candidate_copies','endpoint_refreshes','point_buffer_before_bytes','point_buffer_retained_bytes')} for v,x in counted.items()}})
print(json.dumps({'attempt':attempt,'groups':summary},indent=2))
