"""Independent pure-Python saved-data/admission predicate tests.
Imports only definitions from analysis/evidence/control/guard; never invokes any
launcher, auditor, seal, host/process utility, or existing author test/checker.
Synthetic data intentionally exercises schemas without solving frozen fixtures.
"""
from pathlib import Path
import copy,json,math,struct,tempfile,hashlib,traceback
from unittest.mock import patch
import analysis as a
import evidence as e
import control as c
E=Path(__file__).resolve().parent
checks={};notes={}
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def need(v,n):
 checks[n]=bool(v)
 if not v:raise AssertionError(n)
def rejects(n,call):
 try:call()
 except (ValueError,RuntimeError,KeyError,TypeError,IndexError,FileNotFoundError):checks[n]=True
 else:need(False,n)
def enc(v):
 if type(v) is bool:return str(v).lower()
 if isinstance(v,str):return json.dumps(v)
 if isinstance(v,dict):return '{'+', '.join(enc(k)+' = '+enc(x) for k,x in v.items())+'}'
 if isinstance(v,list):return '['+', '.join(enc(x) for x in v)+']'
 return repr(v)
def toml(v):return '\n'.join(enc(k)+' = '+enc(x) for k,x in v.items())+'\n'
def write(p,v):Path(p).write_text(json.dumps(v,indent=2)+'\n')
def tok(x):return struct.pack('>d',x).hex()
def counters():return {k:0 for k in json.loads((E/'probe-inverse.json').read_text())['counts']}
def storage(n=2,C=0,R=0,K=0,S=0,D=0,live=0,cap0=0):
 top='values row_ids row_backs slab start capacity count column prev next row_order row_position column_order column_position column_head column_tail rows gap_first gap_length bins scratch_value scratch_row scratch_back'.split()
 arr=[]
 def add(name,length,width):arr.append(dict(name=name,length=length,element_bytes=width,backing_length=length,backing_bytes=length*width,graph_bytes=40+length*width))
 for key in top:
  if key in ['values','row_ids','row_backs']:length,width=D,8
  elif key in ['slab','start','capacity','count','column','prev','next']:length,width=K,4
  elif key=='rows':length,width=n,8
  elif key=='bins':length,width=32,4
  elif key.startswith('scratch'):length,width=33,8 if key=='scratch_value' else 4
  else:length,width=n,4
  add(key,length,width)
 for i in range(1,S+1):
  for key,width in [('values',8),('row_ids',4),('row_backs',4)]:add(f'{key}[{i}]',C//S,width)
 for i in range(1,n+1):add(f'rows[{i}]',cap0 if i==1 else 0,4)
 return dict(C=C,R=R,K=K,S=S,D=D,used=live,live=live,live_blocks=live,free_capacity=0,gap_reserve=R-live,core_payload=16*C+4*R+28*K+32*n+656,outer_pointer_payload=8*n+24*D,struct_bytes=216,graph_bytes=216+sum(x['graph_bytes'] for x in arr),arrays=arr)
def growth():
 states=[];cap=0;g=0;copied=0;maxco=0
 for i in range(1,65):
  if i>cap:
   old=cap;cap=i+min(8,max(1,old//8));g+=1;copied+=4*(i-1);maxco=max(maxco,4*(old+cap))
  ct=counters();ct.update(row_growths=g,row_copied_bytes=copied,row_coexist_payload=maxco)
  states.append(dict(insertions=i,row_capacity=cap,counts=ct))
 return dict(complete=True,n=64,insertions=64,factorizations=0,solves=0,states=states,storage=storage(64,C=2048,R=cap,K=64,S=8,D=8,live=64,cap0=cap),counts=ct)
def fixture(name):
 m=dict(n=2,colptr=[1,2,3],rowval=[1,2],nzval=[tok(1.),tok(1.)])
 s=dict(j=1,a=[tok(1.),tok(0.)],dse=[tok(2.),tok(3.)],unit=[tok(1.),tok(0.)])
 return dict(name=name,n=2,matrices=[copy.deepcopy(m) for _ in range(9)],steps=[copy.deepcopy(s) for _ in range(8)])
fixtures=[fixture(n) for n in ['sparse32','dense32','sparse96','dense96']]
def outputs(f):return [s[k] for s in f['steps'] for k in ['a','dse','unit']]
def row(f,process,pair,order,backend='native'):
 side=a.schedule(process,pair)[order-1]
 return dict(pair=pair,order=order,side=side,measured=pair>3,policy='threshold_one' if backend=='native' else 'default',correct=True,inputs_unchanged=True,modes=['normalized']*3,seconds=1. if side=='reference' else .9,bytes=100,events=2,gc_seconds=0.,compile_seconds=0.,recompile_seconds=0.,retained_bytes=10000,nested_seconds=[.01]*6,outputs=copy.deepcopy(outputs(f)))
def preflight(backend):
 values=[tok(0.)]*20;values[3]=tok(1.)
 item=dict(kind=backend,policy='threshold_one' if backend=='native' else 'default',control=values if backend=='native' else [],expected_control=values if backend=='native' else [],strategy=tok(0.) if backend=='native' else '')
 return dict(reference=[copy.deepcopy(item) for _ in range(3)],candidate=[copy.deepcopy(item) for _ in range(3)],modes=['normalized']*3,inputs_unchanged=True,constructions=2,refactors=4,explicit_solves=0)
def probe(f):
 states=[]
 for k,r in [(0,False)]+[(k,r) for k in range(1,9) for r in ([False,True] if k in (4,8) else [False])]:states.append(dict(step=k,refactored=r,equal=True,graphs=[10000]*3,storage=storage(),history_length=0 if r or k==0 else (k-1)%4+1,counts=counters()))
 return dict(states=states,outputs=[copy.deepcopy(outputs(f)) for _ in range(3)],inputs_unchanged=True,constructions=3,refactors=6,updates=24,ftran=48,btran=24,copies=0,counts=counters())
def audit_record():
 cells=[]
 for f in fixtures:
  for b in ['native','markowitz']:cells.append(dict(fixture=f['name'],manager='BG',backend=b,policy='threshold_one' if b=='native' else 'default',statistics=dict(time_median_gate=True,allocation_gate=True,memory_gate=True,probe_memory_gate=True,faster_pairs=5)))
 return dict(all_passed=True,pure_timeout=False,cells=cells)
def main():
 f=fixtures[0];ms=[(a.matrix(m),a.matrix(m,True)) for m in f['matrices']]
 need(a.window_ok(row(f,1,4,1),f,1,4,1,ms),'valid_measured_window')
 for key,val in [('compile_seconds',.0001),('recompile_seconds',.0001),('bytes',True),('events',2.),('retained_bytes',-1),('seconds',float('nan')),('correct',False),('inputs_unchanged',False),('policy','bad')]:
  rr=row(f,1,4,1);rr[key]=val
  # Policy is bound by output_checks cell identity, not window_ok alone.
  if key!='policy':rejects('window_refuses_'+key,lambda rr=rr:a.window_ok(rr,f,1,4,1,ms))
 rr=row(f,1,1,1);rr['compile_seconds']=.1;need(a.window_ok(rr,f,1,1,1,ms),'warm_compilation_recorded_allowed')
 for n,s in [('token_short','0'),('token_uppercase','3FF0000000000000'),('token_inf','7ff0000000000000'),('token_nan','7ff8000000000000')]:rejects(n,lambda s=s:a.number(s))
 need(a.number(tok(-0.))==0. and tok(-0.)!=tok(0.),'signed_zero_numerical_equal_bits_distinct')
 mm=dict(n=2,colptr=[1,2,4],rowval=[1,1,2],nzval=[tok(1.),tok(2.),tok(1.)])
 need(a.residual(a.matrix(mm),[tok(3.),tok(4.)],[tok(11.),tok(4.)]),'exact_asymmetric_forward')
 need(a.residual(a.matrix(mm,True),[tok(3.),tok(4.)],[tok(3.),tok(10.)]),'exact_asymmetric_transpose')
 need(not a.residual(a.matrix(mm),[tok(3.),tok(4.)],[tok(3.),tok(10.)]),'transpose_not_forward_norm_or_matrix')
 s=storage();need(e.storage_ok(s,2),'complete_empty_storage_schema')
 for label,fn in [('backing_under_length',lambda x:x['arrays'][0].update(length=1)),('backing_wrong_bytes',lambda x:x['arrays'][0].update(backing_bytes=8)),('missing_row',lambda x:x['arrays'].pop()),('Int_overflow',lambda x:x.update(C=2**63)),('handle_overflow',lambda x:x.update(K=2**26)),('bool_capacity',lambda x:x.update(C=True)),('wrong_payload',lambda x:x.update(core_payload=0)),('wrong_outer_payload',lambda x:x.update(outer_pointer_payload=0))]:
  ss=copy.deepcopy(s);fn(ss);rejects('storage_'+label,lambda ss=ss:e.storage_ok(ss,2))
 cc=counters();need(e.counters_ok(cc),'29_zero_counter_schema')
 for k,v in [('splits',1),('merge_stage_reads',1),('row_handle_repairs',1),('allocation_requests',2**63),('gap_moves',True)]:
  cc=counters();cc[k]=v;rejects('counters_'+k,lambda cc=cc:e.counters_ok(cc))
 gg=growth();need(e.growth_ok(gg),'64_growth_rule_and_copy_ledger');notes['growth_terminal']=dict(row_capacity=gg['states'][-1]['row_capacity'],row_growths=gg['counts']['row_growths'],row_copied_bytes=gg['counts']['row_copied_bytes'],row_coexist_payload=gg['counts']['row_coexist_payload'])
 for k in ['row_capacity','counts']:
  bad=copy.deepcopy(gg)
  if k=='row_capacity':bad['states'][4][k]+=1
  else:bad[k]['row_copied_bytes']-=4
  rejects('growth_refuses_'+k,lambda bad=bad:e.growth_ok(bad))
 pr=probe(f);need(e.probe_ok(pr,f,ms),'11_checkpoint_probe')
 for label,fn in [('missing_checkpoint',lambda x:x['states'].pop()),('wrong_step',lambda x:x['states'][4].update(step=8)),('history_after_refactor',lambda x:x['states'][5].update(history_length=4)),('unequal_signed_zero',lambda x:x['outputs'][1][0].__setitem__(1,tok(-0.))),('wrong_count',lambda x:x.update(ftran=47)),('counter_decreases',lambda x:x['states'][0]['counts'].update(gap_moves=1))]:
  bad=copy.deepcopy(pr);fn(bad);rejects('probe_'+label,lambda bad=bad:e.probe_ok(bad,f,ms))
 rows=[row(f,1,p,o) for p in range(1,11) for o in [1,2]];st=a.summarize(rows)
 need(st['time_median_gate'] and st['allocation_gate'] and st['memory_gate'] and st['faster_pairs']==7,'all_seven_measured_pair_gates')
 bad=copy.deepcopy(rows);bad[-1]['retained_bytes']=11001;need(a.summarize(bad)['memory_gate'] is False,'every_final_memory_pair_gate')
 bad=copy.deepcopy(rows)
 for rr in bad:
  if rr['side']=='candidate':rr['bytes']=101
 need(a.summarize(bad)['allocation_gate'] is False,'bytes_not_hidden_by_equal_events')
 bad=copy.deepcopy(st);bad['faster_pairs']=2;need(not a.qualify(st,bad),'combined_9_of14_refused');bad['faster_pairs']=3;need(a.qualify(st,bad),'combined_10_of14_accepted')
 first=audit_record();need(a.first_process_viable(first,fixtures),'first_all_eight_viable')
 for cell in range(8):
  for k in ['time_median_gate','allocation_gate','memory_gate','probe_memory_gate']:
   bad=copy.deepcopy(first);bad['cells'][cell]['statistics'][k]=False;need(not a.first_process_viable(bad,fixtures),f'first_cell{cell+1}_{k}_refused')
 for label,fn in [('faster2',lambda x:x['cells'][0]['statistics'].update(faster_pairs=2)),('bool_faster',lambda x:x['cells'][0]['statistics'].update(faster_pairs=True)),('missingcell',lambda x:x['cells'].pop()),('wrongpolicy',lambda x:x['cells'][0].update(policy='default')),('reordered',lambda x:x['cells'].reverse()),('timeout',lambda x:x.update(pure_timeout=True)),('badintegrity',lambda x:x.update(all_passed=False))]:
  bad=copy.deepcopy(first);fn(bad);need(not a.first_process_viable(bad,fixtures),'first_'+label)
 p=dict(reason='wall_time',returncode=-15,pins_unchanged=True);sup=dict(returncode=1,hard_timeout=False,child_kill=False,guard_term=False,guard_kill=False)
 need(e.timeout_ok(p,sup,'BEGIN matched policy cost cost1-300',293,300),'pure_inner_timeout_predicate')
 for marker in ['WARNING:','Warning:','world age','FATAL COST:','ERROR:','Traceback','Measured compilation; stop','TEST FAILURE:']:
  need(not e.timeout_ok(p,sup,'BEGIN matched policy cost cost1-300\n'+marker,293,300),'timeout_refuses_'+marker)
 for key in ['hard_timeout','child_kill','guard_term','guard_kill']:
  bad=dict(sup);bad[key]=True;need(not e.timeout_ok(p,bad,'BEGIN matched policy cost cost1-300',293,300),'timeout_'+key)
 need(not e.timeout_ok(p,sup,'BEGIN matched policy cost cost1-300',301,300),'late_cleanup_refused')
 # Full 199-file parser and prefix schema, with local synthetic fixtures only.
 with tempfile.TemporaryDirectory(prefix='block-review-predicates-') as tmp:
  out=Path(tmp);cfg=dict(phase='cost1-300',process=1,stage='/synthetic-stage')
  for name in e.BASE:(out/name).write_text('{}\n')
  (out/'growth.toml').write_text(toml(growth()))
  for cell,(ff,b) in enumerate([(ff,b) for ff in fixtures for b in ['native','markowitz']],1):
   identity=dict(fixture=ff['name'],manager='BG',backend=b,policy='threshold_one' if b=='native' else 'default')
   for key,value in [('started',identity),('preflight',preflight(b)),('probe',probe(ff)),('cell',dict(identity,windows=20))]:(out/f'{key}-{cell}.toml').write_text(toml(value))
   for w in range(1,21):(out/f'window-{cell}-{w}.toml').write_text(toml(row(ff,1,(w+1)//2,1+(w-1)%2,b)))
  raw=dict(phase=cfg['phase'],loaded=c.loaded_for(cfg),completed=True,fatal='',cells=8,windows=160,threads=1,blas_threads=1);(out/'raw.toml').write_text(toml(raw))
  oldrd=e.rd
  def rd(p):return {'fixtures':fixtures} if Path(p).name=='inputs.json' else oldrd(p)
  with patch.object(e,'rd',rd):
   got,count=e.output_checks(out,cfg);need(len(got)==8 and count==dict(cells=8,windows=160,exact_residuals=4416),'full199files_160windows_4416residuals')
   def mutate(name,change,label):
    target=out/name;original=target.read_text();data=e.tomllib.loads(original);change(data);target.write_text(toml(data))
    try:rejects(label,lambda:e.output_checks(out,cfg))
    finally:target.write_text(original)
   mutate('raw.toml',lambda x:x['loaded'].update(Test='/extra/Test.jl'),'extra_Test_loaded_refused')
   mutate('raw.toml',lambda x:x['loaded'].pop('TOML'),'missing_loaded_refused')
   mutate('raw.toml',lambda x:x['loaded'].update(JSimplex='/wrong'),'wrong_loaded_refused')
   mutate('window-1-2.toml',lambda x:x['outputs'][0].__setitem__(1,tok(-0.)),'completed_pair_signed_zero_refused')
   mutate('window-1-1.toml',lambda x:x.update(policy='default'),'window_wrong_policy_refused')
   mutate('preflight-1.toml',lambda x:x['candidate'][0]['control'].__setitem__(3,tok(.1)),'native_wrong_actual_controls_refused')
   mutate('window-1-8.toml',lambda x:x.update(compile_seconds=.01),'measured_compile_output_refused')
   mutate('cell-1.toml',lambda x:x.update(windows=19),'incomplete_cell_refused')
   (out/'unknown').write_text('x');rejects('unexpected_output_refused',lambda:e.output_checks(out,cfg));(out/'unknown').unlink()
   rejects('complete_output_not_pure_timeout',lambda:e.output_checks(out,cfg,partial=True))
   keep=e.BASE|{'growth.toml','started-1.toml','preflight-1.toml','probe-1.toml','window-1-1.toml','window-1-2.toml'}
   for path in out.iterdir():
    if path.name not in keep:path.unlink()
   got,count=e.output_checks(out,cfg,partial=True);need(count==dict(cells=0,windows=2,exact_residuals=120),'partial_complete_pair_and_probe_checked')
   target=out/'window-1-2.toml';dd=e.tomllib.loads(target.read_text());dd['outputs'][0][1]=tok(-0.);target.write_text(toml(dd));rejects('partial_pair_signed_zero_refused',lambda:e.output_checks(out,cfg,partial=True))
 # Exact review binding and process predecessor admission with synthetic files.
 def bindreview(run,filename,scope,phase):
  files={str(p):sha(p) for p in run.rglob('*') if p.is_file() and p!=run/filename}
  write(run/filename,dict(accepted=True,findings=[],scope=scope,phase=phase,sha256=files))
 def with_predecessor(phase,first=None,timeout=None,change=None):
  with tempfile.TemporaryDirectory(prefix='block-review-admission-') as tmp:
   root=Path(tmp);D=root/'DIRECT-BG-BLOCK-COST-PREPARATION';D.mkdir();G=root/'DIRECT-BG-BLOCK-DRIVER-PREPARATION/runs/green300';G.mkdir(parents=True)
   write(D/'lineage.json',{'sha256':{}});write(D/'stages.json',{'cost':{'path':'/synthetic-stage'}});write(D/'inputs.json',{'fixtures':fixtures})
   write(G/'audit.json',{'all_passed':True});write(G/'launch-pins.json',{});write(G/'posthost.json',{'groups':[100]});bindreview(G,'result-review.json','block BG GREEN result','green300')
   with patch.object(c,'D',D),patch.object(c.guard,'pins_match',lambda _:True):
    if first is not None:
     P=D/'runs/cost1-300';P.mkdir(parents=True);write(P/'audit.json',first);write(P/'sealed.json',{});write(P/'posthost.json',{'groups':[101]});bindreview(P,'result-review.json','block BG matched cost result','cost1-300')
    if timeout is not None:
     prev=phase[:-3]+'300';P=D/'runs'/prev;P.mkdir(parents=True,exist_ok=True);write(P/'audit.json',timeout);write(P/'sealed.json',{'config':c.config(prev)});write(P/'posthost.json',{'groups':[102]});bindreview(P,'timeout-review.json','pure timeout result',prev)
    if change:change(D)
    return c.predecessor(phase)
 need(bool(with_predecessor('cost1-300')[0]),'first_admission_GREEN_bound')
 rejects('second_without_first_refused',lambda:with_predecessor('cost2-300'))
 need(bool(with_predecessor('cost2-300',first=audit_record())[0]),'second_after_all8_first_success')
 bad=audit_record();bad['cells'][7]['statistics']['allocation_gate']=False
 rejects('second_after_eighth_cell_failure_refused',lambda:with_predecessor('cost2-300',first=bad))
 need(bool(with_predecessor('cost1-600',timeout={'all_passed':False,'pure_timeout':True})[0]),'explicit_pure_timeout_extension')
 rejects('extension_mixed_failure_refused',lambda:with_predecessor('cost1-600',timeout={'all_passed':False,'pure_timeout':False}))
 rejects('extension_success_relabel_refused',lambda:with_predecessor('cost1-600',timeout={'all_passed':True,'pure_timeout':True}))
 need(bool(with_predecessor('cost2-600',first=audit_record(),timeout={'all_passed':False,'pure_timeout':True})[0]),'second_timeout_requires_both_predecessors')
 rejects('out_of_order_attempt_directory_refused',lambda:with_predecessor('cost1-300',change=lambda d:(d/'runs/cost2-300').mkdir(parents=True)))
 with tempfile.TemporaryDirectory(prefix='block-review-exactbind-') as tmp:
  p=Path(tmp)/'pins.json';write(p,{});f=Path(tmp)/'bound';f.write_text('source');required=[str(p),str(f)]
  rv=dict(accepted=True,findings=[],scope='block BG matched cost preparation',pins_sha256=sha(p),sha256={str(x):sha(x) for x in [p,f]})
  c.verify_review(rv,p,required,rv['scope']);need(True,'exact_review_binding_accepts')
  for label,fn in [('missing',lambda x:x['sha256'].pop(str(f))),('extra',lambda x:x['sha256'].update(extra='0'*64)),('wrongscope',lambda x:x.update(scope='block BG matched cost admission')),('findings',lambda x:x.update(findings=['issue'])),('wrongpins',lambda x:x.update(pins_sha256='0'*64))]:
   bad=copy.deepcopy(rv);fn(bad);rejects('review_'+label,lambda bad=bad:c.verify_review(bad,p,required,rv['scope']))
 notes['definition_imports']=['analysis.py','evidence.py','control.py','guard.py']
 notes['not_executed']=['audit.py','seal.py','launch.py','supervisor.run','guard.run','host inspection','Julia','author tests/checkers']
result={}
try:
 main();result.update(all_passed=True)
except Exception as ex:
 result.update(all_passed=False,error=repr(ex),traceback=traceback.format_exc());raise
finally:
 result.update(checks=checks,notes=notes,checker_sha256=sha(__file__),pins_sha256=sha(E/'preparation-pins.json'),scope='Independent pure offline synthetic schemas, exact residual predicates, and admission refusal controls')
 with (E/'reviewer-predicates-v1.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
 print(json.dumps(dict(all_passed=result['all_passed'],checks=len(checks),notes=notes)))
