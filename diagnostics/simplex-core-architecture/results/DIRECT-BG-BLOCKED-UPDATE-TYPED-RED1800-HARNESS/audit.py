"""UNEXECUTED one-shot auditor; failed and timeout results stay failed."""
from control import *
from oracle import validate,warning_log,PAYLOAD
import tomllib,math

def resource_records(resources,terminal,elapsed):
 require(type(resources) is list and bool(resources),'Missing samples')
 require(type(elapsed) in (int,float) and math.isfinite(elapsed) and 0<=elapsed<=1792,'Process elapsed for resources')
 previous=-1.0
 for sample in resources:
  require(type(sample) is dict and {'available_kib','swap_used_kib','elapsed'}<=set(sample)<={'available_kib','swap_used_kib','elapsed','child_memory'},'Resource fields')
  t=sample['elapsed']
  require(type(t) in (int,float) and math.isfinite(t) and 0<=t<=elapsed and t>=previous,'Resource elapsed/order')
  previous=t
  if 'child_memory' in sample:require(type(sample['child_memory']) is list and all(type(line) is str for line in sample['child_memory']),'Resource child-memory text')
 require(type(terminal) is dict and set(terminal)=={'available_kib','swap_used_kib'},'Terminal resource fields')
 require(all(type(z[k]) is int and z[k]>=0 for z in resources+[terminal] for k in ('available_kib','swap_used_kib')),'Resource types')
 require(all(z['available_kib']>=6*1024**2 and z['swap_used_kib']<=1024**2 for z in resources+[terminal]),'Resource limit')
 return True

def checks_for(phase):
 cfg=config(phase);run=Path(cfg['run']);out=Path(cfg['output']);validate_environment();preparation();validate_sources();predecessor(phase)
 names={p.name for p in out.iterdir()};base={'pins.json','current.json','process.json','resources.jsonl','run.log'}
 require(names==base and all(p.is_file() and not p.is_symlink() for p in out.iterdir()) and not out.is_symlink(),'Exact guard output membership')
 payload=Path(cfg['payload'])
 require(not payload.is_symlink() and payload.is_dir(),'Payload root')
 require({p.name for p in payload.iterdir()}==PAYLOAD and all(p.is_file() and not p.is_symlink() for p in payload.iterdir()),'Exact payload membership')
 sp=run/'sealed.json';s=rd(sp);rp=run/'admission.json';pp=run/'launch-pins.json';pins=rd(pp)
 verify_seal(cfg,s)
 verify_outer_invocation(phase,s)
 require(str(outer_dir(phase)/'outer-ready.json') in s['files'],'Outer ready not sealed')
 require(s['phase']==phase and s['config']==cfg and rd(run/'config.json')==cfg,'Config')
 verify_review(rd(rp),sp,s['files']+[str(sp)],'BG blocked typed RED repeat exact-run admission',phase)
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
 resource_records(resources,p['terminal_memory'],p['elapsed_including_launch'])
 require(type(p['child_maxrss_kib']) in (int,float) and math.isfinite(p['child_maxrss_kib']) and p['child_maxrss_kib']>0,'RSS')
 require(all(sup.get(k) is False for k in ('soft_timeout','hard_timeout','child_kill','guard_term','guard_kill')),'Timeout/termination')
 require('error' not in p and 'remaining_group' not in p and 'remaining_session' not in p,'Process error/descendants')
 require(type(p['elapsed_including_launch']) in (int,float) and math.isfinite(p['elapsed_including_launch']) and 0<=p['elapsed_including_launch']<=cfg['seconds']-8,'Child inclusive bound')
 require(p['cwd']==str(R),'Wrong child cwd')
 require(type(p['returncode']) is int and p['returncode']==cfg['expected_exit'] and p['reason']=='exit'+str(cfg['expected_exit']) and type(sup['returncode']) is int and sup['returncode']==0 and sup['accepted'] is True,'Exact successful exit')
 log=(out/'run.log').read_text(errors='replace')+'\n'+(run/'launcher.log').read_text(errors='replace')
 data={p.name:tomllib.loads(p.read_text()) for p in payload.iterdir()}
 result=validate(data,rd(D/'schedule.json'),loaded_for(cfg),'red300') # unchanged Julia/raw RED semantic phase
 require(not warning_log(log,data,'red300'),'Warning/world-age/unexpected error log')
 return dict(all_passed=True,pure_timeout=False,result=result,process_elapsed_seconds=inv['elapsed_seconds'],scope_note='Full blocked BG structural/lifecycle/stream qualification; no Task3 performance acceptance',error='')

def audit(phase):
 run=Path(config(phase)['run'])
 try:record=checks_for(phase)
 except Exception as e:record=dict(all_passed=False,pure_timeout=False,error=repr(e),result={})
 files=sorted(p for p in run.rglob('*') if p.is_file())
 record.update(phase=phase,sha256={str(p):sha(p) for p in files},scope='Saved blocked BG typed RED/GREEN integrity/results; independent result review required')
 save(run/'audit.json',record);return record
if __name__=='__main__':require(audit(sys.argv[1])['all_passed'],'Failed; preserve evidence')
