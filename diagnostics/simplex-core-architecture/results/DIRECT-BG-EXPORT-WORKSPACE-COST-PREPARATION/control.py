"""Definitions only for a distinct BG export-workspace cost qualification."""
from pathlib import Path
import importlib.util,json,subprocess,sys,os,time
D=Path(__file__).resolve().parent;R=D.parents[3];G=D.with_name('DIRECT-BG-EXPORT-WORKSPACE-GREEN2-PREPARATION')
spec=importlib.util.spec_from_file_location('bgx_green2_control',G/'control.py');base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
require=base.require;rd=base.rd;sha=base.sha;save=base.save;git=base.git;bindings=base.bindings;verify_review=base.verify_review;host_safe=base.host_safe
validate_environment=base.validate_environment;guard=base.guard;MASTER=base.MASTER;W=base.W;C=base.C;WRAPPER=base.WRAPPER

def full_host(extra=()):return base.full_host(list(extra)+rd(G/'runs/green2-300/posthost.json')['groups'])
def validate_sources():
 base.validate_sources()
 for stage in rd(D/'stages.json').values():
  root=Path(stage['path']);require(not root.is_symlink() and not any(p.is_symlink() for p in root.rglob('*')),'Cost stage symlink')
  require({str(p.relative_to(root)) for p in root.rglob('*') if p.is_file()}==set(stage['sha256']) and all(sha(root/n)==h for n,h in stage['sha256'].items()),'Cost stage drift')
def config(phase):
 require(phase in ('cost1-300','cost2-300','cost1-600','cost2-600'),'Unprepared cost phase')
 stage=rd(D/'stages.json')['cost']['path'];run=D/'runs'/phase;out=run/'output'
 command=['/bin/bash',WRAPPER,'--compiled-modules=existing','--threads=1','--gcthreads=1,0','--heap-size-hint=2G','--history-file=no','--project='+stage,str(D/'cost.jl'),phase,str(out),stage]
 return dict(phase=phase,mode='cost',process=int(phase[4]),seconds=300 if phase.endswith('300') else 600,expected_exit=0,stage=stage,run=str(run),output=str(out),command=command)
def loaded_for(cfg):return dict(rd(D/'loaded-paths.json'),JSimplex=str(Path(cfg['stage'])/'src/JSimplex.jl'))
def preparation():
 files=base.preparation();m=D/'preparation-pins.json';j=rd(m)
 require(bindings(j) and set(j['sha256'])==set(rd(D/'required-paths.json')['paths']),'Cost preparation drift/membership')
 verify_review(rd(D/'review.json'),m,list(j['sha256'])+[str(m)],'BG export workspace cost preparation')
 return sorted(set(files)|set(j['sha256'])|{str(m),str(D/'review.json')})
def result_review(phase,scope,filename):
 run=D/'runs'/phase;v=rd(run/filename);files=sorted(str(p) for p in run.rglob('*') if p.is_file() and p!=run/filename)
 require(v.get('accepted') is True and v.get('findings')==[] and v.get('scope')==scope and v.get('phase')==phase,'Result scope')
 require(set(v.get('sha256',{}))==set(files) and bindings(v) and v.get('evidence_sha256') and bindings(v,'evidence_sha256'),'Result exact bindings')
 return files+[str(run/filename)],rd(run/'posthost.json')['groups']
def predecessor(phase):
 cfg=config(phase);files,groups=base.result_review('green2-300','BG export workspace GREEN2 result','result-review.json')
 require(rd(G/'runs/green2-300/audit.json')['all_passed'] is True and guard.pins_match(rd(G/'runs/green2-300/sealed.json')),'Corrected GREEN not accepted/intact')
 if cfg['process']==2:
  from analysis import first_process_viable
  choices=[p for p in ('cost1-300','cost1-600') if (D/'runs'/p/'result-review.json').is_file()]
  require(len(choices)==1,'Exactly one first process')
  f,g=result_review(choices[0],'BG export workspace cost result','result-review.json');a=rd(D/'runs'/choices[0]/'audit.json')
  require(first_process_viable(a,rd(D/'inputs.json')['fixtures']),'Stop fixed design: first process gates')
  require(guard.pins_match(rd(D/'runs'/choices[0]/'sealed.json')),'First process source drift');files+=f;groups+=g
 if phase.endswith('600'):
  prev=phase[:-3]+'300';f,g=result_review(prev,'pure timeout result','timeout-review.json');a=rd(D/'runs'/prev/'audit.json');first=config(prev);s=rd(D/'runs'/prev/'sealed.json')
  require(a['all_passed'] is False and a['pure_timeout'] is True and s['config']==first and first['command'][:-3]==cfg['command'][:-3] and guard.pins_match(s),'Not unchanged pure timeout')
  files+=f;groups+=g
 return sorted(set(files)),sorted(set(groups))
def guard_command(cfg,pins,started):
 seconds=cfg['seconds']-8
 return [sys.executable,'-B',str(D/'guard.py'),'run',str(pins),cfg['output'],'--seconds',str(seconds),'--deadline',str(started+seconds),'--expected-exit','0','--',*cfg['command']]
