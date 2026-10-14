from control import *
def median(xs):return statistics.median(xs)
def load(i,kind,id):return tomllib.loads((D/f'run-{i}'/f'{kind}-{id}.toml').read_text())
def stats(v,side=None):
 w=[x for x in v['windows'] if x['measured'] and (side is None or x['side']==side)]
 return {k:median([x[k] for x in w]) for k in ('seconds','bytes','events')}|dict(min_seconds=min(x['seconds'] for x in w),max_seconds=max(x['seconds'] for x in w),mad_seconds=median([abs(x['seconds']-median([z['seconds'] for z in w])) for x in w]),gc_windows=sum(x['gc_seconds']>0 for x in w))
def main():
 configs=tomllib.loads((D/'cases.toml').read_text())['cases'];ids=[f['id'] for f in configs];coreids=ids+['sparse-repeated','sparse-unique','dense-repeated','dense-unique']
 checks={f'audit_{i}':rd(D/f'audit-{i}.json')['all_passed'] is True for i in range(1,5)}
 public=[];core=[];improved=[];public_guard=True;component_guard=True
 for id in ids:
  vs=[load(i,'solve',id) for i in range(1,5)];checks['cross_process_'+id]=len({v['signature'] for v in vs})==1 and len({v['options'] for v in vs})==1
  ss=[stats(v) for v in vs];blocks=[]
  for r,c in ((0,1),(3,2)):
   ratios={k:ss[c][k]/ss[r][k] for k in ('seconds','bytes','events')};blocks.append(ratios)
   public_guard &= ratios['seconds']<=1.05
  qualifies=all(b['seconds']<=.95 and b['bytes']<1 and b['events']<1 for b in blocks)
  if qualifies:improved.append(id)
  public.append(dict(id=id,process_stats=ss,blocks=blocks,qualifies=qualifies,cold_seconds=[v['cold']['seconds'] for v in vs]))
 for id in coreids:
  runs=[]
  for i in range(1,5):
   v=load(i,'core',id);r=stats(v,'reference');c=stats(v,'candidate');w=v['windows'];pairs=[next(x['seconds'] for x in w if x['rep']==j and x['side']=='candidate')/next(x['seconds'] for x in w if x['rep']==j and x['side']=='reference') for j in range(4,11)]
   ratio=median(pairs);ok=ratio<=1.10 and c['bytes']<=1.10*r['bytes'] and c['events']<=1.10*r['events'];component_guard &=ok
   runs.append(dict(index=i,reference=r,candidate=c,paired_median_ratio=ratio,paired_min=min(pairs),paired_max=max(pairs),paired_mad=median([abs(x-ratio) for x in pairs]),no_material_regression=ok))
  core.append(dict(id=id,nonzero_values=v['nonzero_values'],distinct_values=v['distinct_values'],conversion_count_scope='matrix-wide upper bounds; not observed calls, early stop may reduce both',runs=runs))
 checks['posthost_clear']=not rd(D/'posthost.json')['matches']
 inv=[rd(D/f'invocation-{i}.json') for i in range(1,5)];checks['inclusive_budget']=sum(x['elapsed_seconds'] for x in inv)<=360
 result=dict(correctness_accepted=all(checks.values()),performance_screen_accepted=all(checks.values()) and len(improved)>=2 and public_guard and component_guard,checks=checks,improved=improved,public_no_regression=public_guard,component_no_regression=component_guard,public=public,core=core,inclusive_seconds=sum(x['elapsed_seconds'] for x in inv),load_seconds=[tomllib.loads((D/f'run-{i}/raw.toml').read_text())['load_seconds'] for i in range(1,5)],limitations='Exploratory two ABBA blocks, small fixtures; no universal/end-to-end large-LP or native-retention claim; no production promotion.',sha256={str(p):sha(p) for p in D.glob('audit-*.json')})
 save(D/'analysis.json',result)
 print(json.dumps({k:result[k] for k in ('correctness_accepted','performance_screen_accepted','improved','public_no_regression','component_no_regression','inclusive_seconds')},indent=2))
if __name__=='__main__':main()
