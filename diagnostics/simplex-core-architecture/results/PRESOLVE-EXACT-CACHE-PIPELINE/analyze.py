from control import *
def main():
 ids=[f['id'] for f in tomllib.loads((D/'cases.toml').read_text())['cases']]+['sparse-repeated','sparse-unique','dense-repeated','dense-unique']
 checks={f'audit_{i}':rd(D/f'audit-{i}.json')['all_passed'] is True for i in range(1,5)};cases=[];improved=[];no_allocations=True;no_slowdown=True
 for id in ids:
  vs=[tomllib.loads((D/f'run-{i}/presolve-{id}.toml').read_text()) for i in range(1,5)]
  checks['exact_crossprocess_'+id]=len({v['signature'] for v in vs})==1
  ss=[]
  for v in vs:
   w=[x for x in v['windows'] if x['measured']];med=statistics.median([x['seconds'] for x in w])
   ss.append({k:statistics.median([x[k] for x in w]) for k in ('seconds','bytes','events')}|dict(min_seconds=min(x['seconds'] for x in w),max_seconds=max(x['seconds'] for x in w),mad_seconds=statistics.median([abs(x['seconds']-med) for x in w]),gc_windows=sum(x['gc_seconds']>0 for x in w)))
  blocks=[{k:ss[c][k]/ss[r][k] for k in ('seconds','bytes','events')} for r,c in ((0,1),(3,2))]
  alloc=all(b['bytes']<=1 and b['events']<=1 for b in blocks);timeguard=all(b['seconds']<=1.05 for b in blocks);qualifies=alloc and all(b['seconds']<=.95 for b in blocks)
  no_allocations &=alloc;no_slowdown &=timeguard
  if qualifies:improved.append(id)
  cases.append(dict(id=id,process_stats=ss,blocks=blocks,allocations_nonincreasing=alloc,time_no_material_regression=timeguard,qualifies=qualifies,cold_seconds=[v['cold']['seconds'] for v in vs],gc_warmup_seconds=[v['gc_warmup'][0]['seconds'] for v in vs]))
 inv=[rd(D/f'invocation-{i}.json') for i in range(1,5)];elapsed=sum(x['elapsed_seconds'] for x in inv)
 checks['budget']=elapsed<=280;checks['no_julia']=not rd(D/'posthost.json')['matches']
 accepted=all(checks.values()) and no_allocations and no_slowdown and len([i for i in improved if i in ids[:4]])>=2
 result=dict(correctness_accepted=all(checks.values()),performance_screen_accepted=accepted,checks=checks,cases=cases,improved=improved,all_cases_no_allocation_increase=no_allocations,all_cases_no_material_slowdown=no_slowdown,inclusive_seconds=elapsed,load_seconds=[tomllib.loads((D/f'run-{i}/raw.toml').read_text())['load_seconds'] for i in range(1,5)],scope='Whole presolve_problem, unchanged cache candidate; user-updated criterion. Four processes/two ABBA blocks, small fixtures, no universal speedup/GC/native-retention proof.',sha256={str(p):sha(p) for p in D.glob('audit-*.json')})
 save(D/'analysis.json',result);print(json.dumps({k:result[k] for k in ('correctness_accepted','performance_screen_accepted','improved','all_cases_no_allocation_increase','all_cases_no_material_slowdown','inclusive_seconds')},indent=2))
if __name__=='__main__':main()
