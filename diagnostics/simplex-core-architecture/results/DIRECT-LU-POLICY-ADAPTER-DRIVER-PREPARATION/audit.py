"""UNEXECUTED one-shot auditor; failed and timeout results stay failed."""
from control import *
from oracle import test_results,timeout_only
import tomllib,math

def checks_for(phase):
 cfg=config(phase);run=Path(cfg['run']);out=Path(cfg['output']);validate_environment();preparation();validate_sources();predecessor(phase)
 names={p.name for p in out.iterdir()};base={'pins.json','current.json','process.json','resources.jsonl','run.log'}
 require(names in [base,base|{'raw.toml'}] and all(p.is_file() and not p.is_symlink() for p in out.iterdir()),'Output membership')
 sp=run/'sealed.json';s=rd(sp);rp=run/'admission.json';pp=run/'launch-pins.json';pins=rd(pp)
 require(s['phase']==phase and s['config']==cfg and rd(run/'config.json')==cfg,'Config')
 verify_review(rd(rp),sp,s['files']+[str(sp)],'direct adapter exact-stage admission',phase)
 require(set(pins['files'])==set(s['files'])|{str(sp),str(rp),str(run/'prehost.json')} and pins['trees']==s['trees'],'Launch membership')
 require(guard.pins_match(s) and guard.pins_match(pins) and rd(out/'pins.json')==pins,'Pins changed')
 require(all(pins['inventory'].get(n)==v for n,v in s['inventory'].items()),'Seal/launch drift')
 inv=rd(run/'invocation.json');sup=inv['supervisor'];p=rd(out/'process.json');cur=rd(out/'current.json');pre=rd(run/'prehost.json');hs=rd(run/'host.json');post=rd(run/'posthost.json')
 require(all(not h['matches'] for h in [pre,hs,post]),'Processes remain')
 require(all(pre[k]==hs[k]==post[k]==s[k] for k in ['head','master','boot_id']),'Host drift')
 require(set(s['groups'])<=set(pre['groups'])<=set(post['groups']),'Group coverage')
 require(cur['runner']==p['runner']==sup['guard_identity'] and cur['child']==p['child'],'Identity linkage')
 require(all(p[role][key] in post['groups'] for role in ['runner','child'] for key in ['pgid','sid']),'Group/session closure')
 require(all(p[role]['boot_id']==s['boot_id'] and p[role]['start_ticks']>0 and p[role]['command'] for role in ['runner','child']),'Boot/start/command')
 require(all(type(v) in (int,float) and math.isfinite(v) and 0<=v<=cfg['seconds'] for v in [inv['elapsed_seconds'],sup['elapsed_seconds']]) and 'cleanup_error' not in sup,'Inclusive limit/cleanup')
 require(p['pins_unchanged'] is True and p['command']==cur['command']==inv['command']==cfg['command'],'Command/integrity')
 require(p['pins_sha256']==cur['pins_sha256']==inv['pins_sha256']==sha(pp),'Pin identity')
 require(inv['guard_command']==guard_command(cfg,pp,inv['monotonic_start']) and Path(inv['python']).resolve()==Path(sys.executable).resolve(),'Guard command')
 res=run/'reservation.json';require(rd(res)==dict(one_attempt=True,phase=phase,command=cfg['command'],pins_sha256=sha(pp),review_sha256=sha(rp),max_seconds=cfg['seconds']),'Reservation')
 require(inv['reservation_sha256']==sha(res) and inv['review_sha256']==sha(rp),'Invocation linkage')
 resources=[json.loads(v) for v in (out/'resources.jsonl').read_text().splitlines()];require(resources,'Missing samples')
 require(all(z['available_kib']>=6*1024**2 and z['swap_used_kib']<=1024**2 for z in resources+[p['terminal_memory']]),'Resource limit')
 require(type(p['child_maxrss_kib']) in (int,float) and math.isfinite(p['child_maxrss_kib']) and p['child_maxrss_kib']>0,'RSS')
 raw=tomllib.loads((out/'raw.toml').read_text()) if 'raw.toml' in names else None
 log=(out/'run.log').read_text(errors='replace')+'\n'+(run/'launcher.log').read_text(errors='replace')
 pure=timeout_only(p,sup,raw,log,inv['elapsed_seconds'],cfg['seconds'],loaded_for(cfg),phase)
 if pure:return dict(all_passed=False,pure_timeout=True,result={},error='Pure process timeout; independent result review required before new600s admission')
 require(p['returncode']==cfg['expected_exit'] and p['reason']=='exit'+str(cfg['expected_exit']) and sup['returncode']==0 and sup['accepted'] is True,'Exact exit')
 require(raw is not None and names==base|{'raw.toml'},'Missing raw')
 result=test_results(raw,rd(D/'expected-tests.json')[cfg['mode']],loaded_for(cfg),phase)
 require('BROKEN TEST:' not in log and 'FATAL DRIVER:' not in log and 'GROUP/COUNT MISMATCH' not in log,'Failure log')
 require(log.count('TEST FAILURE:')==(7 if cfg['mode']=='red' else 0),'Exact failure log count')
 return dict(all_passed=True,pure_timeout=False,result=result,error='')
def audit(phase):
 run=Path(config(phase)['run'])
 try:record=checks_for(phase)
 except Exception as e:record=dict(all_passed=False,pure_timeout=False,error=repr(e),result={})
 files=sorted(p for p in run.rglob('*') if p.is_file())
 record.update(phase=phase,sha256={str(p):sha(p) for p in files},scope='Saved adapter phase integrity/results; independent result review required')
 save(run/'audit.json',record);return record
if __name__=='__main__':require(audit(sys.argv[1])['all_passed'],'Failed; preserve evidence')
