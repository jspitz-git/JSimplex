"""New failed-GREEN preservation check; never reruns Julia or the frozen auditor."""
from pathlib import Path
import json,hashlib,sys,tomllib,subprocess
D=Path(__file__).resolve().parent;Q=D.parent/'NATIVE-PIVOT-QUALIFICATION';R=D.parents[3];RUN=Q/'runs/green'
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
a=rd(RUN/'audit.json');s=rd(RUN/'sealed.json');ad=rd(RUN/'admission.json');p=rd(RUN/'output/process.json');iv=rd(RUN/'invocation.json');lp=rd(RUN/'launch-pins.json');raw=tomllib.loads((RUN/'output/raw.toml').read_text());gs=raw['tests']['children'];sup=iv['supervisor']
res=[json.loads(x) for x in (RUN/'output/resources.jsonl').read_text().splitlines()]
err=[e for e in raw['events'] if e.get('exception')=='MethodError']
checks=dict(failed_audit_preserved=a['all_passed'] is False and a['error']=="RuntimeError('Inclusive limit/cleanup')" and bound(a),admission=ad['accepted'] is True and ad['findings']==[] and ad['phase']=='green' and ad['scope']=='exact-stage admission' and ad['pins_sha256']==sha(RUN/'sealed.json') and set(ad['sha256'])==set(s['files'])|{str(RUN/'sealed.json')} and bound(ad),sealed_inventory=all(sha(n)==v['sha256'] and str(Path(n).resolve())==v['resolved'] for n,v in s['inventory'].items()),launch_inventory=all(sha(n)==v['sha256'] and str(Path(n).resolve())==v['resolved'] for n,v in lp['inventory'].items()),preparation=bound(rd(Q/'preparation-pins-reviewed.json')) and bound(rd(Q/'review-final.json')),raw=raw['complete'] is True and raw['fatal']=='' and len(gs)==9 and sum(g['pass'] for g in gs)==5352 and sum(g['fail']+g['broken'] for g in gs)==0 and sum(g['error'] for g in gs)==1,missing=rd(Q/'budget.json')['green_assertions']-sum(g['pass'] for g in gs)==1506,error_location=gs[2]['name']=='private_spare_copy_and_failure' and gs[2]['pass']==62 and gs[2]['error']==1 and 'zero(::String)' in gs[2]['failures'][0] and 'test-support.jl:35' in gs[2]['failures'][0],after_solve=len(err)==1 and err[0]['call']=='forward_solve' and err[0]['number']==8 and err[0]['after']['kind']=='Vector{Float64}' and len(err[0]['output'])==2 and 'rhs' not in err[0],partial_work=len(raw['events'])==sum(raw['counts'].values())==289 and len(raw['equations'])==34,exit=p['returncode']==1 and p['reason']=='exit1' and p['pins_unchanged'] is True and sup['returncode']==1 and sup['accepted'] is False,no_timeout=0<iv['elapsed_seconds']<60 and not any(sup[k] for k in ['soft_timeout','hard_timeout','child_kill','guard_term','guard_kill']) and 'cleanup_error' not in sup,resources=len(res)==28 and all(z['available_kib']>=6*1024**2 and z['swap_used_kib']==0 for z in res+[p['terminal_memory']]),host=not h['matches'] and len(h['groups'])==212 and h['head']==s['head'] and h['master']==s['master'] and h['boot_id']==s['boot_id'],no_cost={z.name for z in (Q/'runs').iterdir()}=={'red','green'},actual_unchanged=not subprocess.check_output(['git','diff','--name-only','--','src','test','Project.toml','.github','diagnostics/direct-lu-markowitz/reproduce'],cwd=R,text=True).strip())
runtime=Path('/home/jspitz/.julia/juliaup/julia-1.13.0+0.aarch64.linux.gnu/share/julia/stdlib/v1.13/SparseArrays/src')
checks['source_cause']='e["rhs"]=scalar.(args[2])' in (Q/'test-support.jl').read_text() and '_isnotzero(Cx)' in (runtime/'higherorderfns.jl').read_text() and '_isnotzero' in (runtime/'SparseArrays.jl').read_text()
paths=[Path(__file__),D/'postcheck-host.json',RUN/'audit.json',RUN/'admission.json',RUN/'sealed.json',RUN/'launch-pins.json',RUN/'output/raw.toml',RUN/'output/process.json',RUN/'invocation.json',Q/'test-support.jl',Q/'tests-observed.jl',runtime/'higherorderfns.jl',runtime/'SparseArrays.jl']
save(D/'postcheck.json',dict(all_passed=all(checks.values()),qualification_accepted=False,checks=checks,sha256={str(p):sha(p) for p in paths},scope='Post-exit diagnostic preservation checks only; original GREEN audit FALSE remains authoritative'))
require(all(checks.values()),'Preservation check failed; preserve');print(dict(checks=len(checks),bindings=len(paths),diagnostic_pass=True,qualification_accepted=False))
