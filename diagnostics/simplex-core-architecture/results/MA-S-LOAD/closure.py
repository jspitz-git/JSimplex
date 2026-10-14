from pathlib import Path
import json,hashlib,subprocess
R=Path.cwd();E=R/'diagnostics/simplex-core-architecture/results/MA-S-LOAD';S=E.with_name('MA-S')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text())
def git(*a):return subprocess.check_output(['git',*a],text=True).strip()
def bound(d):return all(sha(p)==s for p,s in d['sha256'].items())
entry=read(E/'entry.json');green=read(E/'source-green.json');review=read(E/'review.json');host=read(S/'host.json');maps=read(E/'continuation-map.json')['old_bindings'];old=(S/'driver.jl').read_text();new=(E/'driver.jl').read_text();inverse=new
for a,b in green['edits']:inverse=inverse.replace(b,a)
checks={'entry12':entry['all_passed'] is True and len(entry['checks'])==12 and bound(entry),'source11':green['all_passed'] is True and len(green['checks'])==11 and bound(green),'independent_review':review['accepted'] is True and review['findings']==[] and bound(review),'whole_inverse':inverse==old,'two_outer_boundaries':new.count('Base.invokelatest(')==2 and new.split('function main()')[0]==old.split('function main()')[0],'original_failure_preserved':read(S/'audit-1.json')['all_passed'] is False and read(S/'run-1/process.json')['returncode']==1,'no_runtime_output':not any((E/n).exists() for n in ['run-1','sequence-reservation.json','launch-context.json','numerical-review.json']),'no_original_retry':not any((S/n).exists() for n in ['run-2','run-3','aggregate.json']),'source514':len(host['master_identity'])==514 and all(sha(R/p)==s for p,s in host['master_identity'].items()),'protected6':len(host['protected'])==6 and all(sha(p)==s for p,s in host['protected'].items()),'continuation6':len(maps)==6 and all(sha(x['preserved'])==x['sha256']==read(x['source'])['sha256'][x['path']] for x in maps),'refs':git('rev-parse','HEAD')==entry['host']['refs']['head'] and git('rev-parse','master')==entry['host']['refs']['master'],'tracked_scope':set(git('diff','--name-only','HEAD').splitlines())=={'diagnostics/simplex-core-architecture/STATUS.md','docs/superpowers/plans/2026-10-11-simplex-core-architecture.md'},'no_stage':not git('diff','--cached','--name-only'),'authored_diff_clean':subprocess.run(['git','diff','--check'],capture_output=True).returncode==0}
names=['entry.py','entry.json','continuation-map.json','STATUS.md.before-MA-S-LOAD','roadmap.md.before-MA-S-LOAD','prepare.py','driver.jl','driver.diff','source-red.json','source-green.json','plan.md','ledger.md','review.md','review.json','closure.py','publication.py']
paths=[E/n for n in names]+[R/'diagnostics/simplex-core-architecture/MA-DENSELU-BIGFLOAT-LOADER-FIX.md',R/'diagnostics/simplex-core-architecture/STATUS.md',R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md']
o=dict(all_passed=all(checks.values()),runtime_qualified=False,checks=checks,sha256={str(p):sha(p) for p in paths},scope='Offline loader correction only; original numerical failure preserved.')
with (E/'closure.json').open('x') as f:json.dump(o,f,indent=2);f.write('\n')
print(json.dumps({'checks':checks,'bindings':len(paths),'all_passed':o['all_passed']}))
if not o['all_passed']:raise SystemExit(1)
