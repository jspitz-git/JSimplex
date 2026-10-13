"""Independent aggregation of preserved raw metrics; no numerical rerun."""
from pathlib import Path
import json,tomllib,statistics as s,hashlib
D=Path(__file__).resolve().parent;O=D/'attempt-2';post=json.loads((D/'postprocess.json').read_text());raw={p.parent.name:tomllib.loads(p.read_text()) for p in O.glob('*/raw.toml')};out=[]
for m in post['measurements']:
 i=next(i for i,r in enumerate(raw['pair04-reference']['records']) if (r['name'],r['scalar'])==(m['name'],m['scalar']))
 r=dict(name=m['name'],scalar=m['scalar'],median_ratio=m['median_ratio'],minimum_ratio=m['min_ratio'],maximum_ratio=m['max_ratio'],MAD=m['MAD'],faster_pairs=m['faster_pairs'],target_gate=m['target_gate'],control_gate=m['control_gate'])
 for side in ['reference','candidate']:
  rr=[raw[f'pair{p:02d}-{side}']['records'][i] for p in range(4,11)];r[side]={}
  for key in ['construction','first_full','steady_full','first_upper','steady_upper','scratch']:
   if key not in rr[0]:continue
   div=4 if key.startswith('steady') else 1
   r[side][key]={field:s.median(x[key][field]/div for x in rr) for field in rr[0][key]}
  r[side]['backend_graph_bytes']=[x['backend_graph_bytes'] for x in rr]
  if 'scratch_graph_bytes' in rr[0]:r[side]['scratch_graph_bytes']=[x['scratch_graph_bytes'] for x in rr]
 out.append(r)
metrics=[r[k] for name,a in raw.items() if name.startswith('pair') for r in a['records'] for k in ['steady_full','steady_upper']]
result=dict(cases=out,steady_windows=len(metrics),nonzero_steady_compile=sum(m['compile_seconds']!=0 or m['recompile_seconds']!=0 for m in metrics),nonzero_steady_GC=sum(m['gc_seconds']!=0 for m in metrics),qualification_assertions=raw['qualification']['counts'],qualification_rows=sum(len(r['trace']) for r in raw['qualification']['records']),red_counts=raw['red']['counts'],target_cases=sum(m['target_gate'] is not None for m in out),target_pass=sum(m['target_gate'] is True for m in out),control_cases=sum(m['control_gate'] is not None for m in out),control_fail=[dict(name=m['name'],scalar=m['scalar']) for m in out if m['control_gate'] is False],normalization='Steady windows contain four calls; side seconds/bytes/events divided by4. Paired ratios calculated before medians, not ratio of side medians. First/cold windows unnormalized; seven measured pairs only. Warm raw retained.',raw_sha256={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in O.glob('*/raw.toml')})
with (D/'summary.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
print('windows',result['steady_windows'],'compile',result['nonzero_steady_compile'],'GC',result['nonzero_steady_GC'],'rows',result['qualification_rows'],'targets',result['target_pass'],'of',result['target_cases'],'controlfail',len(result['control_fail']),'of',result['control_cases'])
for r in out:
 if r['control_gate'] is False:print(r['name'],r['scalar'],'us',r['reference']['steady_full']['seconds']*1e6,r['candidate']['steady_full']['seconds']*1e6,'MAD',r['MAD'])
