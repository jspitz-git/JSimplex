from pathlib import Path
import json,tomllib,statistics,hashlib,sys
D=Path(__file__).resolve().parent
raw=D/'results-1.toml';run=D/'comparison-2'
data=tomllib.loads(raw.read_text());proc=json.loads((run/'guard/process.json').read_text());sup=json.loads((run/'supervisor.json').read_text());post=json.loads((run/'postflight.json').read_text())
checks={}
checks['process_exit0']=proc['reason']=='exit0' and proc['returncode']==0
checks['guard_pins']=proc['pins_unchanged']
checks['supervisor']=sup['accepted']
checks['postflight']=not post['conflicts']
checks['cells24']=len(data['cold'])==24 and all(c['ok'] and c['completed_updates']==256 for c in data['cold'])
checks['windows144']=len(data['windows'])==144
checks['compile_zero']=all(w['compile_seconds']==w['recompile_seconds']==0 for w in data['windows'] if not w['warm'])
checks['work_perwindow']=all(w['updates']==256 and w['refactors']==1 for w in data['windows'])
checks['sourcepins']=all(Path(p).resolve()==Path(v['resolved']) and hashlib.sha256(Path(p).read_bytes()).hexdigest()==v['sha256'] for p,v in json.loads((D/'pins-2.json').read_text())['inventory'].items())
summ=[]
for fixture in ['band','blocks','sparse','dense']:
 for backend in ['native','markowitz']:
  group=[c for c in data['cold'] if (c['fixture'],c['backend'])==(fixture,backend)]
  checks[f'initial_{fixture}_{backend}']=len(group)==3 and len(set(c['initial_factor_hash'] for c in group))==1
  for c in group:
   key=(fixture,backend,c['manager']);tr=c['trace'];ups=[x for x in tr if x['event']=='update'];ws=[w for w in data['windows'] if (w['fixture'],w['backend'],w['manager'])==key and not w['warm']];ft=[w for w in data['windows'] if (w['fixture'],w['backend'],w['manager'])==(fixture,backend,'FT') and not w['warm']]
   checks['_'.join(key)]=len(tr)==258 and [x['step'] for x in ups]==list(range(1,257)) and len(ws)==5 and sorted(w['repetition'] for w in ws)==list(range(1,6))
   if not ws:continue
   before=next(x for x in ups if x['step']==128);after=next(x for x in tr if x['event']=='refactor');end=ups[-1]
   med=lambda name:statistics.median(w[name] for w in ws)
   ratios=[w['seconds']/next(z['seconds'] for z in ft if z['repetition']==w['repetition']) for w in ws]
   row=dict(fixture=fixture,backend=backend,manager=c['manager'],seconds_median=med('seconds'),seconds_min=min(w['seconds'] for w in ws),seconds_max=max(w['seconds'] for w in ws),paired_to_FT_median=statistics.median(ratios),paired_to_FT_min=min(ratios),paired_to_FT_max=max(ratios),bytes_median=med('bytes'),bytes_min=min(w['bytes']for w in ws),bytes_max=max(w['bytes']for w in ws),events_median=med('events'),gc_seconds_total=sum(w['gc_seconds']for w in ws),retained_bytes_median=med('retained_bytes'),u_initial=tr[0]['u_nonzero'],u_before_refactor=before['u_nonzero'],u_after_refactor=after['u_nonzero'],u_final=end['u_nonzero'],u_max=max(x['u_nonzero']for x in ups),max_storage_ratio=max(x['storage_ratio_since_refactor']for x in tr),history_coefficients_final=end['history_stored_coefficients'],history_records_final=end['history_records'],max_graph_bytes=max(x.get('reachable_bytes',0)for x in tr),basis_nnz_initial=tr[0]['basis_nonzeros'],basis_nnz_final=end['basis_nonzeros'],u_growth_max=max(x['u_max']for x in tr))
   for field in ['construct_seconds','ftran_seconds','btran_seconds','update_seconds','refactor_seconds']:row[field+'_median']=med(field)
   summ.append(row)
samples=[json.loads(x)for x in (run/'guard/resources.jsonl').read_text().splitlines()]
result=dict(accepted=all(checks.values()),checks=checks,summary=summ,process=dict(elapsed=proc['elapsed_including_launch'],maxrss_kib=proc['child_maxrss_kib'],min_available_kib=min(s['available_kib']for s in samples),max_swap_kib=max(s['swap_used_kib']for s in samples)),raw_sha256=hashlib.sha256(raw.read_bytes()).hexdigest())
with(D/'analysis-1.json').open('x')as f:json.dump(result,f,indent=2);f.write('\n')
print('ACCEPTED',result['accepted'],'checks',len(checks));print('fixture backend manager median_ms alloc_KiB events retained_KiB U0/U128/Ufresh/U256/max history ratio_toFT max_storage_ratio')
for s in summ:print(s['fixture'],s['backend'],s['manager'],round(s['seconds_median']*1000,3),round(s['bytes_median']/1024,1),s['events_median'],round(s['retained_bytes_median']/1024,1),'/'.join(str(s[k])for k in ['u_initial','u_before_refactor','u_after_refactor','u_final','u_max']),s['history_coefficients_final'],round(s['paired_to_FT_median'],3),round(s['max_storage_ratio'],2))
if not result['accepted']:print('FALSE',[k for k,v in checks.items()if not v]);sys.exit(1)
