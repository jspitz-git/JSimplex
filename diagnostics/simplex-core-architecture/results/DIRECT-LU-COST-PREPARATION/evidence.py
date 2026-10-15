"""New read-only evidence validator. Never calls any historical executable."""
from control import *
from analysis import matrix,window_ok,summarize,qualify
import guard
SUFFIXES=('seal-host.json','sealed-pins.json','admission.json','prehost.json','launch-pins.json','reservation.json','launcher.log','invocation.json','posthost.json')
def output_names():
 return ['pins.json','current.json','process.json','resources.jsonl','run.log','raw.toml']+[f'{prefix}-{c}.toml' for c in range(1,25) for prefix in ('started','cell')]+[f'window-{c}-{w}.toml' for c in range(1,25) for w in range(1,21)]
def phase_paths(phase,cfg):
 return [D/(phase+'-'+n) for n in SUFFIXES]+[Path(cfg['output'])/n for n in output_names()]
def validate_predecessor(phase):
 binding=rd(D/'predecessor-bindings.json')
 req(all(sha(n)==h for n,h in binding['sha256'].items()),'Correctness predecessor changed')
 prev=D.parent/'DIRECT-LU-GREEN-CORRECTNESS';a=D.parent/'DIRECT-LU-GREEN-ADMISSION'
 req(rd(prev/'review.json')['accepted'] is True and rd(prev/'review.json')['findings']==[],'Correctness review rejected')
 req(rd(prev/'closure.json')['all_passed'] is True and rd(a/'green-audit.json')['all_passed'] is True,'Correctness closure rejected')
 req(guard.pins_match(rd(a/'green-launch-pins.json')),'Qualified sources changed')
 paths=[Path(n) for n in binding['sha256']]+[D/'predecessor-bindings.json']
 if phase=='cost2':
  audit=rd(D/'cost1-audit.json');req(audit['all_passed'] is True,'First cost attempt not qualified')
  req(all(sha(n)==h for n,h in audit['sha256'].items()),'First cost evidence changed')
  checks,_=phase_checks('cost1');req(all(checks.values()),'First cost evidence invalid')
  paths += [D/'cost1-audit.json']+[Path(n) for n in audit['sha256']]
 return paths

def phase_checks(phase):
 cfg=phase_config(phase);out=Path(cfg['output']);paths=phase_paths(phase,cfg)
 req(all(p.is_file() for p in paths),'Missing phase evidence')
 req({p.name for p in out.iterdir()}==set(output_names()) and all(p.is_file() for p in out.iterdir()),'Unexpected output membership')
 inv=rd(D/(phase+'-invocation.json'));post=rd(D/(phase+'-posthost.json'));p=rd(out/'process.json');s=inv['supervisor']
 pin_path=D/(phase+'-launch-pins.json');pins=rd(pin_path);sp=D/(phase+'-sealed-pins.json');sealed=rd(sp);rp=D/(phase+'-admission.json')
 validate_review(rd(rp),sp,sealed['files']+[str(sp)])
 req(sealed['phase']==phase,'Wrong sealed phase')
 req(set(pins['files'])==set(sealed['files'])|{str(sp),str(rp)} and pins['trees']==sealed['trees'],'Launch membership')
 req(all(pins['inventory'].get(n)==v for n,v in sealed['inventory'].items()),'Launch/seal drift')
 current=rd(out/'current.json');pre=rd(D/(phase+'-prehost.json'));hs=rd(D/(phase+'-seal-host.json'));reservation=D/(phase+'-reservation.json')
 resources=[json.loads(line) for line in (out/'resources.jsonl').read_text().splitlines()]+[p['terminal_memory']]
 checks=dict(complete=True,review=True,host=not pre['matches'] and not hs['matches'] and all(pre[k]==hs[k]==sealed[k] for k in ('head','master','boot_id')),
  no_processes=post['matches']==[] and all(post[k]==pre[k] for k in ('head','master','boot_id')),
  identities=current['runner']==p['runner']==s['guard_identity'] and current['child']==p['child'] and all(p[k][field] in post['groups'] for k in ('runner','child') for field in ('pgid','sid')),
  bounded=inv['elapsed_seconds']<=90 and s['elapsed_seconds']<=90 and s.get('accepted') is True and 'cleanup_error' not in s,
  exit=p['returncode']==0 and p['reason']=='exit0' and s['returncode']==0,
  pins=p['pins_unchanged'] is True and guard.pins_match(pins) and rd(out/'pins.json')==pins,
  command=p['command']==current['command']==cfg['command']==inv['command'] and p['pins_sha256']==current['pins_sha256']==sha(pin_path)==inv['pins_sha256'],
  resources=all(r['available_kib']>=6*1024**2 and r['swap_used_kib']<=1024**2 for r in resources),
  raw=raw_ok(tomllib.loads((out/'raw.toml').read_text()),phase,cfg),
  reservation=rd(reservation)==dict(one_attempt=True,phase=phase,command=cfg['command'],pins_sha256=sha(pin_path),review_sha256=sha(rp),max_seconds=90),
  invocation=inv['review_sha256']==sha(rp) and inv['reservation_sha256']==sha(reservation))
 results=[];fixtures=rd(D/'inputs.json')['fixtures'];cell=0;process=1 if phase=='cost1' else 2
 for f in fixtures:
  matrices=[(matrix(m),matrix(m,True)) for m in f['matrices']]
  for manager in ('FT','SS','BG'):
   for backend in ('native','markowitz'):
    cell+=1;identity=dict(fixture=f['name'],manager=manager,backend=backend)
    req(tomllib.loads((out/f'started-{cell}.toml').read_text())==identity,'Cell start')
    req(tomllib.loads((out/f'cell-{cell}.toml').read_text())==dict(identity,windows=20),'Cell completion')
    rows=[]
    for w in range(1,21):
     row=tomllib.loads((out/f'window-{cell}-{w}.toml').read_text());window_ok(row,f,process,(w+1)//2,1+(w-1)%2,matrices);rows.append(row)
    results.append(dict(identity,statistics=summarize(rows)))
 checks['all_11520_exact_residuals']=True;checks['all_480_schedules_modes_metrics']=True
 return checks,results
