"""One-shot corrected GREEN result closure; no numerical or auditor rerun."""
from pathlib import Path
import json,hashlib,subprocess,sys,tomllib
R=Path(__file__).resolve().parents[4];D=Path(__file__).resolve().parent;A=D.parent/'DIRECT-LU-GREEN-ADMISSION'
sys.path.insert(0,str(A));import guard
from control import sha,rd,req,save,git
checks={};review=rd(D/'review.json');post=rd(D/'postcheck.json')
checks['independent_result_accepted']=review.get('accepted') is True and review.get('findings')==[]
checks['review_bindings']=all(sha(Path(n) if Path(n).is_absolute() else R/n)==h for n,h in review['sha256'].items())
checks['all11_postchecks']=post['all_passed'] is True and len(post['checks'])==11 and all(post['checks'].values())
checks['postcheck_bindings']=all(sha(R/n)==h for n,h in post['sha256'].items())
audit=rd(A/'green-audit.json');checks['canonical15_audit_pass']=audit['all_passed'] is True and len(audit['checks'])==15 and all(audit['checks'].values())
checks['audit_bindings']=all(sha(n)==h for n,h in audit['sha256'].items())
checks['all_sealed_and_launch_pins']=all(guard.pins_match(rd(A/n)) for n in ('green-sealed-pins.json','green-launch-pins.json'))
raw=tomllib.loads((A/'green-run/raw.toml').read_text());cfg=rd(A/'config.json')['phases']['green']
checks['all19557_in12groups']=raw['completed'] and raw['fatal']=='' and raw['total_pass']==19557 and raw['total_fail']==raw['total_error']==raw['total_broken']==0 and len(raw['groups'])==12 and all(g['name']==c['name'] and [g[k] for k in ('pass','fail','error','broken')]==c['counts'] for g,c in zip(raw['groups'],cfg['groups']))
checks['exit0_bounded']=rd(A/'green-run/process.json')['returncode']==0 and rd(A/'green-invocation.json')['elapsed_seconds']<=90
h=rd(D/'final-host.json');checks['separate202_group_session_closure']=len(h['groups'])==202 and h['matches']==[] and all(h[k]==rd(A/'green-posthost.json')[k] for k in ('head','master','boot_id'))
checks['refs_unchanged']=git('rev-parse','HEAD')==h['head'] and git('rev-parse','master')==h['master']=='6f68e24e8ddac42b948da8fcc2d636c010751194'
baseline=rd(D.parent/'DIRECT-LU-PREPARATION/baseline.json')['sha256'];checks['baseline514_unchanged']=len(baseline)==514 and all(sha(R/n)==v for n,v in baseline.items())
old=D.parent/'DIRECT-LU-ADMISSION';checks['old_red_and_failed_green_preserved']=rd(old/'red-audit.json')['all_passed'] is True and rd(old/'green-audit.json')['all_passed'] is False
m=rd(D/'continuation.json')['mappings'];checks['eight_prior_continuation_maps']=len(m)==8 and all(sha(R/x['preserved_path'])==x['sha256']==rd(R/x['record'])['sha256'][x['key']] for x in m)
checks['tracked_diff_clean']=subprocess.run(['git','diff','--check'],cwd=R).returncode==0
paths=[p for p in D.rglob('*') if p.is_file() and p.name not in ('closure.json','publication.json')]+[p for p in A.glob('green-*') if p.is_file()]+[p for p in (A/'green-run').rglob('*') if p.is_file()]+[A/'stage-green-review.md']
paths += [R/'diagnostics/simplex-core-architecture/DIRECT-LU-GREEN-CORRECTNESS.md',R/'diagnostics/simplex-core-architecture/STATUS.md',R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md']
result=dict(all_passed=all(checks.values()),checks=checks,scope='Scoped component/lifecycle correctness only; no performance/full-suite/public solver acceptance',sha256={str(p.relative_to(R)):sha(p) for p in sorted(set(paths))})
save(D/'closure.json',result);print(json.dumps(dict(all_passed=result['all_passed'],checks=checks,bindings=len(result['sha256'])),indent=2));req(result['all_passed'],'Correctness closure refused')
