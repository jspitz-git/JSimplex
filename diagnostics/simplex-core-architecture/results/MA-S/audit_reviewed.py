"""MA-S fail-closed auditor; import performs no process or numerical work."""
from pathlib import Path
import hashlib,json,tomllib,math,statistics,sys
D=Path(__file__).resolve().parent;R=D.parents[3]
def read(p):return json.loads(Path(p).read_text())
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def require(ok,msg):
 if not ok:raise ValueError(msg)
def finite(x):return type(x) in (int,float) and math.isfinite(x) and x>=0
def spec():return tomllib.loads((D.parent/'MA-R/fixtures.toml').read_text())
def expected_correctness():
 s=spec();rows=[]
 for bits in s['bits']:
  for n in s['sizes']:
   for layout in s['layouts']:
    for dr in s['directions']:rows.append((f'grid/{bits}/{n}/{layout}/{dr}',dr,n>=16,1,n,None))
 for kind in s['specials']:
  for dr in s['directions']:
   exc='SingularException' if kind.startswith('pivot_zero_') else 'BoundsError' if kind=='invalid_ipiv' else 'DimensionMismatch' if kind=='dest_long' else None
   rows.append((f'special/{kind}/{dr}',dr,kind not in ('rhs_short','dest_long','rhs_view'),2 if kind=='retained_outputs' else 1,17 if kind=='dest_long' else 16,exc))
 for stored,ambient in s['mixed_stored_ambient']:
  for dr in s['directions']:rows.append((f'mixed/{stored}/{ambient}/{dr}',dr,True,1,16,None))
 for mode in s['matching_rounding']:
  for dr in s['directions']:rows.append((f'rounding/{mode}/{dr}',dr,True,1,16,None))
 for mode in s['scoped_mismatch']:
  for dr in s['directions']:rows.append((f'scoped/{mode}/{dr}',dr,False,1,16,None))
 for scalar in ('Float64','Rational{BigInt}'):
  for dr in s['directions']:rows.append((f'scalar/{scalar}/{dr}',dr,False,1,32,None))
 return rows

def validate_raw(raw,index):
 checks={}
 try:
  require(type(index)==int and index in (1,2,3),'index')
  checks['header']=type(raw.get('index'))==int and raw['index']==index and raw.get('errors')==[] and raw.get('ambient_restored') is True and finite(raw.get('load_seconds')) and finite(raw.get('candidate_definition_seconds'))
  checks['loaded_paths_schema']=isinstance(raw.get('loaded_paths'),dict) and bool(raw['loaded_paths']) and all(isinstance(v,str) and Path(v).is_absolute() for v in raw['loaded_paths'].values())
  cs=raw['correctness'];cnt=raw['counts'];red=raw['red']
  if index==1:
   checks['exact_RED']=(all(type(red.get(k))==int and red[k]==v for k,v in {'pass':0,'fail':2,'error':0,'broken':0}.items()) and red.get('missing_route_only') is True and red.get('failure_expressions')==['isdefined(P, :_dense_ma_eligible)','isdefined(P, :candidate_forward!) && isdefined(P, :candidate_transpose!)'])
   checks['test_counts']=set(cnt)=={'smoke','qualification'} and all(set(v)=={'pass','fail','error','broken'} and type(v['pass'])==int and v['pass']>0 and all(type(v[k])==int and v[k]==0 for k in ('fail','error','broken')) for v in cnt.values())
   expected=expected_correctness();checks['160_cases_162_calls']=len(cs)==160 and len(expected)==160 and sum(c['calls_per_side'] for c in cs)==162
   for c,(id,dr,eligible,calls,n,exc) in zip(cs,expected):
    require(c['id']==id and c['direction']==dr and c['eligible'] is eligible and type(c['calls_per_side'])==int and c['calls_per_side']==calls,'correctness descriptor')
    require(isinstance(c['output'],list) and len(c['output'])==n and all(isinstance(x,str) and x for x in c['output']),'correctness tokens')
    require(c['exception']==[] if exc is None else len(c['exception'])==2 and c['exception'][0] in (exc,'LinearAlgebra.'+exc) and isinstance(c['exception'][1],str),'exception oracle')
  else:checks['no_extra_correctness']=cs==[] and cnt=={} and red=={}
  cases=spec()['cost_cases'];costs=raw['costs']
  checks['exact52cost_cases']=len(costs)==52 and [c['id'] for c in costs]==[c['id'] for c in cases]
  checks['windows']=True;checks['compile_zero']=True;checks['outputs_preserved']=True
  for ci,(c,fixture) in enumerate(zip(costs,cases),1):
   require(c['eligible'] is fixture['eligible'],'cost eligibility')
   require(isinstance(c['expected'],list) and len(c['expected'])==fixture['n'] and all(isinstance(v,str) and v for v in c['expected']),'cost tokens')
   ws=c['windows'];require(len(ws)==20,'window count')
   for pos,w in enumerate(ws):
    pair=pos//2+1;order=pos%2+1;firstref=(index+ci+pair)%2==0
    side=('reference' if firstref else 'candidate') if order==1 else ('candidate' if firstref else 'reference')
    require(type(w['pair'])==int and type(w['order'])==int and w['pair']==pair and w['order']==order and w['side']==side and w['phase']==('warm' if pair<=3 else 'measured') and type(w['calls'])==int and w['calls']==4,'window order/calls')
    require(all(finite(w[k]) for k in ('seconds','bytes','events','gc_seconds','compile_seconds','recompile_seconds')) and w['seconds']>0 and type(w['bytes'])==int and type(w['events'])==int,'window metrics')
    checks['outputs_preserved'] &= w['output']==c['expected'] and w['preserved'] is True
    if pair>3:checks['compile_zero'] &= w['compile_seconds']==0 and w['recompile_seconds']==0
 except Exception as e:checks['schema_complete']=False;checks['schema_error']=repr(e)
 return checks

def passed(checks):return bool(checks) and all(v is True for v in checks.values())
def stage_scalars(proc,inv,res,samples,post,context,sequence):
 checks={}
 try:
  integer=lambda x:type(x)==int and x>=0
  positive=lambda x:type(x)==int and x>0
  checks['exit_codes']=all(type(x)==int and x==0 for x in (proc['returncode'],inv['returncode']))
  checks['elapsed_schema']=all(finite(x) for x in (proc['started'],proc['ended'],proc['elapsed_including_launch'],inv['elapsed_seconds'],inv['cumulative_seconds'],post['time'])) and proc['ended']>=proc['started'] and proc['elapsed_including_launch']<=114 and proc['elapsed_including_launch']<=inv['elapsed_seconds']<=120 and inv['elapsed_seconds']<=inv['cumulative_seconds']<=360
  checks['limit_schema']=type(res['seconds'])==int and res['seconds']==120 and type(context['maximum_processes'])==int and context['maximum_processes']==3 and type(context['maximum_seconds_per_process'])==int and context['maximum_seconds_per_process']==120 and type(sequence['maximum_processes'])==int and sequence['maximum_processes']==3 and type(sequence['total_cap_seconds'])==int and sequence['total_cap_seconds']==360 and sequence['no_retry'] is True
  boot=context['boot_id'];require(isinstance(boot,str) and bool(boot),'context boot')
  checks['identity_schema']=True
  for who in ('runner','child'):
   v=proc[who]
   checks['identity_schema'] &= all(positive(v[k]) for k in ('pid','pgid','sid')) and integer(v['start_ticks']) and v['boot_id']==boot and isinstance(v['command'],str) and bool(v['command']) and v['pid']==v['pgid']==v['sid']
  groups=post['groups']
  checks['post_identity_schema']=isinstance(groups,list) and len(groups)>=158 and all(positive(v) for v in groups) and len(set(groups))==len(groups) and post['boot_id']==boot and post['matches']==[] and post['refs']==context['refs'] and all(proc[who][k] in groups for who in ('runner','child') for k in ('pgid','sid'))
  checks['memory_schema']=len(samples)>=2 and all(integer(s['available_kib']) and integer(s['swap_used_kib']) and s['available_kib']>=6*1024**2 and s['swap_used_kib']<=1024**2 for s in samples)
 except Exception as e:checks['stage_scalar_complete']=False;checks['stage_scalar_error']=repr(e)
 return checks

def stage(index):
 out=D/f'run-{index}';checks={};error=None
 try:
  inv=read(D/f'invocation-{index}.json');res=read(D/f'reservation-{index}.json');proc=read(out/'process.json');pins=read(D/'pins-reviewed.json');cmd=read(D/'commands.json')[str(index)]
  checks['process']=proc['reason']=='exit0' and proc['returncode']==0 and proc['pins_unchanged'] is True and inv['returncode']==0
  checks['command']=proc['command']==cmd and proc['cwd']==str(R) and res['command']==cmd and inv['command'][-len(cmd):]==cmd
  checks['links']=inv['reservation_sha256']==sha(D/f'reservation-{index}.json') and res['pins_sha256']==sha(D/'pins-reviewed.json')==proc['pins_sha256'] and res['review_sha256']==sha(D/'numerical-review.json') and res['context_sha256']==sha(D/'launch-context.json') and res['host_sha256']==sha(D/f'prelaunch-{index}.json') and res['sequence_sha256']==sha(D/'sequence-reservation.json')
  checks['hard_cap']=finite(inv['elapsed_seconds']) and inv['elapsed_seconds']<=120 and finite(inv['cumulative_seconds']) and inv['cumulative_seconds']<=360 and finite(proc['elapsed_including_launch']) and proc['elapsed_including_launch']<=114
  checks['pins']=read(out/'pins.json')==pins and all(sha(p)==v['sha256'] and str(Path(p).resolve())==v['resolved'] for p,v in pins['inventory'].items())
  samples=[json.loads(s) for s in (out/'resources.jsonl').read_text().splitlines()]+[proc['terminal_memory']]
  checks['memory']=len(samples)>=2 and all(type(s['available_kib'])==int and type(s['swap_used_kib'])==int and s['available_kib']>=6*1024**2 and 0<=s['swap_used_kib']<=1024**2 for s in samples)
  post=read(D/f'posthost-{index}.json'); checks['posthost']=post['matches']==[] and all(proc[who][key] in post['groups'] for who in ('runner','child') for key in ('pgid','sid'))
  checks.update(stage_scalars(proc,inv,res,samples,post,read(D/'launch-context.json'),read(D/'sequence-reservation.json')))
  raw=tomllib.loads((out/'raw.toml').read_text());checks.update(validate_raw(raw,index))
  checks['loaded_paths_pinned']=all(str(Path(p).resolve()) in {v['resolved'] for v in pins['inventory'].values()} for p in raw['loaded_paths'].values())
 except Exception as e:error=repr(e);checks['complete_schema']=False
 return dict(all_passed=passed(checks),checks=checks,error=error,sha256={str(p):sha(p) for p in out.rglob('*') if p.is_file()})

def aggregate(raws):
 require(len(raws)==3 and all(passed(validate_raw(r,i)) for i,r in enumerate(raws,1)),'invalid raw sequence')
 rows=[]
 for ci,fixture in enumerate(spec()['cost_cases']):
  ratios=[];processes=[];refs=[];cands=[]
  for raw in raws:
   ws=[w for w in raw['costs'][ci]['windows'] if w['phase']=='measured'];ref=[w for w in ws if w['side']=='reference'];cand=[w for w in ws if w['side']=='candidate']
   r=[b['seconds']/a['seconds'] for a,b in zip(ref,cand)];ratios+=r;refs+=ref;cands+=cand
   rt=statistics.median(w['seconds']/4 for w in ref);ct=statistics.median(w['seconds']/4 for w in cand)
   pr=dict(ratio=statistics.median(r),reference_seconds_per_call=rt,candidate_seconds_per_call=ct,reference_bytes=statistics.median(w['bytes'] for w in ref),candidate_bytes=statistics.median(w['bytes'] for w in cand),reference_events=statistics.median(w['events'] for w in ref),candidate_events=statistics.median(w['events'] for w in cand))
   pr['pass']=(pr['ratio']<1 and pr['candidate_bytes']<pr['reference_bytes'] and pr['candidate_events']<pr['reference_events']) if fixture['eligible'] else (ct-rt<=max(.10*rt,.4e-6) and pr['candidate_bytes']<=pr['reference_bytes'] and pr['candidate_events']<=pr['reference_events'])
   processes.append(pr)
  med=statistics.median(ratios);wins=sum(r<1 for r in ratios);rt=statistics.median(w['seconds']/4 for w in refs);ct=statistics.median(w['seconds']/4 for w in cands)
  pooled=(med<=.95 and wins>=15) if fixture['eligible'] else ct-rt<=max(.05*rt,.2e-6)
  rows.append(dict(id=fixture['id'],target=fixture['eligible'],median_ratio=med,min_ratio=min(ratios),max_ratio=max(ratios),mad=statistics.median(abs(r-med) for r in ratios),faster_pairs=wins,processes=processes,accepted=all(p['pass'] for p in processes) and pooled))
 return rows

def main():
 require(sys.argv[1:]==['aggregate'],'aggregate only')
 stages=[read(D/f'audit-{i}.json') for i in (1,2,3)]
 require(all(s['all_passed'] is True and all(sha(p)==h for p,h in s['sha256'].items()) for s in stages),'stage evidence drift')
 require(all(stage(i)['all_passed'] for i in (1,2,3)),'fresh stage validation failed')
 raws=[tomllib.loads((D/f'run-{i}/raw.toml').read_text()) for i in (1,2,3)];rows=aggregate(raws)
 obj=dict(qualification_pass=True,accepted=all(r['accepted'] for r in rows),cases=rows,total_cost_calls=12480,correctness_backend_calls=488,total_windows=3120,measured_windows=2184,warm_windows=936,gc_windows=sum(w['gc_seconds']>0 for r in raws for c in r['costs'] for w in c['windows']),sha256={str(p):sha(p) for i in (1,2,3) for p in (D/f'run-{i}/raw.toml',D/f'audit-{i}.json')})
 with (D/'aggregate.json').open('x') as f:json.dump(obj,f,indent=2);f.write('\n')
 print('accepted',obj['accepted'],'passing',sum(r['accepted'] for r in rows),'of52')
if __name__=='__main__':main()
