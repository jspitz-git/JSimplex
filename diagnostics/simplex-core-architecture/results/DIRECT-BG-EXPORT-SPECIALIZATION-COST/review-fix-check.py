"""New offline correction checks: actual TOML, exact rational residuals, no operational audit."""
from pathlib import Path
import ast,copy,hashlib,json,math,struct,sys,tempfile,types
D=Path(__file__).resolve().parent;sys.path.insert(0,str(D))
import record_schema as schema,analysis as a,evidence as e
checks={};sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def ck(n,v):checks[n]=bool(v)
def refuses(fn):
 try:fn();return False
 except (ValueError,RuntimeError,KeyError,TypeError,IndexError):return True
# Reuse only pure fixture constructors from the preserved independent checker;
# never execute its top-level checker, output writer or any operational function.
s=(D/'reviewer-check.py').read_text();pure=s[s.index('def tok(x):'):s.index("with tempfile.TemporaryDirectory(prefix='bgxs-reviewer-pure-')")]
exec(compile(pure,'preserved-pure-fixture-definitions','exec'))
old=types.ModuleType('old_evidence');exec(compile((D/'evidence.py.before-review').read_text(),'preserved-old-pure-evidence','exec'),old.__dict__)
# Real successful saved GC records are positive schema fixtures only, not reaudited.
G=D.with_name('DIRECT-BG-EXPORT-SPECIALIZATION-GC-DRIVER')/'runs/greengc300';rd=lambda p:json.loads(Path(p).read_text())
p=rd(G/'output/process.json');cur=rd(G/'output/current.json');inv=rd(G/'invocation.json');resources=[json.loads(x) for x in (G/'output/resources.jsonl').read_text().splitlines()];hosts=[rd(G/n) for n in ['prehost.json','host.json','posthost.json']]
args=[p,cur,inv,resources,hosts,300]
ck('real_writer_record_schema',not refuses(lambda:schema.runtime(*args)))
ck('real_writer_success',schema.success(p,inv['supervisor']))
# Strict runtime leaf and record tests; no live host/process queries.
mutations=[('process_boolean_exit',lambda v:v[0].update(returncode=False)),('supervisor_boolean_exit',lambda v:v[2]['supervisor'].update(returncode=False)),('infinite_available',lambda v:v[3][0].update(available_kib=float('inf'))),('negative_swap',lambda v:v[3][0].update(swap_used_kib=-1)),('negative_infinite_swap',lambda v:v[3][0].update(swap_used_kib=-float('inf'))),('boolean_swap',lambda v:v[3][0].update(swap_used_kib=False)),('missing_soft',lambda v:v[2]['supervisor'].pop('soft_timeout')),('missing_accepted',lambda v:v[2]['supervisor'].pop('accepted')),('boolean_identity',lambda v:v[0]['child'].update(pid=True)),('infinite_elapsed',lambda v:v[0].update(elapsed_including_launch=float('inf'))),('float_rss',lambda v:v[0].update(child_maxrss_kib=1.5)),('negative_sample_elapsed',lambda v:v[3][0].update(elapsed=-1)),('boolean_sample_elapsed',lambda v:v[3][0].update(elapsed=True)),('host_boolean_group',lambda v:v[4][0]['groups'].__setitem__(0,True)),('host_unknown_key',lambda v:v[4][0].update(unrecognized=True)),('process_extra_key',lambda v:v[0].update(unrecognized=True)),('current_status',lambda v:v[1].update(returncode=False)),('invocation_bad_digest',lambda v:v[2].update(pins_sha256='bad'))]
for label,mutate in mutations:
 v=copy.deepcopy(args);mutate(v);ck('runtime_refuse:'+label,refuses(lambda:schema.runtime(*v)))
for flag in ['soft_timeout','hard_timeout','child_kill','guard_term','guard_kill']:
 sup=dict(inv['supervisor']);sup[flag]=True;ck('contradictory_success:'+flag,not schema.success(p,sup))
 for bad in [0,1,None]:
  v=copy.deepcopy(args);v[2]['supervisor'][flag]=bad;ck('flag_type:'+flag+':'+str(bad),refuses(lambda:schema.runtime(*v)))
# Pure timeout requires complete Boolean semantics and no supervisor intervention.
tp=dict(reason='wall_time',returncode=-15,pins_unchanged=True);ts=dict(returncode=1,hard_timeout=False,child_kill=False,guard_term=False,guard_kill=False,soft_timeout=False,accepted=False);log='BEGIN BG export workspace cost cost1-300'
ck('timeout_valid',e.timeout_ok(tp,ts,log,292.,300))
for label,sup in [('timeout_missing_soft_and_accepted',{k:v for k,v in ts.items() if k not in ('soft_timeout','accepted')}),('timeout_contradictory_soft_timeout',dict(ts,soft_timeout=True)),('timeout_accepted_true',dict(ts,accepted=True))]:
 ck('RED_old:'+label,old.timeout_ok(tp,sup,log,292.,300));ck('GREEN_new:'+label,not e.timeout_ok(tp,sup,log,292.,300))
v=copy.deepcopy(args);v[0].update(returncode=-15,reason='wall_time');v[2]['supervisor'].update(returncode=1,accepted=False)
ck('pure_timeout_full_runtime_schema',not refuses(lambda:schema.runtime(*v)))
# Exact schema proof on complete first/reversed schedules and all legal prefixes.
with tempfile.TemporaryDirectory(prefix='bgxs-schema-fix-') as temp:
 root=Path(temp);out=root/'runs/cost1-300/output';out.mkdir(parents=True);(root/'inputs.json').write_text(json.dumps(dict(fixtures=fx)));(root/'loaded-paths.json').write_text('{}')
 cfg=dict(phase='cost1-300',process=1,stage='/synthetic/stage');data={'controls.toml':controls};base=['pins.json','current.json','process.json','resources.jsonl','run.log']
 for name in base:(out/name).write_text('{}')
 for i in range(1,9):
  b='native' if i%2 else 'markowitz';ident=dict(fixture=fx[(i-1)//2]['name'],manager='BG',backend=b,policy='threshold_one' if b=='native' else 'default')
  data.update({f'started-{i}.toml':ident,f'preflight-{i}.toml':preflight(b),f'probe-{i}.toml':probe(),f'cell-{i}.toml':dict(ident,windows=20)})
  for w in range(1,21):data[f'window-{i}-{w}.toml']=window(1,w,b)
 data['raw.toml']=dict(phase='cost1-300',loaded=dict(JSimplex='/synthetic/stage/src/JSimplex.jl'),completed=True,fatal='',cells=8,windows=160,threads=1,blas_threads=1)
 for name,v in data.items():dump_toml(out/name,v)
 rows,totals=e.output_checks(out,cfg);ck('complete_live_TOML_residuals',totals==dict(cells=8,windows=160,window_outputs=3840,probe_outputs=576));ck('first_all8',a.first_process_viable(dict(all_passed=True,pure_timeout=False,cells=rows),fx))
 mutations=[('probe_infinite_graph','probe-1.toml',lambda v:(v.update(coexistence_graph_peak=float('inf')),[s.update(coexistence_graph_peak=float('inf')) for s in v['states']])),('probe_boolean_copies','probe-1.toml',lambda v:v.update(copies=False)),('probe_float_constructions','probe-1.toml',lambda v:v.update(constructions=3.0)),('probe_unknown_key','probe-1.toml',lambda v:v.update(unrecognized=True)),('probe_boolean_step','probe-1.toml',lambda v:v['states'][0].update(step=False)),('control_boolean_call','controls.toml',lambda v:v.update(orientation_synthetic_calls=True)),('control_infinite_graph','controls.toml',lambda v:v['transitions'][0]['states'][0].update(coexistence_graph=float('inf'))),('control_unknown_key','controls.toml',lambda v:v.update(unrecognized=True)),('raw_integer_completed','raw.toml',lambda v:v.update(completed=1)),('cell_float_window_count','cell-1.toml',lambda v:v.update(windows=20.0))]
 for label,name,mutate in mutations:
  v=copy.deepcopy(data[name]);mutate(v);dump_toml(out/name,v);ck('RED_old:'+label,not refuses(lambda:old.output_checks(out,cfg)));ck('GREEN_new:'+label,refuses(lambda:e.output_checks(out,cfg)));dump_toml(out/name,data[name])
 order=['controls.toml']+[name for i in range(1,9) for name in [f'started-{i}.toml',f'preflight-{i}.toml',f'probe-{i}.toml']+[f'window-{i}-{w}.toml' for w in range(1,21)]+[f'cell-{i}.toml']]
 for name in data:(out/name).unlink()
 for length in range(len(order)):
  if length:dump_toml(out/order[length-1],data[order[length-1]])
  ck('legal_partial_live:'+str(length),not refuses(lambda:e.output_checks(out,cfg,partial=True)))
 for name,v in data.items():
  if name.startswith('window-'):
   _,i,w=name.removesuffix('.toml').split('-');v=window(2,int(w),'native' if int(i)%2 else 'markowitz')
  elif name=='raw.toml':v=dict(v,phase='cost2-300')
  dump_toml(out/name,v)
 reverse,_=e.output_checks(out,dict(cfg,phase='cost2-300',process=2));ck('reversed_gates',all(a.qualify(x['statistics'],y['statistics']) for x,y in zip(rows,reverse)))
# Initial pins and checker bindings resolve only through exact explicit before copies.
mp=rd(D/'review-fix-map.json')['mapping']
for name in ['preparation-pins.json','source-check.json','offline-tests-2.json']:
 for path,h in rd(D/name)['sha256'].items():
  actual=Path(mp[path]['preserved']) if path in mp else Path(path)
  ck('initial_binding:'+name+':'+path,sha(actual)==h)
for n in ['audit.py','evidence.py','control.py','record_schema.py']:ast.parse((D/n).read_text());ck('syntax:'+n,True)
ck('runtime_hook',"schema.runtime(p,cur,inv,resources,[pre,hs,post],cfg['seconds'])" in (D/'audit.py').read_text())
ck('success_hook',"require(schema.success(p,sup),'Exact exit')" in (D/'audit.py').read_text())
for n in ['cost.jl','probe.jl','analysis.py','stages.json','guard.py','supervisor.py','outer.py','seal.py','launch.py']:
 ck('unchanged_runtime:'+n,sha(D/n)==rd(D/'preparation-pins.json')['sha256'][str(D/n)])
paths=[D/n for n in ['review-fix-check.py','record_schema.py','review-fix.py','review-fix-map.json','audit.py','evidence.py','control.py','review.json','reviewer-check.json','source-check.json','offline-tests-2.json']]
result=dict(all_passed=all(checks.values()),checks=checks,failed=[n for n,v in checks.items() if not v],sha256={str(p):sha(p) for p in paths},scope='Offline synthetic RED/GREEN only, actual TOML/live exact residuals; no operational auditor, guard, launcher or Julia')
with (D/'review-fix-check.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
print(json.dumps(dict(all_passed=result['all_passed'],checks=len(checks),failed=result['failed'])) )
if not result['all_passed']:raise SystemExit(1)
