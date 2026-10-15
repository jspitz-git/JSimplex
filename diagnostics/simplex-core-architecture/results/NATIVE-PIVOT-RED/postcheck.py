"""New saved-result author check. No Julia or previous checker/auditor execution."""
from pathlib import Path
import json,hashlib,sys,tomllib,subprocess
D=Path(__file__).resolve().parent;Q=D.parent/'NATIVE-PIVOT-QUALIFICATION';R=D.parents[3];RUN=Q/'runs/red'
def rd(p):return json.loads(p.read_text())
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def bound(z):return all(sha(Path(n) if Path(n).is_absolute() else R/n)==v for n,v in z['sha256'].items())
def require(x,m):
 if not x:raise RuntimeError(m)
def save(p,z):
 with p.open('x') as f:json.dump(z,f,indent=2);f.write('\n')
sys.path.insert(0,str(Q));from control_reviewed import full_host
h=full_host(rd(RUN/'posthost.json')['groups']);save(D/'postcheck-host.json',h)
a=rd(RUN/'audit.json');s=rd(RUN/'sealed.json');ad=rd(RUN/'admission.json');p=rd(RUN/'output/process.json');iv=rd(RUN/'invocation.json');lp=rd(RUN/'launch-pins.json');raw=tomllib.loads((RUN/'output/raw.toml').read_text());g=raw['tests']['children'][0]
checks=dict(audit=a['all_passed'] is True and a['error']=='' and bound(a),admission=ad['accepted'] is True and ad['findings']==[] and ad['scope']=='exact-stage admission' and ad['phase']=='red' and ad['pins_sha256']==sha(RUN/'sealed.json') and set(ad['sha256'])==set(s['files'])|{str(RUN/'sealed.json')} and bound(ad),sealed_inventory=all(sha(n)==v['sha256'] and str(Path(n).resolve())==v['resolved'] for n,v in s['inventory'].items()),launch_inventory=all(sha(n)==v['sha256'] and str(Path(n).resolve())==v['resolved'] for n,v in lp['inventory'].items()),preparation=bound(rd(Q/'preparation-pins-reviewed.json')) and bound(rd(Q/'review-final.json')),raw=raw['complete'] is True and raw['fatal']=='' and g['fail']==4 and g['pass']==g['error']==g['broken']==0 and len(raw['tests']['children'])==1,markers=all(k in m for k,m in zip(['native_pivot_policy','_NativePivotPolicy','pivot_policy','_native_lu'],g['failures'])) and len(g['failures'])==4,no_selected_work=raw['counts']=={} and raw['events']==raw['equations']==[],exit=p['returncode']==1 and p['reason']=='exit1' and p['pins_unchanged'] is True and iv['supervisor']['returncode']==0,cap=0<iv['elapsed_seconds']<=30 and iv['supervisor']['accepted'] is True,resources=all(z['available_kib']>=6*1024**2 and z['swap_used_kib']<=1024**2 for z in a['result']['resources']+[p['terminal_memory']]),host=not h['matches'] and len(h['groups'])==210 and h['head']==s['head'] and h['master']==s['master'] and h['boot_id']==s['boot_id'],only_red={z.name for z in (Q/'runs').iterdir()}=={'red'},actual_unchanged=not subprocess.check_output(['git','diff','--name-only','--','src','test','Project.toml','.github','diagnostics/direct-lu-markowitz/reproduce'],cwd=R,text=True).strip())
paths=[Path(__file__),D/'postcheck-host.json',RUN/'audit.json',RUN/'admission.json',RUN/'sealed.json',RUN/'launch-pins.json',RUN/'output/raw.toml',RUN/'output/process.json',RUN/'invocation.json']
save(D/'postcheck.json',dict(all_passed=all(checks.values()),checks=checks,sha256={str(p):sha(p) for p in paths},scope='New post-exit supplemental check, not a launch pin'))
require(all(checks.values()),'Postcheck failed; preserve');print(dict(checks=len(checks),bindings=len(paths),all_passed=True))
