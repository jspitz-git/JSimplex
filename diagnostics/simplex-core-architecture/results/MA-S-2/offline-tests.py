"""Only Python synthetic raw/guard helpers; no launcher/guard main or Julia."""
from pathlib import Path
import copy,json,math,importlib.util,tempfile
D=Path(__file__).resolve().parent

def module(name):
 s=importlib.util.spec_from_file_location(name,D/(name+'.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
A=module('audit');G=module('guard');results={}
def check(name,ok):
 results[name]=bool(ok)
 if not ok:raise ValueError(name)
def raw(index):
 x={'index':index,'errors':[],'ambient_restored':True,'load_seconds':1.,'candidate_definition_seconds':.1,'loaded_paths':{'mock-source':'/tmp/synthetic-only.jl'},'counts':{},'red':{},'correctness':[],'costs':[]}
 if index==1:
  x['counts']={k:{'pass':10,'fail':0,'error':0,'broken':0} for k in ('smoke','qualification')}
  x['red']={'pass':0,'fail':2,'error':0,'broken':0,'missing_route_only':True,'failure_expressions':['isdefined(P, :_dense_ma_eligible)','isdefined(P, :candidate_forward!) && isdefined(P, :candidate_transpose!)']}
  x['correctness']=[{'id':id,'direction':dr,'eligible':eligible,'calls_per_side':calls,'exception':[] if exc is None else [exc,'synthetic exception'],'output':['synthetic exact token']*n} for id,dr,eligible,calls,n,exc in A.expected_correctness()]
 for ci,f in enumerate(A.spec()['cost_cases'],1):
  c={'id':f['id'],'eligible':f['eligible'],'expected':['synthetic exact token']*f['n'],'windows':[]}
  for pair in range(1,11):
   sides=['reference','candidate'] if (index+ci+pair)%2==0 else ['candidate','reference']
   for order,side in enumerate(sides,1):
    candidate=side=='candidate' and f['eligible']
    c['windows'].append(dict(pair=pair,order=order,side=side,phase='warm' if pair<=3 else 'measured',calls=4,seconds=.00036 if candidate else .0004,bytes=90 if candidate else 100,events=9 if candidate else 10,gc_seconds=0.,compile_seconds=0.,recompile_seconds=0.,output=c['expected'].copy(),preserved=True))
  x['costs'].append(c)
 return x
rs=[raw(i) for i in (1,2,3)]
check('valid_three_synthetic_raws',all(A.passed(A.validate_raw(r,i)) for i,r in enumerate(rs,1)))
check('fixed_counts',len(A.expected_correctness())==160 and sum(r[3] for r in A.expected_correctness())==162 and len(A.spec()['cost_cases'])==52)
mutations={
 'missing_costs':lambda r:r.pop('costs'),
 'missing_case':lambda r:r['costs'].pop(),
 'duplicate_id':lambda r:r['costs'][0].update(id=r['costs'][1]['id']),
 'missing_correctness':lambda r:r['correctness'].pop(),
 'wrong_calls':lambda r:r['correctness'][0].update(calls_per_side=2),
 'generic_failure_as_RED':lambda r:r['red'].update(error=1,fail=1),
 'wrong_RED_expression':lambda r:r['red']['failure_expressions'].__setitem__(0,'false'),
 'test_failure':lambda r:r['counts']['qualification'].update(fail=1),
 'missing_exception':lambda r:r['correctness'][112].update(exception=[]),
 'extra_window':lambda r:r['costs'][0]['windows'].append(copy.deepcopy(r['costs'][0]['windows'][0])),
 'wrong_order':lambda r:r['costs'][0]['windows'][0].update(order=2),
 'negative_bytes':lambda r:r['costs'][0]['windows'][0].update(bytes=-1),
 'nan_time':lambda r:r['costs'][0]['windows'][0].update(seconds=math.nan),
 'boolean_event_count':lambda r:r['costs'][0]['windows'][0].update(events=True),
 'wrong_batch_budget':lambda r:r['costs'][0]['windows'][0].update(calls=5),
 'measured_compile':lambda r:r['costs'][0]['windows'][6].update(compile_seconds=.1),
 'changed_output':lambda r:r['costs'][0]['windows'][0].update(output=['bad']),
 'changed_input':lambda r:r['costs'][0]['windows'][0].update(preserved=False),
 'ambient_drift':lambda r:r.update(ambient_restored=False),
 'raw_error':lambda r:r.update(errors=['unexpected']),
}
for name,mutate in mutations.items():
 r=copy.deepcopy(rs[0]);mutate(r);check('reject_'+name,not A.passed(A.validate_raw(r,1)))
check('aggregate_target_and_controls_pass',all(r['accepted'] for r in A.aggregate(rs)))
for name,ci,field,value in [('target_equal_bytes',0,'bytes',100),('target_slow',0,'seconds',.00041),('control_extra_events',36,'events',11),('control_slow',36,'seconds',.0005)]:
 altered=copy.deepcopy(rs)
 for r in altered:
  for w in r['costs'][ci]['windows']:
   if w['side']=='candidate':w[field]=value
 check('reject_'+name,not A.aggregate(altered)[ci]['accepted'])
# Declared 15/21 faster threshold: six outliers retain 15 wins and median .9.
altered=copy.deepcopy(rs)
for r in altered:
 for w in r['costs'][0]['windows']:
  if w['side']=='candidate' and w['pair'] in (9,10):w['seconds']=.0005
check('target15wins_pass',A.aggregate(altered)[0]['accepted'])
for w in altered[0]['costs'][0]['windows']:
 if w['side']=='candidate' and w['pair']==8:w['seconds']=.0005
check('target14wins_reject',not A.aggregate(altered)[0]['accepted'])
check('memory_boundary',not G.pressure({'available_kib':6*1024**2,'swap_used_kib':1024**2}))
check('memory_low_reject',G.pressure({'available_kib':6*1024**2-1,'swap_used_kib':0}))
check('swap_high_reject',G.pressure({'available_kib':7*1024**2,'swap_used_kib':1024**2+1}))
a=dict(pid=1,start_ticks=1,boot_id='b',command='x',pgid=3,sid=4)
check('identity_start_ticks',not G.same_identity(a,dict(a,start_ticks=2)))
check('session_membership',G.identity_owned(a,4) and not G.identity_owned(a,9))
with tempfile.TemporaryDirectory() as tmp:
 p=Path(tmp)/'source';p.write_text('a');pins=dict(files=[str(p)],trees=[],inventory=G.inventory([str(p)],[]))
 check('pins_match',G.pins_match(pins));p.write_text('b');check('pins_drift_refused',not G.pins_match(pins))

for key in ('pair','order'):
 for value in (True,1.0):
  r=copy.deepcopy(rs[0]);r['costs'][0]['windows'][0][key]=value
  check('reject_'+key+'_'+type(value).__name__,not A.passed(A.validate_raw(r,1)))
ctx={'boot_id':'boot','refs':{'head':'h'},'maximum_processes':3,'maximum_seconds_per_process':120}
identity=lambda pid:dict(pid=pid,pgid=pid,sid=pid,start_ticks=1,boot_id='boot',command='synthetic')
proc=dict(returncode=0,started=1.,ended=3.,elapsed_including_launch=2.,runner=identity(1),child=identity(2))
inv=dict(returncode=0,elapsed_seconds=3.,cumulative_seconds=3.)
res=dict(seconds=120)
samples=[dict(available_kib=7*1024**2,swap_used_kib=0),dict(available_kib=7*1024**2,swap_used_kib=0)]
post=dict(time=4.,groups=list(range(1,161)),boot_id='boot',matches=[],refs={'head':'h'})
seq=dict(maximum_processes=3,total_cap_seconds=360,no_retry=True)
args=[proc,inv,res,samples,post,ctx,seq]
check('stage_valid',A.passed(A.stage_scalars(*args)))
mutations_stage={
 'proc_bool_exit':lambda a:a[0].update(returncode=False),
 'inv_bool_exit':lambda a:a[1].update(returncode=False),
 'float_exit':lambda a:a[0].update(returncode=0.0),
 'missing_exit':lambda a:a[0].pop('returncode'),
 'inf_available':lambda a:a[3][0].update(available_kib=math.inf),
 'terminal_negative_swap':lambda a:a[3][-1].update(swap_used_kib=-1),
 'float_memory':lambda a:a[3][0].update(available_kib=float(7*1024**2)),
 'bool_swap':lambda a:a[3][-1].update(swap_used_kib=False),
 'missing_terminal_memory':lambda a:a[3][-1].pop('available_kib'),
 'nan_time':lambda a:a[1].update(elapsed_seconds=math.nan),
 'negative_time':lambda a:a[0].update(elapsed_including_launch=-1),
 'total_less_than_stage':lambda a:a[1].update(cumulative_seconds=1),
 'over120':lambda a:a[1].update(elapsed_seconds=121,cumulative_seconds=121),
 'over360':lambda a:a[1].update(cumulative_seconds=361),
 'bool_pid':lambda a:a[0]['runner'].update(pid=True),
 'float_start_ticks':lambda a:a[0]['child'].update(start_ticks=1.0),
 'wrong_boot':lambda a:a[0]['child'].update(boot_id='other'),
 'missing_command':lambda a:a[0]['runner'].pop('command'),
 'float_group':lambda a:a[4]['groups'].__setitem__(0,1.0),
 'duplicate_group':lambda a:a[4]['groups'].__setitem__(0,2),
 'nonempty_session':lambda a:a[4].update(matches=[{'pid':1}]),
 'float_limit':lambda a:a[2].update(seconds=120.0),
 'float_maximum':lambda a:a[5].update(maximum_processes=3.0),
 'retry_flag':lambda a:a[6].update(no_retry=False),
}
for name,mutate in mutations_stage.items():
 a=copy.deepcopy(args);mutate(a);check('stage_reject_'+name,not A.passed(A.stage_scalars(*a)))


# New preparation-specific checks; only copied pure Python helpers.
check('stage_reject_only159groups',not A.passed(A.stage_scalars(proc,inv,res,samples,dict(post,groups=list(range(1,160))),ctx,seq)))
empty=copy.deepcopy(rs[0]);empty['costs']=[];empty['correctness']=[]
check('reject_empty_partial_MA_S_shape',not A.passed(A.validate_raw(empty,1)))
C=json.loads((D/'commands.json').read_text())
check('new_output_and_corrected_driver',all(c[-3:]==[str(D.with_name('MA-S-LOAD')/'driver.jl'),i,str(D/f'run-{i}')] for i,c in C.items()))
# validate_admission only: synthetic files/reviews in a temporary directory,
# no main(), host(), guard(), reservation, process, or numerical work.
L=module('launcher');oldD=L.D
with tempfile.TemporaryDirectory() as tmp:
 T=Path(tmp);L.D=T
 def put(n,o): (T/n).write_text(json.dumps(o))
 (T/'source').write_text('fixed')
 manifest=dict(files=[str(T/'source')],trees=[],inventory={str(T/'source'):dict(resolved=str((T/'source').resolve()),sha256=A.sha(T/'source'))})
 put('pins.json',manifest);put('launch-context.json',dict(standing_short_run_permission=True,maximum_processes=3,maximum_seconds_per_process=120))
 prep=dict(accepted=True,findings=[],pins_sha256=A.sha(T/'pins.json'),sha256={str(T/'source'):A.sha(T/'source')})
 put('admission-review.json',prep)
 seal=dict(accepted=True,findings=[],pins_sha256=A.sha(T/'pins.json'),context_sha256=A.sha(T/'launch-context.json'),preparation_review_sha256=A.sha(T/'admission-review.json'),sha256={str(T/n):A.sha(T/n) for n in ['pins.json','launch-context.json','admission-review.json']})
 context=json.loads((T/'launch-context.json').read_text())
 def accepts(p,s,c,required=None):
  try:L.validate_admission(manifest,list(manifest['inventory']) if required is None else required,p,s,c);return True
  except (ValueError,KeyError,FileNotFoundError):return False
 check('admission_synthetic_valid',accepts(prep,seal,context))
 for name,p,s,c in [
  ('prep_rejected',dict(prep,accepted=False),seal,context),
  ('seal_rejected',prep,dict(seal,accepted=False),context),
  ('seal_findings',prep,dict(seal,findings=['x']),context),
  ('old_manifest_hash',prep,dict(seal,pins_sha256='old'),context),
  ('wrong_context_hash',prep,dict(seal,context_sha256='old'),context),
  ('old_preparation_review',prep,dict(seal,preparation_review_sha256='old'),context),
  ('missing_seal_membership',prep,dict(seal,sha256={}),context),
  ('no_permission',prep,seal,dict(context,standing_short_run_permission=False)),
  ('wrong_limit',prep,seal,dict(context,maximum_seconds_per_process=121))]:
  check('admission_reject_'+name,not accepts(p,s,c))
 check('admission_reject_required_membership',not accepts(prep,seal,context,[]))
 (T/'source').write_text('drift')
 check('admission_reject_source_drift',not accepts(prep,seal,context))
L.D=oldD

obj={'scope':'Synthetic Python-only records and copied pure guard helpers, not numerical evidence or live guard execution. No old script run.','checks':results,'all_passed':all(results.values()),'sha256':{str(D/n):A.sha(D/n) for n in ['audit.py','guard.py','offline-tests.py','launcher.py','commands.json']}}
with (D/'offline-tests.json').open('x') as f:json.dump(obj,f,indent=2);f.write('\n')
print(json.dumps({'checks':len(results),'all_passed':obj['all_passed']}))
