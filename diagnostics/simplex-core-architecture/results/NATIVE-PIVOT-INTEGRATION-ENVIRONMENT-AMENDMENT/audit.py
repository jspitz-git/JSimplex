"""UNEXECUTED stage auditor, fail closed on absent or malformed evidence."""
from control import *
from oracle import test_results
import guard,tomllib,math

def checks_for(phase):
 cfg=config(phase);run=Path(cfg['run']);out=Path(cfg['output']);validate_environment();predecessor(phase);validate_stage(cfg)
 names={'pins.json','current.json','process.json','resources.jsonl','run.log','raw.toml'}
 require({p.name for p in out.iterdir()}==names and all(p.is_file() for p in out.iterdir()),'Exact output membership')
 sp=run/'sealed.json';sealed=rd(sp);rp=run/'admission.json';pp=run/'launch-pins.json';pins=rd(pp)
 require(sealed['phase']==phase and sealed['config']==cfg and rd(run/'config.json')==cfg,'Config')
 verify_review(rd(rp),sp,sealed['files']+[str(sp)],'exact-stage admission',phase)
 require(set(pins['files'])==set(sealed['files'])|{str(sp),str(rp),str(run/'prehost.json')} and pins['trees']==sealed['trees'],'Launch membership')
 require(guard.pins_match(sealed) and guard.pins_match(pins) and rd(out/'pins.json')==pins,'Pins changed')
 require(all(pins['inventory'].get(n)==v for n,v in sealed['inventory'].items()),'Seal/launch drift')
 inv=rd(run/'invocation.json');sup=inv['supervisor'];p=rd(out/'process.json');cur=rd(out/'current.json');pre=rd(run/'prehost.json');hs=rd(run/'host.json');post=rd(run/'posthost.json')
 require(all(not h['matches'] for h in [pre,hs,post]),'Processes remain')
 require(all(pre[k]==hs[k]==post[k]==sealed[k] for k in ['head','master','boot_id']),'Host drift')
 require(set(sealed['groups'])<=set(pre['groups'])<=set(post['groups']),'Group coverage')
 require(cur['runner']==p['runner']==sup['guard_identity'] and cur['child']==p['child'],'Process identity linkage')
 require(all(p[role][key] in post['groups'] for role in ['runner','child'] for key in ['pgid','sid']),'New group/session coverage')
 require(all(p[role]['boot_id']==sealed['boot_id'] and p[role]['start_ticks']>0 and p[role]['command'] for role in ['runner','child']),'Boot/start/command identity')
 require(0<=inv['elapsed_seconds']<=cfg['seconds'] and 0<=sup['elapsed_seconds']<=cfg['seconds'] and sup['accepted'] is True and 'cleanup_error' not in sup,'Inclusive limit/cleanup')
 require(p['returncode']==cfg['expected_exit'] and p['reason']==f"exit{cfg['expected_exit']}" and sup['returncode']==0 and p['pins_unchanged'] is True,'Exact exit')
 require(p['command']==cur['command']==inv['command']==cfg['command'],'Command')
 require(p['pins_sha256']==cur['pins_sha256']==inv['pins_sha256']==sha(pp),'Pin identity')
 require(inv['guard_command']==guard_command(cfg,pp,inv['monotonic_start']) and Path(inv['python']).resolve()==Path(sys.executable).resolve(),'Guard command')
 res=run/'reservation.json';require(rd(res)==dict(one_attempt=True,phase=phase,command=cfg['command'],pins_sha256=sha(pp),review_sha256=sha(rp),max_seconds=cfg['seconds']),'Reservation')
 require(inv['reservation_sha256']==sha(res) and inv['review_sha256']==sha(rp),'Invocation linkage')
 resources=[json.loads(s) for s in (out/'resources.jsonl').read_text().splitlines()];require(resources,'Missing resource samples')
 require(all(z['available_kib']>=6*1024**2 and z['swap_used_kib']<=1024**2 for z in resources+[p['terminal_memory']]),'Resource limit')
 require(type(p['child_maxrss_kib']) in (int,float) and math.isfinite(p['child_maxrss_kib']) and p['child_maxrss_kib']>0,'Terminal resident memory')
 raw=tomllib.loads((out/'raw.toml').read_text());expected=rd(D/'loaded-paths.json');expected=dict(expected,JSimplex=str(Path(cfg['stage'])/'src/JSimplex.jl'))
 require(raw['loaded']==expected,'Loaded paths')
 result=test_results(raw,phase)
 result['resident_highwater_kib']=p['child_maxrss_kib'];result['resources']=resources
 return result

def audit(phase):
 cfg=config(phase);run=Path(cfg['run']);result={};error=''
 try:result=checks_for(phase)
 except Exception as e:error=repr(e)
 files=sorted({p for p in run.rglob('*') if p.is_file()}|{p for p in D.iterdir() if p.is_file()})
 record=dict(phase=phase,all_passed=not error,error=error,result=result,sha256={str(p):sha(p) for p in files},scope='Exact single stage integrity; independent result review still required')
 save(run/'audit.json',record);return record
if __name__=='__main__':require(audit(sys.argv[1])['all_passed'],'Audit failed; preserve and stop')
