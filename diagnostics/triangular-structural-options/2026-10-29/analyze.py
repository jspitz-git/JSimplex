from pathlib import Path
import json,tomllib,hashlib,statistics,csv,re
D=Path(__file__).resolve().parent
raw=tomllib.loads((D/'results-1.toml').read_text());run=D/'options-1'
proc=json.loads((run/'guard/process.json').read_text());sup=json.loads((run/'supervisor.json').read_text());post=json.loads((run/'postflight.json').read_text());pins=json.loads((D/'pins.json').read_text())
checks={'exit0':proc['reason']=='exit0'and proc['returncode']==0,'supervisor':sup['accepted'],'pins_guard':proc['pins_unchanged'],'90pins':len(pins['inventory'])==90 and all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==v['sha256']for p,v in pins['inventory'].items()),'postflight':not post['conflicts'],'96cold':len(raw['cold'])==96 and all(c['ok']and c['updates']==256 for c in raw['cold']),'576windows':len(raw['windows'])==576,'480measured':sum(not w['warm']for w in raw['windows'])==480,'compile_zero':all(w['compile_seconds']==w['recompile_seconds']==0 for w in raw['windows']if not w['warm'])}
summary=[]
for manager in ['SS','FT','BG']:
 for fixture in ['band','blocks','sparse','dense']:
  for backend in ['native','markowitz']:
   g=[c for c in raw['cold']if(c['manager'],c['fixture'],c['backend'])==(manager,fixture,backend)]
   checks[f'initial_{manager}_{fixture}_{backend}']=len(g)==4 and len(set(c['initial_factor_hash']for c in g))==1
   baseline=[w for w in raw['windows']if(w['manager'],w['fixture'],w['backend'],w['interval'])==(manager,fixture,backend,128)and not w['warm']]
   for c in g:
    key=(manager,fixture,backend,c['interval']);ups=[r for r in c['trace']if r['event']=='update'];refs=[r for r in c['trace']if r['event']=='refactor'];ws=[w for w in raw['windows']if(w['manager'],w['fixture'],w['backend'],w['interval'])==key and not w['warm']]
    checks['_'.join(map(str,key))]=len(ups)==256 and [r['step']for r in ups]==list(range(1,257))and len(refs)==256//c['interval']-1 and c['refactors']==len(refs)and len(ws)==5 and sorted(w['repetition']for w in ws)==list(range(1,6))and all(w['updates']==256 and w['refactors']==len(refs)for w in ws)
    supported=[r for r in ups if r['permutation_probe']['supported']];possible=[r for r in supported if r['permutation_probe']['possible']];new=[r for r in ups if r['pure_permutation_with_actual_elimination']]
    checks['topological_'+'_'.join(map(str,key))]=all(r['permutation_probe']['topological_agreement']for r in supported)
    ps=[r['permutation_probe']for r in ups];compiled_free=[p for p in ps if p['compile_seconds']==p['recompile_seconds']==0]
    med=lambda field:statistics.median(w[field]for w in ws)
    paired=[w['seconds']/next(b['seconds']for b in baseline if b['repetition']==w['repetition'])for w in ws]
    row=dict(manager=manager,fixture=fixture,backend=backend,interval=c['interval'],seconds_median=med('seconds'),seconds_min=min(w['seconds']for w in ws),seconds_max=max(w['seconds']for w in ws),paired_to128_median=statistics.median(paired),paired_to128_min=min(paired),paired_to128_max=max(paired),bytes_median=med('bytes'),events_median=med('events'),retained_bytes_median=med('retained_bytes'),gc_seconds_total=sum(w['gc_seconds']for w in ws),refactors=len(refs),u_peak=max(r['u_nonzero']for r in ups),storage_ratio_peak=max(r['storage_ratio_since_refactor']for r in ups),history_nonzero_peak=max(r['history_nonzero_coefficients']for r in ups),graph_peak=max(r.get('reachable_bytes',0)for r in c['trace']),probe_supported=len(supported),probe_possible=len(possible),possible_actual_elimination=len(new),possible_nonzero_multipliers=sum(r['new_nonzero_multipliers']for r in new),probe_entries_scanned=sum(p.get('graph_entries_scanned',0)for p in ps),reach_edges=sum(p.get('reach_edges_visited',0)for p in ps),probe_uncompiled_seconds_median=statistics.median(p['seconds']for p in compiled_free),probe_bytes_median=statistics.median(p['bytes']for p in ps),rotation_span_median=statistics.median(r['spike_last']-r['leaving_position']for r in ups),pre_union_columns_median=statistics.median(p.get('pre_rotation_row_union_columns',0)for p in ps),suffix_columns_median=statistics.median(p.get('suffix_columns',0)for p in ps))
    for field in ['construct_seconds','ftran_seconds','btran_seconds','update_seconds','refactor_seconds','assembly_seconds']:row[field+'_median']=med(field)
    summary.append(row)
for fixture in ['band','blocks','sparse','dense']:
 for backend in ['native','markowitz']:
  cs=[c for c in raw['cold']if(c['fixture'],c['backend'])==(fixture,backend)]
  checks[f'all_manager_initial_{fixture}_{backend}']=len(cs)==12 and len(set(c['initial_factor_hash']for c in cs))==1
checks['624coldrefactors']=sum(c['refactors']for c in raw['cold'])==624
checks['3120measuredrefactors']=sum(w['refactors']for w in raw['windows']if not w['warm'])==3120
samples=[json.loads(line)for line in(run/'guard/resources.jsonl').read_text().splitlines()]
result={'accepted':all(checks.values()),'checks':checks,'summary':summary,'process':{'elapsed':proc['elapsed_including_launch'],'maxrss_kib':proc['child_maxrss_kib'],'min_available_kib':min(s['available_kib']for s in samples),'swap_max':max(s['swap_used_kib']for s in samples)},'raw_sha256':hashlib.sha256((D/'results-1.toml').read_bytes()).hexdigest(),'test_summary_log':(run/'guard/run.log').read_text().splitlines()[-6:]}
with(D/'analysis-1.json').open('x')as f:json.dump(result,f,indent=2);f.write('\n')
with(D/'summary.csv').open('x',newline='')as f:w=csv.DictWriter(f,fieldnames=list(summary[0]),lineterminator='\n');w.writeheader();w.writerows(summary)
print('ACCEPTED',result['accepted'],'checks',len(checks),'process',result['process'])
for m in ['SS','FT','BG']:
 print(m,'fixture backend bestinterval whole_ms ratio bytes128KiB->bestKiB possible128 novel128')
 for fixture in ['band','blocks','sparse','dense']:
  for backend in ['native','markowitz']:
   g=[r for r in summary if(r['manager'],r['fixture'],r['backend'])==(m,fixture,backend)];best=min(g,key=lambda r:r['seconds_median']);b=next(r for r in g if r['interval']==128)
   print(fixture,backend,best['interval'],round(best['seconds_median']*1000,3),round(best['paired_to128_median'],3),round(b['bytes_median']/1024,1),round(best['bytes_median']/1024,1),b['probe_possible'],b['possible_actual_elimination'])
if not result['accepted']:print('FALSE',[k for k,v in checks.items()if not v]);raise SystemExit(1)
