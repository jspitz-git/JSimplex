"""Supplemental post-exit integrity checks, not a launch input or old audit rerun."""
from pathlib import Path
import sys,json,shutil,tomllib
Q=Path(__file__).resolve().parent;D=Q.parent/'NATIVE-ACCURACY-PREPARATION';sys.path.insert(0,str(D))
from control import sha,rd,save,host,R,req
import guard
out=Q/'accuracy-run';inv=rd(Q/'accuracy-invocation.json');post=rd(Q/'accuracy-posthost.json');audit=rd(Q/'accuracy-audit.json')
fresh=host(post['groups']);save(Q/'result-host.json',fresh)
pins=rd(Q/'accuracy-launch-pins.json');process=rd(out/'process.json');raw=tomllib.loads((out/'raw.toml').read_text()) if (out/'raw.toml').exists() else None
checks=dict(no_processes=not fresh['matches'],full_groups_sessions=set(post['groups'])<=set(fresh['groups']),refs_boot=all(fresh[k]==post[k] for k in ('head','master','boot_id')),all_launch_pins=guard.pins_match(pins),master_unchanged=fresh['master']=='6f68e24e8ddac42b948da8fcc2d636c010751194',one_reservation=rd(Q/'accuracy-reservation.json')['one_attempt'] is True,inclusive_limit=inv['elapsed_seconds']<=45,original_cost_false=rd(D.parent/'DIRECT-LU-COST-PREPARATION/cost1-audit.json')['all_passed'] is False)
portable=Q/'portable';portable.mkdir(exist_ok=False)
files=sorted(p for p in out.iterdir() if p.is_file())
for p in files:shutil.copyfile(p,portable/p.name)
checks['portable_exact']=all(sha(p)==sha(portable/p.name) for p in files)
result=dict(all_passed=all(checks.values()),checks=checks,run_integrity=audit['all_passed'],process_exit=process['returncode'],process_reason=process['reason'],raw_complete=raw is not None and raw.get('completed') is True,counts=raw.get('counts') if raw else None,elapsed_seconds=inv['elapsed_seconds'],portable_files=len(files),accuracy=audit.get('result',{}).get('accuracy'),cost_interpretable=audit.get('result',{}).get('interpretable_cost'),sha256={str(p):sha(p) for p in [Path(__file__),Q/'accuracy-audit.json',Q/'accuracy-invocation.json',Q/'result-host.json',*files,*sorted(portable.iterdir())]},scope='Post-exit supplemental reconciliation and portable copy; not retrospective launch pins or a numerical rerun')
save(Q/'postcheck.json',result);req(result['all_passed'],'Postcheck failed; preserve');print(json.dumps({k:v for k,v in result.items() if k!='sha256'}))
