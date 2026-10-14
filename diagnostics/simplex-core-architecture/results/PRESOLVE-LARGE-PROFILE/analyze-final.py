"""Post-exit analysis only; never starts Julia or replays a frozen auditor."""
from control import *
import tomllib
NAMES=['basic','singleton_rows','singleton_equalities','sparse_equalities','parallel_rows','dependent_rows','doubleton','propagation','dual_fixings']
models={}
for i,name in enumerate(('runtime','medium','test'),1):
 out=D/f'run-{i}';req(out.exists(),'missing model process')
 raw=tomllib.loads((out/'raw.toml').read_text()) if (out/'raw.toml').exists() else None
 events=[tomllib.loads(p.read_text()) for p in out.glob('finish-*.toml')];events.sort(key=lambda e:(e['rep'],e['serial']))
 profiles=[tomllib.loads(p.read_text()) for p in sorted(out.glob('profile-*.toml'))]
 byrep={}
 for rep in range(1,4):
  es=[e for e in events if e['rep']==rep]
  if not es:continue
  total=sum(e['seconds'] for e in es);passes=[]
  for index,label in enumerate(NAMES,1):
   selected=[e for e in es if e['index']==index]
   if not selected:continue
   stats={k:sum(e[k] for e in selected) for k in ('seconds','bytes','events','gc_seconds','compile_seconds','recompile_seconds')}
   passes.append(dict(index=index,name=label,calls=len(selected),changed=sum(e.get('changed',False) for e in selected),share=stats['seconds']/total if total else 0,**stats))
  byrep[str(rep)]=dict(complete=any(p['rep']==rep for p in profiles),all_compile_zero=all(e['compile_seconds']==e['recompile_seconds']==0 for e in es),dispatch_seconds=total,passes=sorted(passes,key=lambda p:p['seconds'],reverse=True))
 cold_trace=[(e['round'],e['index'],e['input_dimensions'],e.get('output_dimensions'),e.get('changed'),e['failure']) for e in events if e['rep']==1]
 cold_complete=any(p['rep']==1 for p in profiles)
 for key,v in byrep.items():
  observed=[(e['round'],e['index'],e['input_dimensions'],e.get('output_dimensions'),e.get('changed'),e['failure']) for e in events if e['rep']==int(key)]
  v['matches_completed_cold_dispatch_trace']=cold_complete and observed==cold_trace
 warm=[v for k,v in byrep.items() if int(k)>1 and v['all_compile_zero'] and (v['complete'] or v['matches_completed_cold_dispatch_trace'])]
 # A full saved dispatch trace can support descriptive timing even when the
 # subsequent digest was interrupted. It DOES NOT establish output/input equality.
 warm_result_verified=all(v['complete'] for v in warm) if warm else False
 summary=[]
 if warm:
  for index,label in enumerate(NAMES,1):
   ss=[next((p for p in v['passes'] if p['index']==index),None) for v in warm]
   if any(s is None for s in ss):continue
   summary.append(dict(name=label,index=index,samples=len(ss),median_seconds=statistics.median(s['seconds'] for s in ss),min_seconds=min(s['seconds'] for s in ss),max_seconds=max(s['seconds'] for s in ss),median_bytes=statistics.median(s['bytes'] for s in ss),median_events=statistics.median(s['events'] for s in ss),calls=[s['calls'] for s in ss],changes=[s['changed'] for s in ss],gc_seconds=[s['gc_seconds'] for s in ss]))
  summary.sort(key=lambda s:s['median_seconds'],reverse=True)
  total=sum(s['median_seconds'] for s in summary)
  for s in summary:s['share_of_medians']=s['median_seconds']/total
 models[name]=dict(raw=raw,profiles=profiles,by_rep=byrep,warm_summary=summary,warm_result_verified=warm_result_verified,process=rd(out/'process.json'),invocation=rd(D/f'invocation-{i}.json'))
print(json.dumps({name:dict(input=v['raw'].get('input_dimensions') if v['raw'] else None,profiles=len(v['profiles']),warm_result_verified=v['warm_result_verified'],ranking=v['warm_summary']) for name,v in models.items()},indent=2))
save(D/'analysis.json',dict(models=models,scope='Descriptive observed dispatch attribution; no candidate/no speedup/no native allocation-free or observer neutrality claim.',sha256={str(p):sha(p) for i in range(1,4) for p in (D/f'run-{i}').iterdir() if p.is_file()}))
