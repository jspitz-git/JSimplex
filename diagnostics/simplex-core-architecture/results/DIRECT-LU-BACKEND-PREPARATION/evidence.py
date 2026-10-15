"""Read-only fail-closed diagnostic validation; never executes historical scripts."""
from control import *
from analysis import analyze
import guard
SUFFIXES=('seal-host.json','sealed-pins.json','admission.json','prehost.json','launch-pins.json','reservation.json','launcher.log','invocation.json','posthost.json')
def output_names():return ['pins.json','current.json','process.json','resources.jsonl','run.log','raw.toml','fresh.toml','prefix.toml']
def phase_paths(phase,cfg):return [D/(phase+'-'+n) for n in SUFFIXES]+[Path(cfg['output'])/n for n in output_names()]
def validate_predecessor(phase):
 req(phase=='probe','One diagnostic only');binding=rd(D/'predecessor-bindings.json')
 req(all(sha(n)==h for n,h in binding['sha256'].items()),'Predecessor changed')
 C=D.parent/'DIRECT-LU-REFERENCE-DIAGNOSIS';A=D.parent/'DIRECT-LU-COST-PREPARATION'
 req(rd(C/'review.json')['accepted'] is True and rd(C/'review.json')['findings']==[] and rd(C/'closure.json')['all_passed'] is True,'Diagnosis predecessor rejected')
 req(rd(A/'cost1-audit.json')['all_passed'] is False,'Original false audit must remain false')
 req(guard.pins_match(rd(A/'cost1-launch-pins.json')),'Frozen qualified inputs changed')
 return [Path(n) for n in binding['sha256']]+[D/'predecessor-bindings.json']
def execution_checks(cfg,inv,post,p,current,pre,hs,sealed,pins,pin_hash,review_hash,reservation,reservation_hash):
 s=inv['supervisor'];start=inv['monotonic_start']
 expected=[inv['python'],'-B',str(D/'guard.py'),'run',str(D/'probe-launch-pins.json'),cfg['output'],'--seconds','39','--deadline',str(start+39),'--',*cfg['command']]
 return dict(host=not pre['matches'] and not hs['matches'] and all(pre[k]==hs[k]==sealed[k] for k in ('head','master','boot_id')),
 no_processes=post['matches']==[] and all(post[k]==pre[k] for k in ('head','master','boot_id')) and set(pre['groups'])<=set(post['groups']),
 identities=current['runner']==p['runner']==s['guard_identity'] and current['child']==p['child'] and all(p[k][field] in post['groups'] for k in ('runner','child') for field in ('pgid','sid')),
 bounded=type(start) in (float,int) and 0<=inv['elapsed_seconds']<=45 and 0<=s['elapsed_seconds']<=45 and s.get('accepted') is True and 'cleanup_error' not in s,
 exit=p['returncode']==0 and p['reason']=='exit0' and s['returncode']==0,
 pins=p['pins_unchanged'] is True,
 command=p['command']==current['command']==cfg['command']==inv['command'] and p['pins_sha256']==current['pins_sha256']==pin_hash==inv['pins_sha256'],
 guard_command=inv['guard_command']==expected and str(Path(inv['python']).resolve())==str(Path(sys.executable).resolve()),
 reservation=reservation==dict(one_attempt=True,phase='probe',command=cfg['command'],pins_sha256=pin_hash,review_sha256=review_hash,max_seconds=45),
 invocation=inv['review_sha256']==review_hash and inv['reservation_sha256']==reservation_hash)
def phase_checks(phase):
 cfg=phase_config(phase);out=Path(cfg['output']);paths=phase_paths(phase,cfg);validate_predecessor(phase)
 req(all(p.is_file() for p in paths),'Missing phase evidence')
 req({p.name for p in out.iterdir()}==set(output_names()) and all(p.is_file() for p in out.iterdir()),'Output membership')
 inv=rd(D/(phase+'-invocation.json'));post=rd(D/(phase+'-posthost.json'));p=rd(out/'process.json')
 pp=D/(phase+'-launch-pins.json');pins=rd(pp);sp=D/(phase+'-sealed-pins.json');sealed=rd(sp);rp=D/(phase+'-admission.json')
 validate_review(rd(rp),sp,sealed['files']+[str(sp)])
 req(sealed['phase']==phase,'Sealed phase');req(set(pins['files'])==set(sealed['files'])|{str(sp),str(rp)} and pins['trees']==sealed['trees'],'Launch membership')
 req(all(pins['inventory'].get(n)==v for n,v in sealed['inventory'].items()),'Launch/seal drift')
 req(guard.pins_match(pins) and rd(out/'pins.json')==pins,'Actual pin mismatch')
 current=rd(out/'current.json');pre=rd(D/(phase+'-prehost.json'));hs=rd(D/(phase+'-seal-host.json'));r=D/(phase+'-reservation.json')
 checks=execution_checks(cfg,inv,post,p,current,pre,hs,sealed,pins,sha(pp),sha(rp),rd(r),sha(r))
 resources=[json.loads(line) for line in (out/'resources.jsonl').read_text().splitlines()]
 req(resources,'No resource samples');resources.append(p['terminal_memory'])
 checks['resources']=all(r['available_kib']>=6*1024**2 and r['swap_used_kib']<=1024**2 for r in resources)
 def toml(p):return tomllib.loads(p.read_text())
 A=D.parent/'DIRECT-LU-COST-PREPARATION';f=next(f for f in rd(A/'inputs.json')['fixtures'] if f['name']=='sparse96')
 result=analyze(toml(out/'raw.toml'),toml(out/'fresh.toml'),toml(out/'prefix.toml'),f,toml(A/'cost1-run/window-13-1.toml'),cfg['project'])
 checks['diagnostic_integrity']=True
 return checks,result
