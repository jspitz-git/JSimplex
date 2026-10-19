"""Prepare new protocol from accepted isolated-outer protocol plus cost predicates; no operations."""
from pathlib import Path
import ast
D=Path(__file__).resolve().parent;G=D.with_name('DIRECT-BG-EXPORT-SPECIALIZATION-GC-DRIVER');O=D.with_name('DIRECT-BG-EXPORT-WORKSPACE-COST-PREPARATION')
def put(n,s):
 ast.parse(s)
 with (D/n).open('x') as f:f.write(s)
s=(G/'control.py').read_text().replace("ENTRY='ff248544e8f89cc05aecff64806bf60d8b2bd9cf'","ENTRY='7fd611127d3e3366c25ddb531768c3610548f303'")
s=s.replace("def config(phase):", "G=D.with_name('DIRECT-BG-EXPORT-SPECIALIZATION-GC-DRIVER')\nimport importlib.util\n_spec=importlib.util.spec_from_file_location('accepted_gc_control',G/'control.py');gcbase=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(gcbase)\ndef config(phase):",1)
a=s.index('def config(phase):');b=s.index('def verify_review',a)
s=s[:a]+'''def config(phase):
 require(phase in ('cost1-300','cost2-300','cost1-600','cost2-600'),'Unprepared phase')
 stage=rd(D/'stages.json')['cost']['path'];run=D/'runs'/phase;out=run/'output'
 command=['/bin/bash',WRAPPER,'--compiled-modules=existing','--threads=1','--gcthreads=1,0','--heap-size-hint=2G','--history-file=no','--project='+stage,str(D/'cost.jl'),phase,str(out),stage]
 return dict(phase=phase,mode='cost',process=int(phase[4]),seconds=300 if phase.endswith('300') else 600,expected_exit=0,stage=stage,run=str(run),output=str(out),command=command)
'''+s[b:]
a=s.index('def preparation():');b=s.index('def result_review',a)
s=s[:a]+'''def preparation():
 prior=gcbase.preparation();m=D/'preparation-pins.json';j=rd(m)
 require(bindings(j) and set(j['sha256'])==set(rd(D/'required-paths.json')['paths']),'Preparation drift/membership')
 v=rd(D/'review.json');verify_review(v,m,list(j['sha256'])+[str(m)],'BG specialized export cost preparation')
 require(v.get('launch_admitted') is False,'Preparation is not launch admission')
 return sorted(set(prior)|set(j['sha256'])|{str(m),str(D/'review.json')}|set(v.get('evidence_sha256',{})))
'''+s[b:]
a=s.index('def predecessor(phase):');b=s.index('def outer_dir',a)
s=s[:a]+'''def predecessor(phase):
 cfg=config(phase);green='greengc300';run=G/'runs'/green
 files,groups=gcbase.result_review(green,'BG specialization GC GREEN result','result-review.json')
 v=rd(run/'result-review.json');require(bindings(v,'evidence_sha256'),'GREEN review evidence')
 closure=rd(run/'outer-closure.json');gcbase.validate_result_closure(green,closure)
 require(rd(run/'audit.json')['all_passed'] is True and guard.pins_match(rd(run/'sealed.json')),'GREEN not accepted/intact')
 outcome=rd(gcbase.outer_dir(green)/'outer-outcome.json')
 require(outcome['identity']==closure['outer_identity'] and outcome['launched'] is True and outcome['returncode']==0 and outcome['error']=='','GREEN outer outcome')
 files+=list(closure['sha256'])+list(v['evidence_sha256']);groups+=closure['host']['groups']
 if cfg['process']==2:
  from analysis import first_process_viable
  choices=[p for p in ('cost1-300','cost1-600') if (D/'runs'/p/'result-review.json').is_file()]
  require(len(choices)==1,'Exactly one first process')
  f,g=result_review(choices[0],'BG specialized export cost result','result-review.json');a=rd(D/'runs'/choices[0]/'audit.json');cl=rd(D/'runs'/choices[0]/'outer-closure.json');validate_result_closure(choices[0],cl)
  require(first_process_viable(a,rd(D/'inputs.json')['fixtures']),'Stop fixed design: first process performance gates')
  require(guard.pins_match(rd(D/'runs'/choices[0]/'sealed.json')),'First process source drift')
  files+=f+list(cl['sha256']);groups+=g+cl['host']['groups']
 if phase.endswith('600'):
  prev=phase[:-3]+'300';f,g=result_review(prev,'pure timeout result','timeout-review.json');a=rd(D/'runs'/prev/'audit.json');old=config(prev);seal=rd(D/'runs'/prev/'sealed.json');cl=rd(D/'runs'/prev/'outer-closure.json');validate_result_closure(prev,cl)
  require(a['all_passed'] is False and a['pure_timeout'] is True and seal['config']==old and old['command'][:-3]==cfg['command'][:-3] and old['command'][-1]==cfg['command'][-1] and guard.pins_match(seal),'Not unchanged pure timeout')
  files+=f+list(cl['sha256']);groups+=g+cl['host']['groups']
 return sorted(set(files)),sorted(set(groups))
'''+s[b:]
s=s.replace("require(set(v.get('sha256',{}))==set(files) and bindings(v),'Result review membership/bindings')","require(set(v.get('sha256',{}))==set(files) and bindings(v),'Result review membership/bindings')\n if 'evidence_sha256' in v:require(bindings(v,'evidence_sha256'),'Result evidence bindings')")
put('control.py',s)
# Cost saved-data semantics + accepted exact outer/inventory/process protocol.
s=(O/'audit.py').read_text().replace('BG export workspace cost admission','BG specialized export cost admission')
s=s.replace("require(s['phase']==phase", "verify_seal(cfg,s);verify_outer_invocation(phase,s)\n require(str(outer_dir(phase)/'outer-ready.json') in s['files'],'Outer ready not sealed')\n require(s['phase']==phase",1)
s=s.replace("{str(sp),str(rp),str(run/'prehost.json')}","{str(sp),str(rp),str(run/'prehost.json'),str(outer_dir(phase)/'release.json'),str(outer_dir(phase)/'outer-invocation.json')}")
s=s.replace("res=run/'reservation.json';require(","res=run/'reservation.json';require(rd(res).get('one_attempt') is True,'Strict reservation boolean');require(")
put('audit.py',s)
print('New cost protocol saved; syntax checked; no seal/outer/launch/audit executed.')
