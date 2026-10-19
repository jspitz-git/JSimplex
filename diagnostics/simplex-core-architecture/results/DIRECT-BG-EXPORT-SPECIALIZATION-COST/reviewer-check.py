"""Fresh independent OFFLINE review. Never imports/runs launch/audit/control or Julia.
Actual new analysis/evidence pure functions operate on generated TOML only.
Runtime findings execute AST-extracted validation predicates on in-memory data;
checks_for, audit, old checkers, process/lock/reservation APIs are never called.
"""
from pathlib import Path
import ast,copy,hashlib,json,math,os,struct,sys,tempfile,tomllib,time
D=Path(__file__).resolve().parent;R=D.parents[3];C=R/'diagnostics/direct-bg-export-specialized/reproduce'
checks={};repros={};details={}
def ck(name,value):checks[name]=bool(value)
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def rd(p):return json.loads(Path(p).read_text())
def refuses(fn):
 try:fn();return False
 except (ValueError,RuntimeError,KeyError,TypeError,IndexError,FileNotFoundError):return True
def require(v,m):
 if not v:raise ValueError(m)
pins=rd(D/'preparation-pins.json')['sha256'];paths=rd(D/'required-paths.json')['paths']
ck('exact_2569_pin_membership',len(pins)==len(paths)==len(set(paths))==2569 and set(paths)==set(pins))
for p,h in pins.items():ck('pin:'+p,sha(p)==h)
details['primary_binding_count']=len(pins)+1;details['pins_sha256']=sha(D/'preparation-pins.json')
for n in ['runs','outers']:ck('no_operational_'+n,not (D/n).exists())
# Complete source inverses, reconstructed here without executing generators.
inv=rd(C/'source-inverse.json')
for n,v in inv['files'].items():
 text=(C/(n+'.jl')).read_text();ck('candidate_hash:'+n,sha(C/(n+'.jl'))==v['candidate_sha256'])
 for edit in reversed(v['edits']):
  ck('candidate_edit_once:'+n+':'+edit['before'],text.count(edit['after'])==1);text=text.replace(edit['after'],edit['before'])
 for old,new in inv['rename'].items():text=text.replace(new,old)
 ck('candidate_full_inverse:'+n,text==Path(v['source']).read_text() and sha(v['source'])==v['source_sha256'])
pi=rd(D/'probe-inverse.json');st=rd(D/'stages.json')['cost'];stage=Path(st['path']);seed=Path(pi['seed'])
actual={str(p.relative_to(stage)) for p in stage.rglob('*') if p.is_file()}
ck('stage_exact_87',actual==set(st['sha256']) and len(actual)==87 and not any(p.is_symlink() for p in stage.rglob('*')))
for n,h in st['sha256'].items():ck('stage_hash:'+n,sha(stage/n)==h)
for n,edits in pi['edits'].items():
 p=D/('probe-'+n+'.jl');text=p.read_text();ck('probe_stage:'+n,text==(stage/'src'/('_bgxsp_'+n+'.jl')).read_text())
 if n=='workspace':ck('probe_header_once',text.startswith(pi['header']));text=text.removeprefix(pi['header'])
 for old,new,count in reversed(edits):ck('probe_edit:'+n+':'+old,text.count(new)==count);text=text.replace(new,old)
 for old,new in reversed(pi['rename']):text=text.replace(new,old)
 ck('probe_full_inverse:'+n,text==(C/(n+'.jl')).read_text())
seedfiles={str(p.relative_to(seed)) for p in seed.rglob('*') if p.is_file()};ck('seed_83',len(seedfiles)==83)
for n in seedfiles:
 text=(stage/n).read_bytes()
 if n=='src/JSimplex.jl':text=text.replace(pi['stage_addition'].encode(),b'')
 ck('green_stage_preserved:'+n,text==(seed/n).read_bytes())
O=D.with_name('DIRECT-BG-EXPORT-WORKSPACE-COST-PREPARATION')
renames=[('_BGXBuildOwner','_BGXSBuildOwner'),('BGExport','BGSpecializedExport'),('_bgx_','_bgxs_'),('_BGXPBuildOwner','_BGXSPBuildOwner'),('BGProbeExport','BGSpecializedProbeExport'),('_bgxp_','_bgxsp_')]
for n in ['cost.jl','probe.jl','clone_source.py']:
 text=(O/n).read_text()
 for old,new in renames:text=text.replace(old,new)
 ck('old_namespace_inverse:'+n,text==(D/n).read_text())
for n in ['inputs.json','inputs.toml','analysis.py','evidence.py']:ck('old_byte_exact:'+n,(O/n).read_bytes()==(D/n).read_bytes())
for n,v in rd(D/'reused-files.json').items():ck('reused:'+n,sha(D/n)==sha(v['path'])==v['sha256'])
for label,root in [('diagnostic',R),('production',Path('/home/jspitz/.codex/worktrees/native-pivot-production-integration/JSimplex.jl'))]:
 for n,h in rd(D/'baseline.json')[label].items():ck('baseline:'+label+':'+n,sha(root/n)==h)
G=D.with_name('DIRECT-BG-EXPORT-SPECIALIZATION-GC-DRIVER');gr=G/'runs/greengc300';review=rd(gr/'result-review.json');closure=rd(gr/'outer-closure.json')
ck('green_receipt',review['accepted'] is True and review['findings']==[] and review['scope']=='BG specialization GC GREEN result' and review['assertions']==8640)
ck('green_bindings_exact',set(review['sha256'])=={str(p) for p in gr.rglob('*') if p.is_file() and p.name!='result-review.json'} and len(review['sha256'])==81 and len(review['evidence_sha256'])==24 and len(closure['sha256'])==8)
for label,bindings in [('green',review['sha256']),('green_evidence',review['evidence_sha256']),('green_closure',closure['sha256'])]:
 for p,h in bindings.items():ck(label+':'+p,sha(p)==h)
ck('green_outcome_link',rd(G/'outers/greengc300/outer-outcome.json')['identity']==closure['outer_identity'])
ck('265_prior_groups',len(rd(D/'host-entry.json')['groups'])==265 and set(closure['host']['groups'])<=set(rd(D/'host-entry.json')['groups']))
details.update(green_run_bindings=81,green_evidence_bindings=24,green_closure_bindings=8)
# Independent input representation and every stored CSC/step transition.
inputs=rd(D/'inputs.json');ck('json_toml_same_inputs',inputs==tomllib.loads((D/'inputs.toml').read_text()))
fixtures=inputs['fixtures'];ck('four_fixed_fixtures',[(f['name'],f['n']) for f in fixtures]==[('sparse32',32),('dense32',32),('sparse96',96),('dense96',96)])
num=lambda t:struct.unpack('>d',bytes.fromhex(t))[0]
for f in fixtures:
 ck('fixture_shapes:'+f['name'],len(f['matrices'])==9 and len(f['steps'])==8)
 mats=[]
 for i,m in enumerate(f['matrices']):
  n=m['n'];cols=[];valid=n==f['n'] and len(m['colptr'])==n+1 and m['colptr'][0]==1 and m['colptr'][-1]==len(m['nzval'])+1==len(m['rowval'])+1
  for j in range(n):
   lo,hi=m['colptr'][j]-1,m['colptr'][j+1]-1;ids=m['rowval'][lo:hi]
   valid &= lo<=hi and ids==sorted(set(ids)) and all(type(k) is int and 1<=k<=n for k in ids)
   col=['0000000000000000']*n
   for k,t in zip(ids,m['nzval'][lo:hi]):col[k-1]=t;valid &= len(t)==16 and math.isfinite(num(t))
   cols.append(col)
  ck('input_canonical:'+f['name']+':'+str(i),valid);mats.append(cols)
 for i,s in enumerate(f['steps']):
  expected=copy.deepcopy(mats[i]);expected[s['j']-1]=s['a']
  ck('input_transition:'+f['name']+':'+str(i),expected==mats[i+1] and all(len(s[k])==f['n'] and all(math.isfinite(num(v)) for v in s[k]) for k in ['a','dse','unit']))
# Load only new pure definitions, no protocol/control imports.
sys.path.insert(0,str(D));import analysis as a,evidence as e
# Extract actual runtime guard predicates rather than importing operational auditor.
source=ast.parse((D/'audit.py').read_text());fn=next(x for x in source.body if isinstance(x,ast.FunctionDef) and x.name=='checks_for')
predicates={}
for node in ast.walk(fn):
 if isinstance(node,ast.Call) and isinstance(node.func,ast.Name) and node.func.id=='require' and len(node.args)>1 and isinstance(node.args[1],ast.Constant):
  predicates[node.args[1].value]=compile(ast.Expression(node.args[0]),str(D/'audit.py'),'eval')
def pred(name,**vals):return eval(predicates[name],dict(math=math,sys=sys,Path=Path),vals)
valid_p=dict(returncode=0,reason='exit0',terminal_memory=dict(available_kib=7000000,swap_used_kib=0));valid_sup=dict(returncode=0,accepted=True,soft_timeout=False,hard_timeout=False,child_kill=False,guard_term=False,guard_kill=False)
ck('runtime_valid_exit',pred('Exact exit',p=valid_p,sup=valid_sup))
for label,p,sup in [('process_boolean_exit',dict(valid_p,returncode=False),valid_sup),('supervisor_boolean_exit',valid_p,dict(valid_sup,returncode=False)),('contradictory_hard_timeout_success',valid_p,dict(valid_sup,hard_timeout=True)),('contradictory_soft_timeout_success',valid_p,dict(valid_sup,soft_timeout=True))]:
 repros[label]=dict(rejected=not pred('Exact exit',p=p,sup=sup),predicate='Exact exit',mutation=p if label.startswith('process') else sup)
for label,z in [('infinite_available',dict(available_kib=float('inf'),swap_used_kib=0)),('negative_swap',dict(available_kib=7000000,swap_used_kib=-1)),('negative_infinite_swap',dict(available_kib=7000000,swap_used_kib=-float('inf'))),('boolean_swap',dict(available_kib=7000000,swap_used_kib=False))]:
 repros[label]=dict(rejected=not pred('Resource limit',resources=[z],p=valid_p),predicate='Resource limit',mutation=z)
tp=dict(reason='wall_time',returncode=-15,pins_unchanged=True);ts=dict(returncode=1,hard_timeout=False,child_kill=False,guard_term=False,guard_kill=False)
ck('timeout_nominal',e.timeout_ok(tp,dict(ts,soft_timeout=False,accepted=False),'BEGIN BG export workspace cost cost1-300',292.,300))
for label,sup in [('timeout_missing_soft_and_accepted',ts),('timeout_contradictory_soft_timeout',dict(ts,soft_timeout=True,accepted=False)),('timeout_accepted_true',dict(ts,soft_timeout=False,accepted=True))]:
 repros[label]=dict(rejected=not e.timeout_ok(tp,sup,'BEGIN BG export workspace cost cost1-300',292.,300),predicate='timeout_ok',mutation=sup)
# Actual TOML parser and live exact residuals on generated tiny complete records.
def tok(x):return struct.pack('>d',x).hex()
one=tok(1.);zero=tok(0.)
fx=[dict(name=name,n=1,matrices=[dict(n=1,colptr=[1,2],rowval=[1],nzval=[one]) for _ in range(9)],steps=[dict(j=1,a=[one],dse=[one],unit=[one]) for _ in range(8)]) for name in ['sparse32','dense32','sparse96','dense96']]
countnames='allocation_requests requested_payload factorizations extractions orientation_solves orientation_products triangle_checks permutation_checks normalized_stores raw_stores fallback_stores index_stores refactor_entries'.split()
def counts(**kwargs):return {k:kwargs.get(k,0) for k in countnames}
cache=dict(present=False,dimension=0,charge=0,limit=0,seen_bytes=0,orientation_bytes=0,graph_bytes=0)
controls=dict(complete=True,inputs_unchanged=True,orientation_synthetic_calls=1,orientation_requests=2,orientation_payload=64,constructions=4,copies=4,refactors=12,explicit_solves=0,imports=[dict(name=name,correct=True,u=6,counts=counts(normalized_stores=n,raw_stores=r,fallback_stores=f,index_stores=6)) for name,n,r,f in [('normalize_false',0,6,0),('reject_first',1,0,6),('reject_last',4,0,6)]],transitions=[dict(backend=b,constructions=2,copies=2,refactors=6,explicit_solves=0,states=[dict(name=n,cache=cache,graphs=[100,100],coexistence_graph=400) for n in ['same_shape','large_to_small']],copy_cache=cache) for b in ['native','markowitz']])
def probe():
 states=[];nf=1
 for k,b in [(0,False)]+[(k,b) for k in range(1,9) for b in ([False,True] if k in (4,8) else [False])]:
  nf+=int(b);states.append(dict(step=k,refactored=b,equal=True,graphs=[100,100,100],cache=cache,probe_cache=cache,counts=counts(factorizations=nf,extractions=nf,refactor_entries=nf-1),coexistence_graph_peak=400))
 return dict(inputs_unchanged=True,constructions=3,refactors=6,updates=24,ftran=48,btran=24,copies=0,states=states,outputs=[[[one] for _ in range(24)] for _ in range(3)],counts=states[-1]['counts'],coexistence_graph_peak=400,cache_charge_sum=0,cache_charge_peak=0)
def preflight(b):
 pol='threshold_one' if b=='native' else 'default';v=[zero]*20;v[3]=one;q=dict(kind=b,policy=pol,control=v if b=='native' else [],expected_control=v if b=='native' else [],strategy=zero if b=='native' else '')
 return dict(reference=[q]*3,candidate=[q]*3,modes=['normalized']*3,inputs_unchanged=True,constructions=2,refactors=4,explicit_solves=0)
def window(proc,w,b):
 pair=(w+1)//2;order=(w-1)%2+1;side=a.schedule(proc,pair)[order-1]
 return dict(pair=pair,order=order,side=side,measured=pair>3,policy='threshold_one' if b=='native' else 'default',correct=True,inputs_unchanged=True,modes=['normalized']*3,seconds=1. if side=='reference' else .9,bytes=100,events=10,gc_seconds=0.,compile_seconds=0.,recompile_seconds=0.,retained_bytes=100,nested_seconds=[.01]*6,outputs=[[one] for _ in range(24)])
def toml_value(v):
 if isinstance(v,str):return json.dumps(v)
 if type(v) is bool:return 'true' if v else 'false'
 if type(v) in (int,float):return str(v).lower()
 if isinstance(v,list):return '['+', '.join(map(toml_value,v))+']'
 if isinstance(v,dict):return '{'+', '.join(json.dumps(k)+' = '+toml_value(x) for k,x in v.items())+'}'
 raise TypeError(type(v))
def dump_toml(p,v):p.write_text('\n'.join(json.dumps(k)+' = '+toml_value(x) for k,x in v.items())+'\n')
with tempfile.TemporaryDirectory(prefix='bgxs-reviewer-pure-') as temp:
 root=Path(temp);out=root/'runs/cost1-300/output';out.mkdir(parents=True);(root/'inputs.json').write_text(json.dumps(dict(fixtures=fx)));(root/'loaded-paths.json').write_text('{}')
 cfg=dict(phase='cost1-300',process=1,stage='/synthetic/stage');data={'controls.toml':controls};base=['pins.json','current.json','process.json','resources.jsonl','run.log']
 for name in base:(out/name).write_text('{}')
 for i in range(1,9):
  b='native' if i%2 else 'markowitz';ident=dict(fixture=fx[(i-1)//2]['name'],manager='BG',backend=b,policy='threshold_one' if b=='native' else 'default')
  data.update({f'started-{i}.toml':ident,f'preflight-{i}.toml':preflight(b),f'probe-{i}.toml':probe(),f'cell-{i}.toml':dict(ident,windows=20)})
  for w in range(1,21):data[f'window-{i}-{w}.toml']=window(1,w,b)
 data['raw.toml']=dict(phase='cost1-300',loaded=dict(JSimplex='/synthetic/stage/src/JSimplex.jl'),completed=True,fatal='',cells=8,windows=160,threads=1,blas_threads=1)
 for name,v in data.items():dump_toml(out/name,v)
 rows,totals=e.output_checks(out,cfg);ck('complete_real_TOML_live_residuals',totals==dict(cells=8,windows=160,window_outputs=3840,probe_outputs=576));ck('first_all8_gates',a.first_process_viable(dict(all_passed=True,pure_timeout=False,cells=rows),fx))
 # Each malformed mutation is injected separately into an otherwise accepted complete schedule.
 mutations=[('probe_infinite_graph','probe-1.toml',lambda v:(v.update(coexistence_graph_peak=float('inf')),[s.update(coexistence_graph_peak=float('inf')) for s in v['states']])),('probe_boolean_copies','probe-1.toml',lambda v:v.update(copies=False)),('probe_float_constructions','probe-1.toml',lambda v:v.update(constructions=3.0)),('probe_unknown_key','probe-1.toml',lambda v:v.update(unrecognized=True)),('probe_boolean_step','probe-1.toml',lambda v:v['states'][0].update(step=False)),('control_boolean_call','controls.toml',lambda v:v.update(orientation_synthetic_calls=True)),('control_infinite_graph','controls.toml',lambda v:v['transitions'][0]['states'][0].update(coexistence_graph=float('inf'))),('control_unknown_key','controls.toml',lambda v:v.update(unrecognized=True)),('raw_integer_completed','raw.toml',lambda v:v.update(completed=1)),('cell_float_window_count','cell-1.toml',lambda v:v.update(windows=20.0))]
 for label,name,mutate in mutations:
  v=copy.deepcopy(data[name]);mutate(v);dump_toml(out/name,v);repros[label]=dict(rejected=refuses(lambda:e.output_checks(out,cfg)),predicate='output_checks live full TOML/exact residuals',file=name);dump_toml(out/name,data[name])
 for label,name,key,val in [('compile','window-1-7.toml','compile_seconds',.001),('boolean_events','window-1-1.toml','events',True),('changed_solution','window-8-20.toml','outputs',[[tok(2.)]]*24),('wrong_raw_thread','raw.toml','threads',True)]:
  v=copy.deepcopy(data[name]);v[key]=val;dump_toml(out/name,v);ck('reject_known:'+label,refuses(lambda:e.output_checks(out,cfg)));dump_toml(out/name,data[name])
 order=['controls.toml']+[name for i in range(1,9) for name in [f'started-{i}.toml',f'preflight-{i}.toml',f'probe-{i}.toml']+[f'window-{i}-{w}.toml' for w in range(1,21)]+[f'cell-{i}.toml']]
 for name in data:(out/name).unlink()
 for length in range(len(order)):
  if length:dump_toml(out/order[length-1],data[order[length-1]])
  ck('legal_partial_live:'+str(length),not refuses(lambda:e.output_checks(out,cfg,partial=True)))
 # Complete reverse-order schedule, same arithmetic oracle and all raw samples.
 for name,v in data.items():
  if name.startswith('window-'):
   _,i,w=name.removesuffix('.toml').split('-');v=window(2,int(w),'native' if int(i)%2 else 'markowitz')
  elif name=='raw.toml':v=dict(v,phase='cost2-300')
  dump_toml(out/name,v)
 reverse,_=e.output_checks(out,dict(cfg,phase='cost2-300',process=2));ck('reversed_complete_gates',all(a.qualify(x['statistics'],y['statistics']) for x,y in zip(rows,reverse)))
for label,v in repros.items():ck('malformed_refused:'+label,v['rejected'])
# Source-level schedule and safeguards. No runtime measurement is inferred.
s=(D/'cost.jl').read_text();ck('untimed_probe_and_no_explicit_GC','GC.gc' not in s and '_bgxsp_' not in s and 'include("probe.jl")' in s)
ck('symmetric_result_capture',s.count('timed=@timed lifecycle')==1 and 'factor,clocks,modes=timed.value' in s and 'retained=Base.summarysize(factor)' in s)
for n in ['control.py','audit.py','launch.py','outer.py','seal.py','post-return.py','supervisor.py','guard.py','evidence.py','analysis.py','clone_source.py','prepare.py','prepare-protocol.py','prepare-manifest.py']:
 ast.parse((D/n).read_text());ck('python_ast:'+n,True)
details['schedule']=dict(timed_windows=160,measured_windows=112,constructors=204,refactors=412,updates=1472,ftran=2944,btran=1472,copies=4,synthetic_orientation=1,importer_controls=3)
details['limitations']=['No Julia/parser/import/compile/numerics or operational scripts executed.','Runtime tests extract real audit predicates; no operational checks_for/audit function executes.','Generated complete and prefix evidence tests use real TOML decoding and live exact residuals on 1x1 synthetic identity matrices.','No timing/GC/native allocation/code-size/dispatch result established.']
result=dict(all_passed=all(checks.values()),checks=checks,failures=[k for k,v in checks.items() if not v],reproductions=repros,details=details,sha256={str(p):sha(p) for p in [D/'reviewer-check.py',D/'preparation-pins.json']},time=time.time())
with (D/'reviewer-check.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
print(json.dumps(dict(all_passed=result['all_passed'],checks=len(checks),failures=result['failures'],primary_bindings=details['primary_binding_count'],green_bindings=[81,24,8])))
