"""New synthetic full saved-output tests, no Julia or operational audit invocation."""
from pathlib import Path
import sys,json,tempfile,copy,ast,struct
D=Path(__file__).resolve().parent;sys.path.insert(0,str(D));import control as c, evidence as e, analysis as a
checks={}
def ck(n,v):checks[n]=bool(v)
def reject(fn):
 try:fn();return False
 except (ValueError,RuntimeError,KeyError,TypeError,IndexError,FileNotFoundError):return True
def tok(x):return struct.pack('>d',x).hex()
one=tok(1.0);zero=tok(0.0)
fixture=lambda name:dict(name=name,n=1,matrices=[dict(n=1,colptr=[1,2],rowval=[1],nzval=[one]) for _ in range(9)],steps=[dict(j=1,a=[one],dse=[one],unit=[one]) for _ in range(8)])
fixtures=[fixture(n) for n in ['sparse32','dense32','sparse96','dense96']]
keys='allocation_requests requested_payload factorizations extractions orientation_solves orientation_products triangle_checks permutation_checks normalized_stores raw_stores fallback_stores index_stores refactor_entries'.split()
counts=lambda **kw:dict({k:0 for k in keys},**kw)
cache=dict(present=False,dimension=0,charge=0,limit=0,seen_bytes=0,orientation_bytes=0,graph_bytes=0)
controls=dict(complete=True,inputs_unchanged=True,orientation_synthetic_calls=1,orientation_requests=2,orientation_payload=64,constructions=4,copies=4,refactors=12,explicit_solves=0,imports=[dict(name=n,correct=True,u=6,counts=counts(normalized_stores=ns,raw_stores=rs,fallback_stores=fs,index_stores=6)) for n,ns,rs,fs in [('normalize_false',0,6,0),('reject_first',1,0,6),('reject_last',4,0,6)]],transitions=[dict(backend=b,constructions=2,copies=2,refactors=6,explicit_solves=0,states=[dict(name=n,cache=cache,graphs=[100,100],coexistence_graph=400) for n in ['same_shape','large_to_small']],copy_cache=cache) for b in ['native','markowitz']])
def preflight(backend):
 pol='threshold_one' if backend=='native' else 'default';vals=[zero]*20;vals[3]=one
 rec=dict(kind=backend,policy=pol,control=vals if backend=='native' else [],expected_control=vals if backend=='native' else [],strategy=zero if backend=='native' else '')
 return dict(reference=[rec]*3,candidate=[rec]*3,modes=['normalized']*3,inputs_unchanged=True,constructions=2,refactors=4,explicit_solves=0)
def probe():
 cnt=counts(factorizations=3,extractions=3,refactor_entries=2)
 return dict(inputs_unchanged=True,constructions=3,refactors=6,updates=24,ftran=48,btran=24,copies=0,states=[dict(step=k,refactored=b,equal=True,graphs=[100,100,100],cache=cache,probe_cache=cache,counts=cnt,coexistence_graph_peak=400) for k,b in [(0,False)]+[(k,b) for k in range(1,9) for b in ([False,True] if k in (4,8) else [False])]],outputs=[[[one] for _ in range(24)] for _ in range(3)],counts=cnt,coexistence_graph_peak=400,cache_charge_sum=0,cache_charge_peak=0)
def window(process,w,backend):
 pair=(w+1)//2;order=(w-1)%2+1;side=a.schedule(process,pair)[order-1]
 return dict(pair=pair,order=order,side=side,measured=pair>3,policy='threshold_one' if backend=='native' else 'default',correct=True,inputs_unchanged=True,modes=['normalized']*3,seconds=1.0 if side=='reference' else .9,bytes=100,events=10,gc_seconds=0.,compile_seconds=0.,recompile_seconds=0.,retained_bytes=100,nested_seconds=[.01]*6,outputs=[[one] for _ in range(24)])
original_read=e.read
with tempfile.TemporaryDirectory(prefix='bgxs-task3-offline-') as tmp:
 root=Path(tmp);out=root/'runs/cost1-300/output';out.mkdir(parents=True);(root/'inputs.json').write_text(json.dumps(dict(fixtures=fixtures)));loaded={'LinearAlgebra':'synthetic-source'};(root/'loaded-paths.json').write_text(json.dumps(loaded));cfg=dict(phase='cost1-300',process=1,stage='/synthetic/stage')
 data={n:{} for n in ['pins.json','current.json','process.json','resources.jsonl','run.log']};data['controls.toml']=controls
 for i in range(1,9):
  b='native' if i%2 else 'markowitz';ident=dict(fixture=fixtures[(i-1)//2]['name'],manager='BG',backend=b,policy='threshold_one' if b=='native' else 'default')
  data[f'started-{i}.toml']=ident;data[f'preflight-{i}.toml']=preflight(b);data[f'probe-{i}.toml']=probe();data[f'cell-{i}.toml']=dict(ident,windows=20)
  for w in range(1,21):data[f'window-{i}-{w}.toml']=window(1,w,b)
 data['raw.toml']=dict(phase=cfg['phase'],loaded=dict(loaded,JSimplex='/synthetic/stage/src/JSimplex.jl'),completed=True,fatal='',cells=8,windows=160,threads=1,blas_threads=1)
 e.read=lambda p:json.loads(Path(p).read_text()) # JSON fixture codec only; semantic validators remain live.
 def install(values):
  for p in out.iterdir():p.unlink()
  for n,v in values.items():(out/n).write_text(json.dumps(v))
 install(data);result,totals=e.output_checks(out,cfg);ck('complete_first_160windows_4416residuals',totals==dict(cells=8,windows=160,window_outputs=3840,probe_outputs=576));ck('complete_first_all8_gates',a.first_process_viable(dict(all_passed=True,pure_timeout=False,cells=result),fixtures))
 for label,name,key,val in [('compile','window-1-7.toml','compile_seconds',.01),('recompile','window-8-20.toml','recompile_seconds',.01),('wrongside','window-1-1.toml','side','candidate'),('bad_metric','window-1-1.toml','events',True),('wrongpolicy','window-1-1.toml','policy','default'),('inputmutated','window-1-1.toml','inputs_unchanged',False),('residual','window-8-20.toml','outputs',[[tok(2.)]]*24),('probe_copy','probe-1.toml','copies',1),('control_budget','controls.toml','refactors',13),('fatalraw','raw.toml','fatal','error'),('thread','raw.toml','threads',2)]:
  v=copy.deepcopy(data);v[name][key]=val;install(v);ck('reject_'+label,reject(lambda:e.output_checks(out,cfg)))
 for label,change in [('unknown',lambda d:d.update({'orphan.toml':{}})),('missing',lambda d:d.pop('window-8-20.toml')),('probe_missing',lambda d:d.pop('probe-1.toml'))]:
  v=copy.deepcopy(data);change(v);install(v);ck('reject_'+label,reject(lambda:e.output_checks(out,cfg)))
 # Every legal write-prefix of the pinned schedule, before raw completion.
 order=['controls.toml']+[n for i in range(1,9) for n in [f'started-{i}.toml',f'preflight-{i}.toml',f'probe-{i}.toml']+[f'window-{i}-{w}.toml' for w in range(1,21)]+[f'cell-{i}.toml']]
 base={n:data[n] for n in ['pins.json','current.json','process.json','resources.jsonl','run.log']}
 # Bound synthetic cost: all193prefixes use live schema/stats, with residual predicate replaced by true (complete tests above exercised all4416).
 saved_residual=e.residual;e.residual=lambda *args:True;saved_window=a.residual;a.residual=lambda *args:True
 for n in range(len(order)):
  v=dict(base,**{key:data[key] for key in order[:n]});install(v);ck('valid_partial_prefix_'+str(n),not reject(lambda:e.output_checks(out,cfg,partial=True)))
 e.residual=saved_residual;a.residual=saved_window
 v=copy.deepcopy(data)
 for i in range(1,9):
  b='native' if i%2 else 'markowitz'
  for w in range(1,21):v[f'window-{i}-{w}.toml']=window(2,w,b)
 v['raw.toml']['phase']='cost2-300';install(v);result2,_=e.output_checks(out,dict(cfg,phase='cost2-300',process=2));ck('complete_second_reversed',all(a.qualify(x['statistics'],y['statistics']) for x,y in zip(result,result2)))
 e.read=original_read
# Protocol tests are pure identity/release and refusal/source tests only.
import outer
valid=dict(phase='cost1-300',sealed_sha256='s',admission_sha256='a',outer_ready_sha256='o',one_attempt=True)
ck('release_exact',outer.valid_release(valid,'s','a','o','cost1-300'))
for key,val in [('one_attempt',1),('sealed_sha256','bad'),('phase','cost2-300')]:ck('release_reject_'+key,not outer.valid_release(dict(valid,**{key:val}),'s','a','o','cost1-300'))
for phase in ['cost2-300','cost1-600','cost2-600']:ck('predecessor_refuses_'+phase,reject(lambda:c.predecessor(phase)))
for n in ['cost.jl','probe.jl','clone_source.py']:
 src=(D.with_name('DIRECT-BG-EXPORT-WORKSPACE-COST-PREPARATION')/n).read_text();new=(D/n).read_text();renamed=src.replace('_BGXBuildOwner','_BGXSBuildOwner').replace('BGExport','BGSpecializedExport').replace('_bgx_','_bgxs_').replace('_BGXPBuildOwner','_BGXSPBuildOwner').replace('BGProbeExport','BGSpecializedProbeExport').replace('_bgxp_','_bgxsp_');ck('namespace_only_'+n,new==renamed)
ck('exact_output_membership199',len(e.expected_names())==199)
ck('no_GC_added','GC.gc' not in (D/'cost.jl').read_text())
ck('no_operational_paths',not (D/'runs').exists() and not (D/'outers').exists())
for p in D.glob('*.py'):ast.parse(p.read_text())
c.save(D/'offline-tests-2.json',dict(all_passed=all(checks.values()),checks=checks,sha256={str(p):c.sha(p) for p in D.iterdir() if p.is_file()},scope='Synthetic saved-output semantics and source/protocol refusal; JSON codec mocked, partial-prefix residuals mocked only; complete tests perform exact residuals; no Julia or operational launch'))
print(json.dumps(dict(all_passed=all(checks.values()),checks=len(checks),failed=[k for k,v in checks.items() if not v])));c.require(all(checks.values()),'Preserve offline failure')
