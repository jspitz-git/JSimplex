"""New post-exit supplement and portable capture; never reruns the admitted auditor."""
from pathlib import Path
import sys,shutil
E=Path(__file__).resolve().parent;D=E.parent/'DIRECT-LU-BACKEND-PREPARATION';sys.path.insert(0,str(D))
from control import *
import guard
from fractions import Fraction as Q
out=D/'probe-run';portable=E/'probe-run';portable.mkdir(exist_ok=False)
paths=sorted(p for p in out.iterdir() if p.is_file())
for p in paths:shutil.copyfile(p,portable/p.name)
a=rd(D/'probe-audit.json');p=rd(out/'process.json');inv=rd(D/'probe-invocation.json');oldhost=rd(D/'probe-posthost.json')
h=host(oldhost['groups']);save(E/'post-host.json',h)
base=rd(E.parent/'DIRECT-LU-PREPARATION/baseline.json')['sha256']
checks=dict(portable_identical=all(sha(x)==sha(portable/x.name) for x in paths),
 full_launch_pins=guard.pins_match(rd(D/'probe-launch-pins.json')),
 audit_bindings=all(sha(n)==s for n,s in a['sha256'].items()),
 baseline514=len(base)==514 and all(sha(R/n)==s for n,s in base.items()),
 group_session_closure=not h['matches'] and set(oldhost['groups'])<=set(h['groups']) and all(p[k][f] in h['groups'] for k in ('runner','child') for f in ('pgid','sid')),
 refs_boot=all(h[k]==rd(E/'entry-host.json')[k] for k in ('head','master','boot_id')),
 original_cost_false=rd(E.parent/'DIRECT-LU-COST-PREPARATION/cost1-audit.json')['all_passed'] is False,
 no_cost2=not any((E.parent/'DIRECT-LU-COST-PREPARATION').glob('cost2-*')),
 process_complete=p['returncode']==0 and inv['supervisor']['accepted'] is True and inv['elapsed_seconds']<=45,
 diagnostic_audit=a['all_passed'] is True)
resources=[rdict for rdict in map(__import__('json').loads,(out/'resources.jsonl').read_text().splitlines())]+[p['terminal_memory']]
summary=dict(audit_accepted=a['all_passed'],audit_checks=a['checks'],exit=p['returncode'],inclusive_seconds=inv['elapsed_seconds'],resource_samples=len(resources)-1,min_available_kib=min(r['available_kib'] for r in resources),max_swap_kib=max(r['swap_used_kib'] for r in resources),groups=len(h['groups']))
if a.get('result'):
 r=a['result'];summary.update(failed_residuals=r['failed_residuals'],comparisons=r['comparisons'],residuals=[{k:x[k] for k in ('name','passed','max_abs','bound','ratio')} for x in r['residuals']],decomposition={k:dict(factor_identity_exact=v['factor_identity_exact'],factor_identity_max=v['factor_identity_max'],**{name:str(max(map(lambda x:abs(Q(x)),v[name]))) for name in ('representation_action','combined_application','scaled_original')}) for k,v in r['decomposition'].items()})
paths += [D/n for n in ('probe-audit.json','probe-invocation.json','probe-reservation.json','probe-launch-pins.json','probe-admission.json','probe-sealed-pins.json')]
paths += [E/'post-host.json',Path(__file__)]+list(portable.iterdir())
save(E/'postcheck.json',dict(all_passed=all(checks.values()),checks=checks,summary=summary,scope='Post-exit supplement, not a launch pin or rerun of canonical auditor',sha256={str(x):sha(x) for x in paths}))
print(__import__('json').dumps(summary,indent=2));req(all(checks.values()),'Postcheck rejected; preserve and stop')
