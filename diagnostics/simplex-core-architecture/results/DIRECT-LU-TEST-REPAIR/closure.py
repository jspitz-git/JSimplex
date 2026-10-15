"""One-shot OFFLINE preparation closure after independent review; no Julia."""
from pathlib import Path
import hashlib,json,subprocess
R=Path(__file__).resolve().parents[4];D=Path(__file__).resolve().parent
A=D.parent/'DIRECT-LU-ADMISSION'
def rd(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def path(n):return Path(n) if Path(n).is_absolute() else R/n
def git(*a):return subprocess.check_output(['git',*a],cwd=R,text=True).strip()
checks={};review=rd(D/'review.json');source=rd(D/'source-check.json')
checks['independent_offline_acceptance']=review.get('accepted') is True and review.get('findings')==[]
checks['review_bindings_unchanged']=bool(review.get('sha256')) and all(sha(path(n))==h for n,h in review['sha256'].items())
checks['seventeen_source_checks']=source['all_passed'] is True and len(source['checks'])==17 and all(source['checks'].values())
checks['source_check_bindings']=all(sha(path(n))==h for n,h in source['sha256'].items())
frozen=rd(D/'frozen-inputs.json')['sha256'];baseline=rd(D.parent/'DIRECT-LU-PREPARATION/baseline.json')['sha256']
checks['all136_frozen_files_unchanged']=len(frozen)==136 and all(sha(R/n)==h for n,h in frozen.items())
checks['all514_baseline_files_unchanged']=len(baseline)==514 and all(sha(R/n)==h for n,h in baseline.items())
checks['original_red_accepted_green_failed']=rd(A/'red-audit.json')['all_passed'] is True and rd(A/'green-audit.json')['all_passed'] is False
m=rd(D/'continuation.json')['mappings']
checks['six_exact_continuation_maps']=len(m)==6 and all(sha(R/x['preserved_path'])==x['sha256']==rd(R/x['record'])['sha256'][x['key']] for x in m)
host=rd(D/'host.json')
checks['fresh_preflight_full200_groups_sessions_noJulia']=len(host['groups'])==200 and host['matches']==[]
checks['refs_unchanged']=git('rev-parse','HEAD')==host['head'] and git('rev-parse','master')==host['master']=='6f68e24e8ddac42b948da8fcc2d636c010751194'
checks['no_new_launcher_reservation_outputs']=not any((D/n).exists() for n in ('launch.py','reservation.json','run','process.json'))
checks['no_tracked_production_changes']=not git('diff','--name-only','--','src','test','Project.toml','.github')
checks['authored_diff_clean']=subprocess.run(['git','diff','--check'],cwd=R).returncode==0
status=R/'diagnostics/simplex-core-architecture/STATUS.md';roadmap=R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md'
checks['continuation_points_to_new_gate']=all('DIRECT-LU-TEST-REPAIR' in p.read_text() and '19,557' in p.read_text() for p in (status,roadmap))
paths=sorted([p for p in D.iterdir() if p.is_file() and p.name not in ('closure.json','publication.json')]+[status,roadmap,R/'diagnostics/simplex-core-architecture/DIRECT-LU-TEST-REPAIR.md'])
result=dict(all_passed=all(checks.values()),checks=checks,scope='Separate offline test repair only; runtime correctness remains unqualified',sha256={str(p.relative_to(R)):sha(p) for p in paths})
with (D/'closure.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
print(json.dumps(dict(all_passed=result['all_passed'],checks=checks,bindings=len(paths)),indent=2))
if not result['all_passed']:raise SystemExit('Closure refused')
