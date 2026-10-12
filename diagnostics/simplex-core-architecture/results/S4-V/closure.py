from pathlib import Path
import hashlib,json,subprocess
D=Path(__file__).resolve().parent;R=D.parents[3]
def h(p):
 v=hashlib.sha256()
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(1048576),b''):v.update(b)
 return v.hexdigest()
a=json.loads((D/'read-only-audit.json').read_text());ind=json.loads((D/'independent.json').read_text());host=json.loads((D/'host-after.json').read_text())
review=(D.parents[1]/'S4-READONLY-BOOTSTRAP-FEASIBILITY-REVIEW.md').read_text()
report=(D.parents[1]/'S4-READONLY-BOOTSTRAP-FEASIBILITY.md').read_text()
plan=(R/'docs/superpowers/plans/2026-10-12-hh-public-controller-attempt-contract.md').read_text()
checks={
 'audit17_pass':len(a['checks'])==17 and all(a['checks'].values()) and a['all_passed'],
 'independent8_pass':len(ind['checks'])==8 and all(ind['checks'].values()) and ind['all_passed'],
 'full656_unchanged':len(a['sha256'])==656 and all(h(p)==v for p,v in a['sha256'].items()),
 'independent_snapshot_files_unchanged':all(h(p)==v for p,v in ind['snapshot_sha256'].items()),
 'review_accepted':'no actionable findings or unresolved Critical, Important or Minor defects' in ' '.join(review.split()),
 'qualification_not_enabled':a['bootstrap_qualified'] is False and a['numerical_authorization'] is False and 'No launcher is frozen or' in report,
 'next_source_only_no_bootstrap_loop':'do not reopen the sandbox/bootstrap route' in plan and 'NO numerical plan or' in plan,
 'host_full_groups_absent':not(host['old_pids'] or host['old_groups'] or host['julia']),
 'master_unchanged':subprocess.check_output(['git','rev-parse','master'],cwd=R,text=True).strip()=='0eb75c3190096946b0e91e5360230ccd7166f298',
 'production_test_CI_unchanged':not subprocess.check_output(['git','diff','master','--','src','test','.github'],cwd=R,text=True),
}
files=[p for p in D.iterdir() if p.is_file()]+[D.parents[1]/n for n in ['S4-READONLY-BOOTSTRAP-FEASIBILITY.md','S4-READONLY-BOOTSTRAP-FEASIBILITY-REVIEW.md','STATUS.md']]+[R/'docs/superpowers/plans'/n for n in ['2026-10-11-simplex-core-architecture.md','2026-10-12-hh-public-controller-attempt-contract.md']]
with (D/'closure.json').open('x') as f:json.dump({'checks':checks,'all_passed':all(checks.values()),'sha256':{str(p):h(p) for p in files}},f,indent=2);f.write('\n')
print(json.dumps({'checks':len(checks),'all_passed':all(checks.values())}));assert all(checks.values())
