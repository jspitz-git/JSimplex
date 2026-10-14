from pathlib import Path
import json,hashlib,subprocess
R=Path.cwd();E=R/'diagnostics/simplex-core-architecture/results/MA-S-2';S=E.with_name('MA-S');L=E.with_name('MA-S-LOAD')
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def rd(p):return json.loads(Path(p).read_text())
def bound(x):return all(sha(p)==s for p,s in x['sha256'].items())
def git(*a):return subprocess.check_output(['git',*a],text=True).strip()
rev=rd(E/'admission-review.json');entry=rd(E/'entry.json');freeze=rd(E/'freeze-check.json');pins=rd(E/'pins.json');host=rd(E/'host.json');source=rd(E/'source-check.json');test=rd(E/'offline-tests.json');maps=rd(E/'continuation-map.json')['old_bindings']
checks={'review_accepted':rev['accepted'] is True and rev['findings']==[] and rev['pins_sha256']==sha(E/'pins.json') and bound(rev),'entry12':entry['all_passed'] is True and len(entry['checks'])==12 and bound(entry),'freeze5':freeze['all_passed'] is True and len(freeze['checks'])==5 and bound(freeze),'source8':source['all_passed'] is True and len(source['checks'])==8 and bound(source),'synthetic80':test['all_passed'] is True and len(test['checks'])==80 and bound(test),'pins4304':len(pins['inventory'])==4304 and all(sha(p)==v['sha256'] and str(Path(p).resolve())==v['resolved'] for p,v in pins['inventory'].items()),'membership':set(rd(E/'required-paths.json'))==set(pins['inventory'])==set(pins['files'])|{str(p) for root in pins['trees'] for p in Path(root).rglob('*') if p.is_file()},'no_launch':not any((E/n).exists() for n in ['launch-context.json','numerical-review.json','sequence-reservation.json','run-1','run-2','run-3']),'old_failure_preserved':rd(S/'audit-1.json')['all_passed'] is False and rd(S/'run-1/process.json')['returncode']==1 and not (S/'run-2').exists(),'source514':len(host['master_identity'])==514 and all(sha(R/p)==s for p,s in host['master_identity'].items()),'protected6':len(host['protected'])==6 and all(sha(p)==s for p,s in host['protected'].items()),'continuation6':len(maps)==6 and all(sha(x['preserved'])==x['sha256']==rd(x['source'])['sha256'][x['path']] for x in maps),'refs':git('rev-parse','HEAD')==host['refs']['head'] and git('rev-parse','master')==host['refs']['master'],'tracked_scope':set(git('diff','--name-only','HEAD').splitlines())=={'diagnostics/simplex-core-architecture/STATUS.md','docs/superpowers/plans/2026-10-11-simplex-core-architecture.md'},'no_stage':not git('diff','--cached','--name-only'),'authored_diff_clean':subprocess.run(['git','diff','--check'],capture_output=True).returncode==0}
names=['entry.py','entry.json','host.json','continuation-map.json','STATUS.md.before-MA-S-2','roadmap.md.before-MA-S-2','prepare.py','prepare-2.py','preparation-failure.txt','source-check.json','offline-tests.py','offline-tests.json','guard.py','audit.py','launcher.py','commands.json','admission.md','ledger.md','freeze.py','freeze-check.json','pins.json','required-paths.json','admission-review.md','admission-review.json','closure.py','publication.py']
paths=[E/n for n in names]+[R/'diagnostics/simplex-core-architecture/MA-DENSELU-BIGFLOAT-SECOND-ADMISSION.md',R/'diagnostics/simplex-core-architecture/STATUS.md',R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md']
o=dict(all_passed=all(checks.values()),runtime_qualified=False,checks=checks,sha256={str(p):sha(p) for p in paths},scope='Preparation closure only; no numerical seal or launch. Original failed sequence preserved.')
with (E/'closure.json').open('x') as f:json.dump(o,f,indent=2);f.write('\n')
print(json.dumps({'checks':checks,'bindings':len(paths),'all_passed':o['all_passed']}))
if not o['all_passed']:raise SystemExit(1)
