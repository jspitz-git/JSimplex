"""New allocation provenance admission. Definitions only; prior evidence frozen."""
from pathlib import Path
import importlib.util,json,sys,os,time,subprocess
D=Path(__file__).resolve().parent;R=D.parents[3];O=D.with_name('DIRECT-BG-EXPORT-WORKSPACE-COST-PREPARATION')
sp=importlib.util.spec_from_file_location('bgcost_control',O/'control.py');base=importlib.util.module_from_spec(sp);sp.loader.exec_module(base)
require=base.require;rd=base.rd;sha=base.sha;save=base.save;git=base.git;bindings=base.bindings;verify_review=base.verify_review;guard=base.guard;host_safe=base.host_safe;MASTER=base.MASTER;W=base.W;C=base.C
validate_sources=base.validate_sources;validate_environment=base.validate_environment
def full_host(extra=()):return base.full_host(list(extra)+rd(O/'runs/cost1-300/posthost.json')['groups'])
def config(phase):
 require(phase=='profile300','Unprepared phase; no automatic retry')
 stage=rd(D/'stages.json')['green']['path'];run=D/'runs'/phase
 command=['/bin/bash',base.WRAPPER,'--compiled-modules=existing','--threads=1','--gcthreads=1,0','--heap-size-hint=2G','--history-file=no','--project='+stage,str(D/'driver.jl'),phase,str(run/'output'),stage]
 return dict(phase=phase,mode='green',seconds=300,expected_exit=0,stage=stage,run=str(run),output=str(run/'output'),command=command)
def preparation():
 old=base.preparation();m=D/'preparation-pins.json';j=rd(m)
 require(set(j['sha256'])==set(rd(D/'required-paths.json')['paths']) and bindings(j),'Provenance preparation drift')
 return sorted(set(old)|set(j['sha256'])|{str(m)})
def predecessor(phase):
 config(phase);files,groups=base.result_review('cost1-300','BG export workspace cost result','result-review.json')
 require(rd(O/'runs/cost1-300/result-review.json')['performance_accepted'] is False,'Cost rejection preserved')
 return files,groups
def loaded_for(cfg):return dict(rd(D/'loaded-paths.json'),JSimplex=str(Path(cfg['stage'])/'src/JSimplex.jl'))
def guard_command(cfg,pins,started):return [sys.executable,'-B',str(D/'guard.py'),'run',str(pins),cfg['output'],'--seconds','292','--deadline',str(started+292),'--expected-exit','0','--',*cfg['command']]
