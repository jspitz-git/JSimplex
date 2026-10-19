"""UNEXECUTED one-shot auditor; failed and timeout results stay failed."""
from control import *
from oracle import test_results,prefix,warning_log
import tomllib,math

def checks_for(phase):
 cfg=config(phase);run=Path(cfg['run']);out=Path(cfg['output']);validate_environment();preparation();validate_sources();predecessor(phase)
 names={p.name for p in out.iterdir()};base={'pins.json','current.json','process.json','resources.jsonl','run.log'}
 units={f'unit-{i}.toml' for i in range(1,29)}
 require(base<=names<=base|{'raw.toml'}|units and all(p.is_file() and not p.is_symlink() for p in out.iterdir()),'Output membership')
 sp=run/'sealed.json';s=rd(sp);rp=run/'admission.json';pp=run/'launch-pins.json';pins=rd(pp)
 verify_seal(cfg,s)
 verify_outer_invocation(phase,s)
 require(str(outer_dir(phase)/'outer-ready.json') in s['files'],'Outer ready not sealed')
 require(s['phase']==phase and s['config']==cfg and rd(run/'config.json')==cfg,'Config')
 verify_review(rd(rp),sp,s['files']+[str(sp)],'BG blocked U exact-stage admission',phase)
 require(set(pins['files'])==set(s['files'])|{str(sp),str(rp),str(run/'prehost.json'),str(outer_dir(phase)/'release.json'),str(outer_dir(phase)/'outer-invocation.json')} and pins['trees']==s['trees'],'Launch membership')
 require(guard.pins_match(s) and guard.pins_match(pins) and rd(out/'pins.json')==pins,'Pins changed')
 require(all(pins['inventory'].get(n)==v for n,v in s['inventory'].items()),'Seal/launch drift')
 inv=rd(run/'invocation.json');sup=inv['supervisor'];p=rd(out/'process.json');cur=rd(out/'current.json');pre=rd(run/'prehost.json');hs=rd(run/'host.json');post=rd(run/'posthost.json')
 require(all(host_safe(h) for h in [pre,hs,post]),'Processes remain')
 require(all(pre[k]==hs[k]==post[k]==s[k] for k in ['head','master','boot_id']),'Host drift')
 require(set(s['groups'])<=set(pre['groups'])<=set(post['groups']),'Group coverage')
 require(cur['runner']==p['runner']==sup['guard_identity'] and cur['child']==p['child'],'Identity linkage')
 require(all(p[role][key] in post['groups'] for role in ['runner','child'] for key in ['pgid','sid']),'Group/session closure')
 require(all(p[role]['boot_id']==s['boot_id'] and p[role]['start_ticks']>0 and p[role]['command'] for role in ['runner','child']),'Boot/start/command')
 require(all(type(v) in (int,float) and math.isfinite(v) and 0<=v<=cfg['seconds'] for v in [inv['elapsed_seconds'],sup['elapsed_seconds']]) and 'cleanup_error' not in sup,'Inclusive limit/cleanup')
 require(p['pins_unchanged'] is True and p['command']==cur['command']==inv['command']==cfg['command'],'Command/integrity')
 require(p['pins_sha256']==cur['pins_sha256']==inv['pins_sha256']==sha(pp),'Pin identity')
 require(inv['guard_command']==guard_command(cfg,pp,inv['monotonic_start']) and Path(inv['python']).resolve()==Path(sys.executable).resolve(),'Guard command')
 res=run/'reservation.json';require(rd(res).get('one_attempt') is True,'Strict reservation boolean');require(rd(res)==dict(one_attempt=True,phase=phase,command=cfg['command'],pins_sha256=sha(pp),review_sha256=sha(rp),max_seconds=cfg['seconds']),'Reservation')
 require(inv['reservation_sha256']==sha(res) and inv['review_sha256']==sha(rp),'Invocation linkage')
 resources=[json.loads(v) for v in (out/'resources.jsonl').read_text().splitlines()];require(resources,'Missing samples')
 require(all(z['available_kib']>=6*1024**2 and z['swap_used_kib']<=1024**2 for z in resources+[p['terminal_memory']]),'Resource limit')
 require(type(p['child_maxrss_kib']) in (int,float) and math.isfinite(p['child_maxrss_kib']) and p['child_maxrss_kib']>0,'RSS')
 raw=tomllib.loads((out/'raw.toml').read_text()) if 'raw.toml' in names else None
 log=(out/'run.log').read_text(errors='replace')+'\n'+(run/'launcher.log').read_text(errors='replace')
 saved_units={n:tomllib.loads((out/n).read_text()) for n in names & units}
 schedule=rd(D/'schedule.json')
 require(not warning_log(log),'Warning/world-age outcome rejected')
 # Conservative classification only: no failed, errored or interrupted saved unit.
 pure=(p['reason']=='wall_time' and p['returncode'] in [-15,-9] and sup['returncode']==1 and sup.get('hard_timeout') is False
       and sup.get('accepted') is False and 'error' not in p and not any(s in log for s in ['TEST FAILURE:','BROKEN TEST:','ERROR:','FATAL DRIVER:','GROUP/COUNT MISMATCH','LoadError','Test Failed','Test Error','OutOfMemoryError'])
       and 'BEGIN BG blocked U driver '+phase in log and raw is None)
 if pure:
  prefix(saved_units,schedule,phase)
  return dict(all_passed=False,pure_timeout=True,result={},error='Incomplete pure timeout; separate reviewed longer admission required')
 require(p['returncode']==cfg['expected_exit'] and p['reason']=='exit'+str(cfg['expected_exit']) and sup['returncode']==0 and sup['accepted'] is True,'Exact exit')
 require(raw is not None and names==base|{'raw.toml'}|units,'Missing raw/units')
 result=test_results(raw,saved_units,schedule,loaded_for(cfg),phase)
 require(not any(s in log for s in ['BROKEN TEST:','FATAL DRIVER:','GROUP/COUNT MISMATCH']),'Failure log')
 require(log.count('TEST FAILURE:')==(6 if cfg['mode']=='red' else 0),'Exact failure log count')
 require([line for line in log.splitlines() if line.startswith('UNIT BEGIN ')]==[f'UNIT BEGIN {i} {n}' for i,n in enumerate(schedule['units'],1)],'Unit start order')
 require([line for line in log.splitlines() if line.startswith('UNIT END ')]==[f'UNIT END {i} {n}' for i,n in enumerate(schedule['units'],1)],'Unit completion order')
 return dict(all_passed=True,pure_timeout=False,result=result,process_elapsed_seconds=inv['elapsed_seconds'],scope_note='Correctness only; cold exact oracles and compilation included; no performance acceptance',error='')
def audit(phase):
 run=Path(config(phase)['run'])
 try:record=checks_for(phase)
 except Exception as e:record=dict(all_passed=False,pure_timeout=False,error=repr(e),result={})
 files=sorted(p for p in run.rglob('*') if p.is_file())
 record.update(phase=phase,sha256={str(p):sha(p) for p in files},scope='Saved BG blocked U phase integrity/results; independent result review required')
 save(run/'audit.json',record);return record
if __name__=='__main__':require(audit(sys.argv[1])['all_passed'],'Failed; preserve evidence')
