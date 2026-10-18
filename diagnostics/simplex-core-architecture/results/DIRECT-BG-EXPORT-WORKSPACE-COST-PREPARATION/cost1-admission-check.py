"""Fresh exact-phase admission checks; no Julia or prior checker execution."""
from pathlib import Path
import hashlib,json,os,sys,time
D=Path(__file__).resolve().parent;sys.dont_write_bytecode=True;sys.path.insert(0,str(D))
import control as c
run=D/'runs/cost1-300';sp=run/'sealed.json';s=c.rd(sp);checks={}
def ck(name,value):
    checks[name]=bool(value)
    if not value:raise AssertionError(name)
def save(p,v):
    with p.open('x') as f:json.dump(v,f,indent=2);f.write('\n')
cfg=c.config('cost1-300')
ck('phase_config',s['phase']=='cost1-300' and s['config']==cfg==c.rd(run/'config.json'))
ck('only_sealed_inputs',{p.name for p in run.iterdir()}=={'host.json','config.json','sealed.json'})
ck('initial_bounds',cfg['seconds']==300 and cfg['expected_exit']==0 and cfg['process']==1)
cmd=['/bin/bash',c.WRAPPER,'--compiled-modules=existing','--threads=1','--gcthreads=1,0','--heap-size-hint=2G','--history-file=no',
 '--project='+cfg['stage'],str(D/'cost.jl'),'cost1-300',str(run/'output'),cfg['stage']]
ck('exact_command',cfg['command']==cmd)
gc=c.guard_command(cfg,run/'launch-pins.json',1000.)
ck('guard_inner_292',gc==[sys.executable,'-B',str(D/'guard.py'),'run',str(run/'launch-pins.json'),str(run/'output'),'--seconds','292','--deadline','1292.0','--expected-exit','0','--',*cmd])
ck('preparation_manifest_exact',len(c.rd(D/'preparation-pins.json')['sha256'])==2100 and set(c.rd(D/'preparation-pins.json')['sha256'])==set(c.rd(D/'required-paths.json')['paths']))
prepfiles=c.preparation();ck('preparation_accepted_current',bool(prepfiles))
c.validate_environment();ck('exact_environment',True)
c.validate_sources();ck('current_sources_runtime_refs',True)
predecessor,groups=c.predecessor('cost1-300')
ck('GREEN2_predecessor_exact',len(groups)==252 and bool(predecessor))
expected=sorted(set(prepfiles+list(c.rd(D/'runtime-inputs-complete.json')['inventory'])+
 [str(root/n) for label,root in [('diagnostic',c.R),('production',c.W)] for n in c.rd(D/'baseline.json')[label]]+
 [str(Path(cfg['stage'])/n) for n in c.rd(D/'stages.json')['cost']['sha256']]+predecessor+
 [str(run/'host.json'),str(run/'config.json')]))
ck('exact_sealed_file_membership',s['files']==expected and len(s['files'])==len(set(s['files']))==2104)
ck('exact_sealed_trees',s['trees']==[cfg['stage'],str(c.C)] and s['inputs']==[])
actual=c.guard.inventory(s['files'],s['trees'])
ck('all_sealed_hashes_and_resolutions',actual==s['inventory'] and len(actual)==2104)
ck('manifest_and_runtime_all_in_seal',set(c.rd(D/'required-paths.json')['paths'])<=set(s['files']) and set(c.rd(D/'runtime-inputs-complete.json')['inventory'])<=set(s['files']))
h=c.full_host(groups+s['groups'])
h['memory']=c.guard.memory()
h['status']=c.git('status','--porcelain')
h['remote']=c.git('ls-remote','origin','refs/heads/master','refs/heads/codex/simplex-core-architecture')
save(D/'cost1-admission-host.json',h)
ck('fresh_host_safe',c.host_safe(h))
ck('all_252_groups_and_sessions',len(h['groups'])==252 and set(h['groups'])==set(s['groups'])==set(groups))
ck('host_identity_ref_boot',all(h[k]==s[k]==c.rd(run/'host.json')[k] for k in ('head','master','boot_id')))
ck('expected_refs',h['head']=='6fb6539c07262ae9adc237a4d90488da6fac2c61' and h['master']=='26e2291745999f485a74f643298ca997d65c7205')
ck('matching_remote_refs',h['head']+'\trefs/heads/codex/simplex-core-architecture' in h['remote'] and h['master']+'\trefs/heads/master' in h['remote'])
ck('minimum_ram_maximum_swap',not c.guard.pressure(h['memory']))
ck('tracked_clean',not c.git('diff','--name-only') and not c.git('diff','--cached','--name-only'))
ck('no_reservation_output_invocation',not any((run/n).exists() for n in ('reservation.json','output','invocation.json','launch-pins.json','prehost.json')))
ck('pin_bytes_still_current',c.guard.pins_match(s))
# The unchanged accepted preparation supplies the full independent source inverse and refusal review.
v=c.rd(D/'review.json')
ck('prior_independent_129_checks',c.rd(D/'reviewer-check.json')['all_passed'] is True and c.rd(D/'reviewer-check.json')['check_count']==129)
ck('review_evidence_bound',bool(v.get('evidence_sha256')) and c.bindings(v,'evidence_sha256'))
record=dict(all_passed=all(checks.values()),check_count=len(checks),checks=checks,phase='cost1-300',pins_sha256=c.sha(sp),
 sealed_files=len(s['files']),inventory_entries=len(s['inventory']),historical_groups_and_sessions=len(groups),
 scope='Fresh exact-stage admission only. No Julia/parser/import/compiler, launch, seal or old checker execution.',
 api_budget=dict(constructions=204,refactors=412,updates=1472,ftran=2944,btran=1472,copies=4,native_orientation_solves_upper_bound=308))
save(D/'cost1-admission-check.json',record)
print(json.dumps(dict(all_passed=record['all_passed'],checks=len(checks),sealed_files=len(s['files']),host_safe=c.host_safe(h),memory=h['memory'])))
