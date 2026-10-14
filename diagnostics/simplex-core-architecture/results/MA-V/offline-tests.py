"""New pure Python schema/mutation tests; no host/launcher/guard execution."""
from pathlib import Path
import copy,importlib.util,json,sys,tempfile,ast
D=Path(__file__).resolve().parent
sys.dont_write_bytecode=True
sys.path.insert(0,str(D))
import audit as A
import launcher as L
checks={}
def check(n,v):
 checks[n]=v is True
 if not checks[n]:raise ValueError(n)
def measured():return dict(seconds=4e-6,bytes=80,events=4,gc_seconds=0.,compile_seconds=0.,recompile_seconds=0.)
def window_rows(cases,index,micro=False,red=False):
 rows=[]
 for ci,f in enumerate(cases,1):
  c=dict(id=f['id'],expected=(256 if f['expected'] else 0) if micro else ['token']*f['n'],windows=[])
  if not micro:c['eligible']=f['eligible'];c['bundle_snapshot_setup_seconds']=.1
  for pair in range(1,11):
   order=['reference','candidate'] if (index+ci+pair)%2==0 else ['candidate','reference']
   for oi,side in enumerate(order,1):
    w=measured();w.update(pair=pair,order=oi,side=side,phase='warm' if pair<=3 else 'measured',calls=256 if micro else 4)
    if micro:
     w.update(checksum=c['expected']);w['bytes']=w['events']=0
    else:
     w.update(output=c['expected'].copy(),preserved=True)
     if side=='candidate':
      if red:w.update(bytes=96,events=6)
      elif f['eligible']:w.update(bytes=64,events=3,seconds=3e-6)
    c['windows'].append(w)
  rows.append(c)
 return rows

def make_raw(index):
 raw=dict(index=index,errors=[],ambient_restored=True,load_seconds=1.,code_inspection_seconds=.2,micro_inclusive_seconds=.3,cost_inclusive_seconds=.4,loaded_paths={'synthetic':'/tmp/synthetic'},
  code=[dict(arm=arm,path=str(D/f'run-{index}/micro-{arm}.ll'),probe_calls=256,accepted=True,ir_bytes=1000,probe_path=str(D/f'run-{index}/probe-{arm}.ll'),probe_ir_bytes=1000) for arm in ('old','new')],timer_baseline=[dict(measured(),bytes=0,events=0,phase='warm' if i<=3 else 'measured') for i in range(1,11)],red=[],correctness={},micro=window_rows(A.spec()['micro'],index,True),costs=window_rows(A.spec()['costs'],index))
 if index==1:
  pred=lambda e:[dict(id=id,reference=b,candidate=b,expected=b,effective=m) for id,b,m in e]
  rows=[]
  for id,dr,e,calls,n,exc in A.expected_whole():
   rows.append(dict(id=id,direction=dr,eligible=e,calls_per_side=calls,exception=[] if exc is None else [exc,'synthetic exception'],output=['token']*n,route_counts=dict(entries=calls,scratches=calls if e else 0,fallbacks=0 if e else calls)))
  raw.update(correctness_seconds=1.,red=window_rows(A.spec()['red'],index,red=True),correctness=dict(counts=dict(pass_=1),predicates=pred(A.expected_predicates()),transitions=pred(A.expected_transitions()),tasks_created=3,no_scope_available=False,no_scope_records=[],whole=rows))
  raw['correctness']['counts']={'pass':1,'fail':0,'error':0,'broken':0}
 return raw
raws=[make_raw(1),make_raw(2)]
for i,r in enumerate(raws,1):check(f'valid_raw_{i}',A.passed(A.validate_raw(r,i)))
check('exact840_844',len(A.expected_whole())==840 and sum(r[3] for r in A.expected_whole())==844)
check('counts270_25',len(A.expected_predicates())==270 and len(A.expected_transitions())==25)
check('aggregate_all12',len(A.aggregate(raws))==12 and all(r['accepted'] for r in A.aggregate(raws)))
def reject(name,mutate,index=1):
 r=copy.deepcopy(raws[index-1]);mutate(r);check('reject_'+name,not A.passed(A.validate_raw(r,index)))
reject('header_error',lambda r:r['errors'].append('failure'))
reject('restoration',lambda r:r.update(ambient_restored=False))
reject('bool_index',lambda r:r.update(index=True))
reject('missing_correctness',lambda r:r.update(correctness={}))
reject('missing_predicate',lambda r:r['correctness']['predicates'].pop())
reject('wrong_predicate',lambda r:r['correctness']['predicates'][0].update(candidate=False))
reject('mode',lambda r:r['correctness']['predicates'][0].update(effective='wrong'))
reject('transition',lambda r:r['correctness']['transitions'][1].update(candidate=True))
reject('task_count',lambda r:r['correctness'].update(tasks_created=2))
reject('fabricated_noscope',lambda r:r['correctness'].update(no_scope_available=True))
reject('missing_whole',lambda r:r['correctness']['whole'].pop())
reject('reordered_whole',lambda r:r['correctness']['whole'].reverse())
reject('route',lambda r:r['correctness']['whole'][0]['route_counts'].update(scratches=0))
reject('bool_counter',lambda r:r['correctness']['whole'][0]['route_counts'].update(entries=True))
reject('calls',lambda r:r['correctness']['whole'][0].update(calls_per_side=2))
reject('testfailure',lambda r:r['correctness']['counts'].update(fail=1))
reject('exception',lambda r:r['correctness']['whole'][0].update(exception=['ErrorException','x']))
reject('extra_process2_correctness',lambda r:r.update(correctness={'x':1}),2)
reject('RED_absent',lambda r:r.update(red=[]))
reject('RED_no_regression',lambda r:[w.update(bytes=80,events=4) for w in r['red'][0]['windows']])
reject('RED_wrong_output',lambda r:r['red'][1]['windows'][0].update(output=['different']))
reject('code_hoisted',lambda r:r['code'][0].update(probe_calls=1))
reject('code_missing',lambda r:r['code'].pop())
reject('code_path',lambda r:r['code'][0].update(path='/tmp/old.ll'))
reject('code_size',lambda r:r['code'][0].update(ir_bytes=1048577))
reject('baseline_alloc',lambda r:r['timer_baseline'][3].update(events=1))
reject('baseline_compile',lambda r:r['timer_baseline'][3].update(compile_seconds=.01))
reject('missing_baseline',lambda r:r['timer_baseline'].pop())
reject('micro_missing',lambda r:r['micro'].pop())
reject('micro_checksum',lambda r:r['micro'][0]['windows'][0].update(checksum=0))
reject('micro_alloc',lambda r:[w.update(bytes=1) for w in r['micro'][0]['windows'] if w['side']=='candidate' and w['phase']=='measured'])
reject('micro_events',lambda r:[w.update(events=1) for w in r['micro'][0]['windows'] if w['side']=='candidate' and w['phase']=='measured'])
reject('cost_case',lambda r:r['costs'].pop())
reject('window_count',lambda r:r['costs'][0]['windows'].pop())
reject('window_order',lambda r:r['costs'][0]['windows'][0].update(order=2))
reject('window_calls',lambda r:r['costs'][0]['windows'][0].update(calls=3))
reject('window_compile',lambda r:r['costs'][0]['windows'][6].update(compile_seconds=.1))
reject('window_recompile',lambda r:r['costs'][0]['windows'][6].update(recompile_seconds=.1))
reject('window_preserve',lambda r:r['costs'][0]['windows'][6].update(preserved=False))
for key,value in [('seconds',float('nan')),('bytes',True),('events',-1),('gc_seconds',float('inf'))]:reject('metric_'+key,lambda r,k=key,v=value:r['costs'][0]['windows'][0].update(**{k:v}))
# No aggregate pooling may rescue an individual process/case/control failure.
for label,ci,key,value in [('target_time',0,'seconds',4.1e-6),('target_bytes',0,'bytes',80),('target_events',0,'events',4),('fallback_bytes',4,'bytes',81),('fallback_events',4,'events',5),('fallback_time',4,'seconds',6e-6),('small_time',10,'seconds',6e-6)]:
 rs=copy.deepcopy(raws)
 for w in rs[0]['costs'][ci]['windows']:
  if w['side']=='candidate' and w['phase']=='measured':w[key]=value
 check('aggregate_reject_'+label,not A.aggregate(rs)[ci]['accepted'])
 check('stage_stops_'+label,not A.passed(A.validate_raw(rs[0],1)))
# Per-side medians must differ from median ratios in this discriminator.
rs=copy.deepcopy(raws)
for p in rs:
 for side,series in [('reference',[1,1,1,100,100,100,100]),('candidate',[2,2,2,50,50,50,50])]:
  ws=[w for w in p['costs'][0]['windows'] if w['side']==side and w['phase']=='measured']
  for w,x in zip(ws,series):w['seconds']=x*1e-6
row=A.aggregate(rs)[0];check('side_median_reducer',row['pooled_ratio']==.5 and row['processes'][0]['ratio']==.5 and row['accepted'])
# Retain GC/outlier windows; they are not grounds for deleting samples.
r=copy.deepcopy(raws[0]);r['costs'][0]['windows'][6]['gc_seconds']=.0001
check('GC_kept',A.passed(A.validate_raw(r,1)))
text='\n'.join(f'  %v{i} = call i8 @j_probe_1()' for i in range(256))
check('code256',A.code_valid(text));check('code1_rejected',not A.code_valid(' %x = call i8 @j_probe_1()'))
check('code_indirect_rejected',not A.code_valid(text+'\n %a = call i8 %fp()'))
check('code_apply_rejected',not A.code_valid(text+'\n %a = call i8 @jl_apply()'))
# Pure scalar guard gates, no processes created.
boot='synthetic-boot';identity=dict(pid=900,pgid=900,sid=900,start_ticks=10,boot_id=boot,command='synthetic')
proc=dict(returncode=0,started=1.,ended=2.,elapsed_including_launch=1.,runner=identity,child=dict(identity,pid=901,pgid=901,sid=901))
inv=dict(returncode=0,elapsed_seconds=2.,cumulative_seconds=2.);res=dict(seconds=90);ctx=dict(boot_id=boot,refs={'x':'y'},maximum_processes=2,maximum_seconds_per_process=90)
seq=dict(maximum_processes=2,total_cap_seconds=180,no_retry=True);post=dict(time=2.,groups=[*range(1,167),900,901],boot_id=boot,matches=[],refs=ctx['refs'])
samples=[dict(available_kib=7*1024**2,swap_used_kib=0)]*2
check('stage_valid',A.passed(A.stage_scalars(proc,inv,res,samples,post,ctx,seq)))
for name,args in [
 ('inner_overrun',[dict(proc,elapsed_including_launch=85),inv,res,samples,post,ctx,seq]),
 ('outer_overrun',[proc,dict(inv,elapsed_seconds=91,cumulative_seconds=91),res,samples,post,ctx,seq]),
 ('total_overrun',[proc,dict(inv,cumulative_seconds=181),res,samples,post,ctx,seq]),
 ('old120',[proc,inv,dict(seconds=120),samples,post,ctx,seq]),
 ('old3',[proc,inv,res,samples,post,dict(ctx,maximum_processes=3),seq]),
 ('pid_only',[proc,inv,res,samples,dict(post,groups=list(range(1,167))),ctx,seq]),
 ('165groups',[proc,inv,res,samples,dict(post,groups=[*range(1,164),900,901]),ctx,seq]),
 ('live',[proc,inv,res,samples,dict(post,matches=[identity]),ctx,seq]),
 ('swap',[proc,inv,res,[dict(available_kib=7*1024**2,swap_used_kib=2*1024**2)]*2,post,ctx,seq]),
 ('ram',[proc,inv,res,[dict(available_kib=5*1024**2,swap_used_kib=0)]*2,post,ctx,seq]),
 ('no_startticks',[dict(proc,child={k:v for k,v in identity.items() if k!='start_ticks'}),inv,res,samples,post,ctx,seq])]:check('stage_reject_'+name,not A.passed(A.stage_scalars(*args)))
# Admission validator only; synthetic files are NOT actual launch contexts/seals.
oldD=L.D
with tempfile.TemporaryDirectory() as tmp:
 T=Path(tmp);L.D=T
 names=['driver.jl','micro-batch.jl','tests-recorded.jl','guard-tests-recorded.jl','launcher.py','guard.py','supervisor.py','audit.py','schedule.json','commands.json','admission.md']
 for n in names:(T/n).write_text('synthetic '+n)
 manifest=dict(files=[str(T/n) for n in names],trees=[],inventory={str(T/n):dict(resolved=str(T/n),sha256=A.sha(T/n)) for n in names})
 def put(n,o):(T/n).write_text(json.dumps(o))
 put('pins.json',manifest);required=list(manifest['inventory']);put('required-paths.json',required)
 context=dict(standing_short_run_permission=True,maximum_processes=2,maximum_seconds_per_process=90);put('launch-context.json',context)
 prep=dict(accepted=True,findings=[],pins_sha256=A.sha(T/'pins.json'),sha256={str(T/n):A.sha(T/n) for n in [*names,'pins.json','required-paths.json']});put('admission-review.json',prep)
 seal=dict(accepted=True,findings=[],pins_sha256=A.sha(T/'pins.json'),context_sha256=A.sha(T/'launch-context.json'),preparation_review_sha256=A.sha(T/'admission-review.json'),sha256={str(T/n):A.sha(T/n) for n in ['pins.json','launch-context.json','admission-review.json']})
 def accepts(p=prep,s=seal,c=context,req=required):
  try:L.validate_admission(manifest,req,p,s,c);return True
  except (ValueError,KeyError,FileNotFoundError):return False
 check('admission_valid',accepts())
 for name,kwargs in [('prep_reject',dict(p=dict(prep,accepted=False))),('prep_membership',dict(p=dict(prep,sha256={}))),('seal_reject',dict(s=dict(seal,accepted=False))),('seal_membership',dict(s=dict(seal,sha256={}))),('seal_findings',dict(s=dict(seal,findings=['x']))),('pin_link',dict(s=dict(seal,pins_sha256='x'))),('context_link',dict(s=dict(seal,context_sha256='x'))),('prep_link',dict(s=dict(seal,preparation_review_sha256='x'))),('permission',dict(c=dict(context,standing_short_run_permission=False))),('limits',dict(c=dict(context,maximum_seconds_per_process=91))),('bool_limits',dict(c=dict(context,maximum_processes=True))),('required_empty',dict(req=[])),('required_duplicate',dict(req=required+[required[0]]))]:check('admission_reject_'+name,not accepts(**kwargs))
 (T/'driver.jl').write_text('changed');check('admission_reject_drift',not accepts())
L.D=oldD
# Durable journal correspondence; independent layout construction.
def journal(r):
 out=[dict(kind='baseline',index=i,window=w) for i,w in enumerate(r['timer_baseline'],1)]
 def cost(cs):
  for c in cs:
   for w in c['windows']:
    loc='cost/'+c['id']+'/'+str(w['pair'])+'/'+str(1 if w['side']=='reference' else 2)
    out.append(dict(kind='whole-metrics',location=loc,window={k:v for k,v in w.items() if k not in ('output','preserved')}))
    out.append(dict(kind='whole-complete',location=loc,window=w))
 cost(r['red'])
 if r['index']==1:
  c=r['correctness']
  for row in c['predicates']+c['transitions'][:20]+c['no_scope_records']+c['transitions'][20:]+c['whole']:out.append(dict(kind='correctness',record=row))
 for c in r['micro']:
  for w in c['windows']:out.append(dict(kind='micro',location='micro/'+c['id']+'/'+str(w['pair'])+'/'+str(1 if w['side']=='reference' else 2),window=w))
 cost(r['costs']);return out
for i,r in enumerate(raws,1):
 j=journal(r);check('journal_valid_'+str(i),A.journal_valid(j,r))
 check('journal_count_'+str(i),len(j)==(1825 if i==1 else 610))
 for label,mut in [('truncated',lambda x:x.pop()),('changed',lambda x:x[0]['window'].update(bytes=1)),('reordered',lambda x:x.reverse())]:
  jj=copy.deepcopy(j);mut(jj)
  try:A.journal_valid(jj,r);refused=False
  except (ValueError,KeyError):refused=True
  check('journal_reject_'+str(i)+'_'+label,refused)
# Source-level no-launch gate only; don't import or execute guard/main.
for n in ['audit.py','launcher.py','guard.py','offline-tests.py']:ast.parse((D/n).read_text())
check('no_outputs',not any((D/n).exists() for n in ['launch-context.json','numerical-review.json','sequence-reservation.json','run-1','run-2']))
obj=dict(all_passed=all(checks.values()),checks=checks,scope='New pure Python synthetic records only; no Julia, no host calls, no launcher/guard main, no old audits',sha256={str(D/n):A.sha(D/n) for n in ['audit.py','launcher.py','guard.py','schedule.json','offline-tests.py']})
with (D/'offline-tests-complete.json').open('x') as f:json.dump(obj,f,indent=2);f.write('\n')
print(len(checks),'PASS')
