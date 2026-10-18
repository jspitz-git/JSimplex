"""Definitions-only separate diagnostic-harness amendment. Original package remains frozen."""
from pathlib import Path
import importlib.util,json,subprocess,sys,os,time
D=Path(__file__).resolve().parent;R=D.parents[3]
O=D.with_name('DIRECT-BG-EXPORT-WORKSPACE-DRIVER-PREPARATION')
spec=importlib.util.spec_from_file_location('original_bgx_control',O/'control.py')
old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
# Definition-only shared primitives, with original lexical paths retained.
require=old.require;rd=old.rd;sha=old.sha;save=old.save;git=old.git;bindings=old.bindings
verify_review=old.verify_review;host_safe=old.host_safe;validate_environment=old.validate_environment
validate_sources=old.validate_sources;loaded_for=old.loaded_for;guard=old.guard
MASTER=old.MASTER;ENTRY=old.ENTRY;WRAPPER=old.WRAPPER;W=old.W;C=old.C

def full_host(extra=()):
 return old.full_host(list(extra)+rd(O/'runs/green300/posthost.json')['groups'])
def config(phase):
 require(phase in ('green2-300','green2-600'),'Unprepared amended phase')
 stage=rd(O/'stages.json')['green']['path'];run=D/'runs'/phase;out=run/'output'
 command=['/bin/bash',WRAPPER,'--compiled-modules=existing','--threads=1','--gcthreads=1,0','--heap-size-hint=2G','--history-file=no','--project='+stage,str(D/'driver.jl'),str(out),stage,phase]
 return dict(phase=phase,mode='green',seconds=300 if phase.endswith('300') else 600,expected_exit=0,stage=stage,run=str(run),output=str(out),command=command)
def preparation():
 original=old.preparation();m=D/'preparation-pins.json';j=rd(m)
 require(bindings(j) and set(j['sha256'])==set(rd(D/'required-paths.json')['paths']),'Amendment preparation drift/membership')
 verify_review(rd(D/'review.json'),m,list(j['sha256'])+[str(m)],'BG export workspace GREEN2 harness preparation')
 return sorted(set(original)|set(j['sha256'])|{str(m),str(D/'review.json')})
def result_review(phase,scope,filename):
 run=D/'runs'/phase;v=rd(run/filename);files=sorted(str(p) for p in run.rglob('*') if p.is_file() and p!=run/filename)
 require(v.get('accepted') is True and v.get('findings')==[] and v.get('scope')==scope and v.get('phase')==phase,'Result review absent/wrong')
 require(set(v.get('sha256',{}))==set(files) and bindings(v) and v.get('evidence_sha256') and bindings(v,'evidence_sha256'),'Result exact bindings/evidence')
 return files+[str(run/filename)],rd(run/'posthost.json')['groups']
def predecessor(phase):
 cfg=config(phase);files,groups=old.predecessor('green300')
 f,g=old.result_review('green300','BG export workspace GREEN failed result','result-review.json');files+=f;groups+=g
 v=rd(O/'runs/green300/result-review.json');a=rd(O/'runs/green300/audit.json')
 require(v.get('correctness_accepted') is False and bindings(v,'evidence_sha256') and a['all_passed'] is False and a['pure_timeout'] is False,'Original failure preservation')
 require(guard.pins_match(rd(O/'runs/green300/sealed.json')),'Original failed attempt drift')
 if phase=='green2-600':
  f,g=result_review('green2-300','pure timeout result','timeout-review.json');a=rd(D/'runs/green2-300/audit.json')
  require(a['all_passed'] is False and a['pure_timeout'] is True,'Not pure timeout')
  first=config('green2-300');s=rd(D/'runs/green2-300/sealed.json')
  require(s['config']==first and first['command'][:-3]==cfg['command'][:-3] and guard.pins_match(s),'Timeout source drift')
  files+=f;groups+=g
 return sorted(set(files)),sorted(set(groups))
def guard_command(cfg,pins,started):
 seconds=cfg['seconds']-8
 return [sys.executable,'-B',str(D/'guard.py'),'run',str(pins),cfg['output'],'--seconds',str(seconds),'--deadline',str(started+seconds),'--expected-exit','0','--',*cfg['command']]
