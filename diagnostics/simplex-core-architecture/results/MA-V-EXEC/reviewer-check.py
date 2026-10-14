"""Independent read-only MA-V result checks. Never imports/runs qualification code."""
from pathlib import Path
import json,tomllib,hashlib,statistics as st,re,math,time
R=Path.cwd();V=R/'diagnostics/simplex-core-architecture/results/MA-V';E=V.with_name('MA-V-EXEC');U=V.with_name('MA-U')
def rd(p):return json.loads(Path(p).read_text())
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
checks={};details={};bound=set()
def ck(name,value):
 checks[name]=bool(value)
 if not value:print('FAILED',name)
def bind(p):bound.add(Path(p));return p
pins=rd(bind(V/'pins.json'));iv=pins['inventory'];bad=[p for p,v in iv.items() if sha(p)!=v['sha256'] or str(Path(p).resolve())!=v['resolved']]
ck('fresh4342',len(iv)==4342 and not bad);details['pin_mismatches']=bad;details['pin_checked_at']=time.time()
for n in ('numerical-review.json','admission-review.json','source-check.json','aggregate.json','audit-1.json','audit-2.json'):
 o=rd(bind(V/n));ck('bindings_'+n,all(sha(p)==s for p,s in o['sha256'].items()));bound.update(map(Path,o['sha256']))
o=rd(bind(E/'postcheck.json'));ck('postcheck_bindings',all(sha(p)==s for p,s in o['sha256'].items()));bound.update(map(Path,o['sha256']))
host=rd(bind(E/'host.json'));ck('source514',len(host['master_identity'])==514 and all(sha(R/p)==s for p,s in host['master_identity'].items()));ck('protected6',len(host['protected'])==6 and all(sha(p)==s for p,s in host['protected'].items()))
m=rd(bind(U/'source-map.json'));src=Path(m['candidate']).read_text();ck('candidate_inverse',src.startswith(m['helper']) and src.count(m['new_expression'])==1 and src[len(m['helper']):].replace(m['new_expression'],m['old_expression'])==Path(m['original']).read_text());ck('source_copies',all(sha(p['original'])==sha(p['copy'])==p['sha256'] for p in m['copy_pairs']))
raws=[tomllib.loads(bind(V/f'run-{i}/raw.toml').read_text()) for i in (1,2)];schedule=rd(bind(V/'schedule.json'));aggregate=rd(V/'aggregate.json');summary=rd(bind(E/'result-summary.json'))
mods=['RoundNearest','RoundDown','RoundUp','RoundToZero','RoundFromZero'];scopes=['nothing']+mods;c=raws[0]['correctness']
expected=[(f'grid/{b}/{g}/{s}/{k}',s=='nothing' or s==g,g if s=='nothing' else s) for b in (128,256,512) for g in mods for s in scopes for k in (0,8,64)]
ck('predicate270',len(c['predicates'])==270 and all(r==dict(id=i,reference=e,candidate=e,expected=e,effective=m) for r,(i,e,m) in zip(c['predicates'],expected)))
tr=[('entry',True,'RoundNearest'),('outer-up',False,'RoundUp'),('inner-down',False,'RoundDown'),('inner-equal',True,'RoundNearest'),('restored-down',False,'RoundDown'),('restored-up',False,'RoundUp'),('restored-absent',True,'RoundNearest'),('throw-down',False,'RoundDown'),('after-throw-up',False,'RoundUp'),('after-throw-absent',True,'RoundNearest')]
for mode in ('RoundUp','RoundDown'):
 tr.extend((f'task/{mode}/{suffix}',equal,'RoundNearest' if equal else mode) for suffix,equal in [('before',False),('after-yield',False),('equal-before',True),('equal-after',True),('restored',False)])
tr.extend((f'global-change/{g}',g=='RoundUp','RoundUp') for g in mods)
ck('transitions25',len(c['transitions'])==25 and all(r==dict(id=i,reference=e,candidate=e,expected=e,effective=m) for r,(i,e,m) in zip(c['transitions'],tr)))
ck('no_scope_unavailable',c['no_scope_available'] is False and c['no_scope_records']==[] and c['tasks_created']==3)
f=tomllib.loads(bind(U/'fixtures.toml').read_text());whole=[]
for b in (128,256,512):
 for n in (16,32):
  for lay in ('dense','zeroheavy'):
   for dr in ('forward','transpose'):
    for g in mods:
     for s in scopes:whole.append((f'grid/{b}/{n}/{lay}/{dr}/{g}/{s}',dr,s=='nothing' or s==g,1,n,None))
for s in ('nothing','RoundUp'):
 for k in f['specials']:
  for dr in ('forward','transpose'):
   ex='SingularException' if k.startswith('pivot_zero_') else 'BoundsError' if k=='invalid_ipiv' else 'DimensionMismatch' if k=='dest_long' else None
   whole.append((f'special/{s}/{k}/{dr}',dr,s=='nothing' and k not in ('rhs_short','dest_long','rhs_view'),2 if k=='retained_outputs' else 1,17 if k=='dest_long' else 16,ex))
for s in ('nothing','RoundUp'):
 for n in (0,1,2,8,15):
  for dr in ('forward','transpose'):whole.append((f'small/{s}/{n}/{dr}',dr,False,1,n,None))
for typ in ('Float64','Rational{BigInt}'):
 for dr in ('forward','transpose'):whole.append((f'scalar/{typ}/{dr}',dr,False,1,32,None))
for stored,ambient in f['mixed_stored_ambient']:
 for s in ('nothing','RoundUp'):
  for dr in ('forward','transpose'):whole.append((f'mixed/{stored}/{ambient}/{s}/{dr}',dr,s=='nothing',1,16,None))
wholeok=len(c['whole'])==len(whole)==840
for row,(i,dr,elig,calls,n,exc) in zip(c['whole'],whole):
 wholeok &= row['id']==i and row['direction']==dr and row['eligible']==elig and row['calls_per_side']==calls and len(row['output'])==n and all(isinstance(x,str) and x for x in row['output'])
 wholeok &= row['route_counts']==dict(entries=calls,scratches=calls if elig else 0,fallbacks=0 if elig else calls)
 wholeok &= row['exception']==[] if exc is None else len(row['exception'])==2 and row['exception'][0] in (exc,'LinearAlgebra.'+exc) and isinstance(row['exception'][1],str)
ck('whole840_routes_exceptions_tokens',wholeok);ck('recorded_Test_counts',c['counts']=={'pass':25861,'fail':0,'error':0,'broken':0});ck('whole_calls844',sum(r['calls_per_side'] for r in c['whole'])==844)
details['correctness_calls']={'direct':3*sum(r['calls_per_side'] for r in c['whole']),'eligible_per_arm':sum(r['calls_per_side'] for r in c['whole'] if r['eligible']),'fallback_per_arm':sum(r['calls_per_side'] for r in c['whole'] if not r['eligible'])}
allwindows=[];micros=[];groups=set(host['groups']);invs=[];code=[];cost_calls=micro_calls=0
for idx,r in enumerate(raws,1):
 out=V/f'run-{idx}';bound.update(p for p in out.iterdir() if p.is_file())
 ck(f'header{idx}',r['index']==idx and not r['errors'] and r['ambient_restored'] is True and (idx==1 or r['correctness']=={} and r['red']==[]))
 ck(f'loaded_paths{idx}',len(r['loaded_paths'])>0 and all(Path(p).is_absolute() and str(Path(p).resolve()) in {v['resolved'] for v in iv.values()} for p in r['loaded_paths'].values()))
 wsok=True;journal=[]
 for n,w in enumerate(r['timer_baseline'],1):
  journal.append(dict(kind='baseline',index=n,window=w));wsok &= w['phase']==('warm' if n<=3 else 'measured')
  if n>3:wsok &= all(w[k]==0 for k in ('bytes','events','compile_seconds','recompile_seconds'))
 wsok &= len(r['timer_baseline'])==10
 for cat in ('red','micro','costs'):
  cases=schedule[cat] if idx==1 or cat!='red' else []
  wsok &= len(r[cat])==len(cases)
  for ci,(row,sp) in enumerate(zip(r[cat],cases),1):
   wsok &= row['id']==sp['id'] and len(row['windows'])==20
   for pos,w in enumerate(row['windows']):
    pair=pos//2+1;order=pos%2+1;firstref=(idx+ci+pair)%2==0;side=('reference' if firstref else 'candidate') if order==1 else ('candidate' if firstref else 'reference')
    wsok &= w['pair']==pair and w['order']==order and w['side']==side and w['phase']==('warm' if pair<=3 else 'measured') and w['calls']==(256 if cat=='micro' else 4)
    wsok &= all(type(w[k]) in (int,float) and math.isfinite(w[k]) and w[k]>=0 for k in ('seconds','bytes','events','gc_seconds','compile_seconds','recompile_seconds')) and w['seconds']>0
    if pair>3:wsok &= w['compile_seconds']==w['recompile_seconds']==0;allwindows.append(w)
    if cat=='micro':
     micro_calls+=w['calls'];wsok &= w['checksum']==row['expected']==(256 if sp['expected'] else 0)
     if pair>3 and side=='candidate':wsok &= w['bytes']==w['events']==0
    else:
     cost_calls+=w['calls'];wsok &= row['eligible']==sp['eligible'] and len(row['expected'])==sp['n'] and w['output']==row['expected'] and w['preserved'] is True
 ck(f'windows_and_baselines{idx}',wsok)
 def wholejournal(rows):
  for row in rows:
   for w in row['windows']:
    loc=f"cost/{row['id']}/{w['pair']}/{1 if w['side']=='reference' else 2}"
    journal.extend([dict(kind='whole-metrics',location=loc,window={k:v for k,v in w.items() if k not in ('output','preserved')}),dict(kind='whole-complete',location=loc,window=w)])
 wholejournal(r['red'])
 if idx==1:
  journal.extend(dict(kind='correctness',record=v) for v in c['predicates']+c['transitions'][:20]+c['no_scope_records']+c['transitions'][20:]+c['whole'])
 for row in r['micro']:
  journal.extend(dict(kind='micro',location=f"micro/{row['id']}/{w['pair']}/{1 if w['side']=='reference' else 2}",window=w) for w in row['windows'])
 wholejournal(r['costs']);jr=tomllib.loads((out/'partial-windows.toml').read_text())['records'];jok=len(jr)==len(journal)
 for got,want in zip(jr,journal):
  if want['kind']=='correctness':
   keys=('id','direction','eligible','calls_per_side','output','route_counts') if 'direction' in want['record'] else tuple(want['record']);jok &= got['kind']=='correctness' and all(got['record'][k]==want['record'][k] for k in keys)
  else:jok &= got==want
 ck(f'journal{idx}',jok)
 for arm,cr in zip(('old','new'),r['code']):
  s=(out/f'micro-{arm}.ll').read_text();p=(out/f'probe-{arm}.ll').read_text();calls=re.findall(r'^.*\b(?:call|invoke)\b[^\n]*@j_probe_[^\n]*$',s,re.M)
  ok=len(calls)==256 and not re.search(r'\b(?:call|invoke)\b[^\n]*\b(?:jl_apply|ijl_apply|jl_invoke|ijl_invoke)\b',s) and not re.search(r'\b(?:call|invoke)\b[^@\n]*%[A-Za-z0-9_.]+\(',s)
  ck(f'code_boundary{idx}_{arm}',ok and cr['probe_calls']==256 and cr['ir_bytes']==len(s.encode())<=1048576 and 0<cr['probe_ir_bytes']==len(p.encode())<=1048576)
  code.append(dict(process=idx,arm=arm,batch_bytes=len(s.encode()),probe_bytes=len(p.encode())))
 proc=rd(out/'process.json');inv=rd(bind(V/f'invocation-{idx}.json'));invs.append(inv);res=rd(bind(V/f'reservation-{idx}.json'));cmd=rd(bind(V/'commands.json'))[str(idx)]
 ck(f'process{idx}',proc['returncode']==inv['returncode']==0 and proc['reason']=='exit0' and proc['pins_unchanged'] is True and proc['elapsed_including_launch']<=84 and inv['elapsed_seconds']<=90 and inv['supervisor']['accepted'] is True and not inv['supervisor']['soft_timeout'] and not inv['supervisor']['hard_timeout'] and proc['command']==res['command']==cmd and inv['command'][-len(cmd):]==cmd and rd(out/'pins.json')==pins)
 ck(f'links{idx}',inv['reservation_sha256']==sha(V/f'reservation-{idx}.json') and res['pins_sha256']==proc['pins_sha256']==sha(V/'pins.json') and res['review_sha256']==sha(V/'numerical-review.json') and res['context_sha256']==sha(V/'launch-context.json') and res['host_sha256']==sha(V/f'prelaunch-{idx}.json') and res['sequence_sha256']==sha(V/'sequence-reservation.json'))
 for who in ('runner','child'):groups.update((proc[who]['pgid'],proc[who]['sid']))
 samples=[json.loads(l) for l in (out/'resources.jsonl').read_text().splitlines()]+[proc['terminal_memory']]
 ck(f'memory{idx}',len(samples)>1 and all(s['available_kib']>=6*1024**2 and 0<=s['swap_used_kib']<=1024**2 for s in samples))
ck('call_totals',cost_calls==2080 and micro_calls==61440);ck('serial_limits',invs[1]['cumulative_seconds']==sum(v['elapsed_seconds'] for v in invs) and invs[1]['cumulative_seconds']<=180 and rd(V/'run-1/process.json')['ended']<rd(V/'run-2/process.json')['started'])
rows=[]
for ci,sp in enumerate(schedule['costs']):
 sides={s:[] for s in ('reference','candidate')};ps=[];ratios=[];deltas=[]
 for r in raws:
  arms={s:[w for w in r['costs'][ci]['windows'] if w['phase']=='measured' and w['side']==s] for s in sides}
  for s in sides:sides[s]+=arms[s]
  rt,ct=[st.median(w['seconds']/4 for w in arms[s]) for s in sides];v=dict(reference_seconds_per_call=rt,candidate_seconds_per_call=ct,ratio=ct/rt)
  for s in sides:
   for k in ('bytes','events'):v[s+'_'+k]=st.median(w[k] for w in arms[s])
  v['accepted']=(ct<rt and all(v['candidate_'+k]<v['reference_'+k] for k in ('bytes','events'))) if sp['eligible'] else (ct-rt<=max(.10*rt,.4e-6) and all(v['candidate_'+k]<=v['reference_'+k] for k in ('bytes','events')))
  ps.append(v);ratios += [b['seconds']/a['seconds'] for a,b in zip(arms['reference'],arms['candidate'])];deltas += [(b['seconds']-a['seconds'])/4 for a,b in zip(arms['reference'],arms['candidate'])]
 rt,ct=[st.median(w['seconds']/4 for w in sides[s]) for s in sides];ok=ct<rt if sp['eligible'] else ct-rt<=max(.05*rt,.2e-6)
 rows.append(dict(id=sp['id'],target=sp['eligible'],reference_seconds_per_call=rt,candidate_seconds_per_call=ct,pooled_ratio=ct/rt,paired_ratios=ratios,paired_deltas_seconds_per_call=deltas,processes=ps,accepted=ok and all(p['accepted'] for p in ps)))
ck('independent_reducers_match',rows==aggregate['cases']==summary['costs']);ck('all12_cost_gates',len(rows)==12 and all(x['accepted'] for x in rows))
red=[]
for row in raws[0]['red']:
 red.append(dict(id=row['id'],**{k:st.median(w[k] for w in row['windows'] if w['phase']=='measured' and w['side']=='candidate')-st.median(w[k] for w in row['windows'] if w['phase']=='measured' and w['side']=='reference') for k in ('bytes','events')}))
ck('old_RED',len(red)==2 and all(x['bytes']>0 or x['events']>0 for x in red) and red==aggregate['old_RED']==summary['old_RED'])
for ci,sp in enumerate(schedule['micro']):
 row={'id':sp['id'],'processes':[]}
 for r in raws:
  row['processes'].append({s:{k:st.median(w[k]/256 if k=='seconds' else w[k] for w in r['micro'][ci]['windows'] if w['phase']=='measured' and w['side']==s) for k in ('seconds','bytes','events')} for s in ('reference','candidate')})
 micros.append(row)
boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip();matches=[]
for p in Path('/proc').glob('[0-9]*'):
 try:
  fs=(p/'stat').read_text().rsplit(')',1)[1].split()
  if int(fs[2]) in groups or int(fs[3]) in groups or (p/'exe').resolve().name.startswith('julia'):matches.append(int(p.name))
 except (FileNotFoundError,ProcessLookupError):pass
ck('fresh170groups_AND_sessions',len(groups)==170 and boot==host['boot_id'] and not matches)
details.update(costs=rows,micro=micros,old_RED=red,code=code,cost_backend_calls=cost_calls,micro_predicate_calls=micro_calls,measured_windows=len(allwindows),measured_gc_windows=sum(w['gc_seconds']>0 for w in allwindows),no_scope_available=c['no_scope_available'],recorded_assertion_counts=c['counts'],groups=sorted(groups),matches=matches)
for p in (V/'admission.md',V/'work-ledger.md',V/'driver.jl',V/'tests-recorded.jl',V/'guard-tests-recorded.jl',V/'micro-batch.jl',U/'candidate.jl',U/'reference.jl',U/'instrumented.jl',V/'audit.py',E/'reviewer-check.py',R/'docs/superpowers/plans/2026-10-14-ma-rounding-guard.md'):bind(p)
result=dict(all_computed_checks_passed=all(checks.values()),computed_checks=checks,details=details,sha256={str(p):sha(p) for p in sorted(bound)})
with (E/'reviewer-check.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
print(json.dumps(dict(all_computed_checks_passed=result['all_computed_checks_passed'],checks=len(checks),bindings=len(bound),pins=len(iv),old_RED=red,cases=[(r['id'],r['pooled_ratio'],r['accepted']) for r in rows],code=code)))
