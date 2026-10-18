"""Fresh exact GREEN2-300 admission: read-only controls/host, no Julia execution."""
from pathlib import Path
import hashlib,json,sys,os
D=Path(__file__).resolve().parent;R=D.parents[3];O=D.with_name('DIRECT-BG-EXPORT-WORKSPACE-DRIVER-PREPARATION');run=D/'runs/green2-300'
sys.path.insert(0,str(D));import control as c
checks={};cache={}
def ck(name,v):checks[name]=bool(v)
def rd(p):return json.loads(Path(p).read_text())
def sha(p):
 p=Path(p);p=p if p.is_absolute() else R/p
 if str(p) not in cache:
  h=hashlib.sha256()
  with p.open('rb') as f:
   for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
  cache[str(p)]=h.hexdigest()
 return cache[str(p)]
def bound(v,key='sha256'):return all(sha(p)==h for p,h in v[key].items())
s=rd(run/'sealed.json');cfg=c.config('green2-300');files=set(s['files']);m=rd(D/'preparation-pins.json');v=rd(D/'review.json')
ck('exact_config_phase',s['phase']=='green2-300' and s['config']==cfg==rd(run/'config.json'))
ck('exact_scope_300',cfg['mode']=='green' and cfg['seconds']==300 and cfg['expected_exit']==0)
ck('command_exact',cfg['command']==['/bin/bash',c.WRAPPER,'--compiled-modules=existing','--threads=1','--gcthreads=1,0','--heap-size-hint=2G','--history-file=no','--project='+cfg['stage'],str(D/'driver.jl'),str(run/'output'),cfg['stage'],'green2-300'])
ck('seal1964_exact_inventory',len(files)==len(s['files'])==1964 and set(s['inventory'])==files and all(vv==dict(resolved=str(Path(p).resolve(strict=True)),sha256=sha(p)) for p,vv in s['inventory'].items()))
ck('sealed_manifest1942',len(m['sha256'])==1942 and set(m['sha256'])==set(rd(D/'required-paths.json')['paths']) and bound(m) and set(m['sha256'])<=files)
ck('preparation_exact_review',v['accepted'] is True and v['findings']==[] and v['scope']=='BG export workspace GREEN2 harness preparation' and v['pins_sha256']==sha(D/'preparation-pins.json') and set(v['sha256'])==set(m['sha256'])|{str(D/'preparation-pins.json')} and bound(v) and bound(v,'evidence_sha256'))
ck('prior56checksevidence',rd(D/'independent-review-check.json')['all_passed'] is True and len(rd(D/'independent-review-check.json')['checks'])==56)
# Definitions-only validation, not any prior checker or audit execution.
prepared=c.preparation();pred,groups=c.predecessor('green2-300');c.validate_environment();c.validate_sources()
ck('actual_environment_source_runtime_stage_refs',True)
expected=set(prepared)|set(rd(D/'runtime-inputs-complete.json')['inventory'])|set(pred)|{str(run/'host.json'),str(run/'config.json')}
for label,root in [('diagnostic',R),('production',c.W)]:expected.update(str(root/n) for n in rd(D/'baseline.json')[label])
expected.update(str(Path(cfg['stage'])/n) for n in rd(D/'stages.json')['green']['sha256'])
ck('exact_sealed_file_derivation',files==expected)
ck('candidate_stage_trees',s['trees']==[cfg['stage'],str(c.C)] and s['inputs']==[])
for tree in s['trees']:
 root=Path(tree);actual={str(p) for p in root.rglob('*') if p.is_file()}
 ck('tree_membership_'+root.name,actual<=files and not root.is_symlink() and not any(p.is_symlink() for p in root.rglob('*')))
stages=rd(D/'stages.json');red=Path(stages['red']['path']);green=Path(stages['green']['path'])
for name,count in [('red',75),('green',79)]:
 root=Path(stages[name]['path']);actual={str(p.relative_to(root)) for p in root.rglob('*') if p.is_file()}
 ck('stage_exact_'+name,len(actual)==count and actual==set(stages[name]['sha256']) and all(sha(root/n)==h for n,h in stages[name]['sha256'].items()))
extra={f'src/_bgx_{n}.jl' for n in ['workspace','export','import','factor']}
ck('four_additional_candidate_files',set(stages['green']['sha256'])-set(stages['red']['sha256'])==extra)
ck('unchanged_other_stage_files',all(sha(red/n)==sha(green/n) for n in stages['red']['sha256'] if n!='src/JSimplex.jl'))
root=(green/'src/JSimplex.jl').read_text();original=(red/'src/JSimplex.jl').read_text()
for n in ['workspace','export','import','factor']:
 line=f'include("_bgx_{n}.jl")\n';ck('one_include_'+n,root.count(line)==1);root=root.replace(line,'');ck('candidate_mapping_'+n,sha(green/f'src/_bgx_{n}.jl')==sha(c.C/f'{n}.jl'))
ck('exact_root_inverse',root==original)
i=rd(D/'inverse.json');before=Path(i['original']).read_text();after=Path(i['amended']).read_text()
ck('single_harness_identity_inverse',after.count(i['after'])==1 and after.replace(i['after'],i['before'])==before and before.count('@test')==after.count('@test'))
fixture=(Path(i['amended']).parent/'../../direct-lu-policy-adapters/reproduce/fixtures.jl').resolve()
ck('actual_fixture_pinned',str(fixture) in files and fixture==(c.C/'../../direct-lu-policy-adapters/reproduce/fixtures.jl').resolve())
for n in i['copied_controls']:ck('unchanged_control_'+n,sha(D/n)==sha(O/n))
orig=(O/'driver.jl').read_text()
for a,b in i['driver_replacements']:orig=orig.replace(a,b)
ck('driver_exact',orig==(D/'driver.jl').read_text())
e=rd(D/'expected-tests.json')['green'];ck('exact7935groups',e['assertions']==7935 and [g[1] for g in e['groups']]==[42,6,35,56,108,53,303,6236,378,108,610] and all(g[2:]==[0,0,0] for g in e['groups']) and sha(D/'expected-tests.json')==sha(O/'expected-tests.json') and sha(D/'expected-tests.toml')==sha(O/'expected-tests.toml'))
oldrun=O/'runs/green300';oldreview=rd(oldrun/'result-review.json');oldaudit=rd(oldrun/'audit.json')
ck('original_GREEN_failed_preserved',oldreview['accepted'] is True and oldreview['correctness_accepted'] is False and oldreview['cost_predecessor_accepted'] is False and oldaudit['all_passed'] is False and oldaudit['pure_timeout'] is False and oldreview['result']['pass']==7934 and oldreview['result']['error']==1 and bound(oldreview) and bound(oldreview,'evidence_sha256'))
ck('RED_accepted_preserved',rd(O/'runs/red300/audit.json')['all_passed'] is True and rd(O/'runs/red300/result-review.json')['accepted'] is True)
ck('old_attempts_in_seal',str(oldrun/'result-review.json') in files and str(O/'runs/red300/result-review.json') in files)
ck('prior_groups_exact250',len(s['groups'])==250 and set(groups)==set(s['groups']))
ck('run_only_seal_host_config',{p.name for p in run.iterdir()}=={'sealed.json','config.json','host.json'})
ck('no_next_attempt_or_cost',not (D/'runs/green2-600').exists() and not (D/'runs/green2-300/output').exists() and not (D/'runs/green2-300/reservation.json').exists())
# Independent current host evidence after full input validation.
h=c.full_host(s['groups']);h['memory']=c.guard.memory();h['remote']=c.git('ls-remote','origin','refs/heads/master','refs/heads/codex/simplex-core-architecture');h['status']=c.git('status','--porcelain')
ck('fresh_scoped_host',c.host_safe(h) and len(h['groups'])==250 and set(h['groups'])==set(s['groups']))
ck('fresh_ref_boot_seal',all(h[k]==s[k]==rd(run/'host.json')[k] for k in ['head','master','boot_id']))
ck('requested_refs',h['head']=='3c6e5cc7aec51e022da2e1834e8c11779f84b314' and h['master']=='26e2291745999f485a74f643298ca997d65c7205')
ck('remote_refs',h['head']+'\trefs/heads/codex/simplex-core-architecture' in h['remote'] and h['master']+'\trefs/heads/master' in h['remote'])
ck('memory_admissible',h['memory']['available_kib']>=6*1024**2 and h['memory']['swap_used_kib']<=1024**2)
ck('tracked_unchanged',not c.git('diff','--name-only') and not c.git('diff','--cached','--name-only'))
ck('guard_inner292',c.guard_command(cfg,run/'launch-pins.json',100)==[sys.executable,'-B',str(D/'guard.py'),'run',str(run/'launch-pins.json'),str(run/'output'),'--seconds','292','--deadline','392','--expected-exit','0','--',*cfg['command']])
ck('pidfd_available',hasattr(os,'pidfd_open') and hasattr(__import__('signal'),'pidfd_send_signal'))
result=dict(all_passed=all(checks.values()),checks=checks,host=h,phase='green2-300',seal_sha256=sha(run/'sealed.json'),sealed_files=len(files),scope='Fresh offline exact-stage admission check only; no Julia, reservation, launch, numerical correctness or cost acceptance')
with (D/'admission-check.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
print(json.dumps(dict(all_passed=result['all_passed'],checks=len(checks),failed=[n for n,v in checks.items() if not v],sealed_files=len(files),groups=len(h['groups']),unreadable_exe=len(h['unreadable_exe_pids']),unreadable_identity=len(h['unreadable_identity_pids']),memory=h['memory'])))
if not result['all_passed']:raise SystemExit(1)
