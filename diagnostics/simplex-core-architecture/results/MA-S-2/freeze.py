from pathlib import Path
import json,hashlib,time
R=Path.cwd();E=R/'diagnostics/simplex-core-architecture/results/MA-S-2';S=E.with_name('MA-S');L=E.with_name('MA-S-LOAD')
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def save(n,o):
 with (E/n).open('x') as f:json.dump(o,f,indent=2);f.write('\n')
old=json.loads((S/'pins-reviewed.json').read_text())
newnames=['entry.py','entry.json','host.json','continuation-map.json','STATUS.md.before-MA-S-2','roadmap.md.before-MA-S-2','prepare.py','prepare-2.py','preparation-failure.txt','audit.py','launcher.py','guard.py','commands.json','offline-tests.py','offline-tests.json','source-check.json','admission.md','freeze.py']
lineage=[L/n for n in ['driver.jl','review.md','review.json','source-green.json','source-red.json','driver.diff','plan.md','entry.json','continuation-map.json','STATUS.md.before-MA-S-LOAD','roadmap.md.before-MA-S-LOAD','closure.json','publication.json']]+[R/'diagnostics/simplex-core-architecture/MA-DENSELU-BIGFLOAT-LOADER-FIX.md']+[S/n for n in ['result-review.md','result-review.json','execution-postcheck.json','execution-continuation-map.json','STATUS.md.before-MA-S-execution','roadmap.md.before-MA-S-execution','run-1/raw.toml','run-1/run.log','audit-1.json','run-1/process.json']]
files=sorted(set(old['files'])|{str(E/n) for n in newnames}|{str(p) for p in lineage})
inv={p:dict(resolved=str(Path(p).resolve(strict=True)),sha256=sha(p)) for p in files}
checks={'old4262unchanged':len(old['inventory'])==4262 and all(inv[p]==v for p,v in old['inventory'].items()),'new80synthetic':len(json.loads((E/'offline-tests.json').read_text())['checks'])==80 and json.loads((E/'offline-tests.json').read_text())['all_passed'] is True,'source8':len(json.loads((E/'source-check.json').read_text())['checks'])==8 and json.loads((E/'source-check.json').read_text())['all_passed'] is True,'no_launch':not any((E/n).exists() for n in ['launch-context.json','numerical-review.json','sequence-reservation.json','run-1','run-2','run-3']),'exact_membership':set(files)==set(files)|{str(p) for root in old['trees'] for p in Path(root).rglob('*') if p.is_file()}}
if not all(checks.values()):raise SystemExit(str(checks))
save('required-paths.json',files);save('pins.json',dict(files=files,trees=old['trees'],inventory=inv,inputs=[]))
save('freeze-check.json',dict(time=time.time(),checks=checks,all_passed=True,pin_count=len(files),sha256={str(E/n):sha(E/n) for n in newnames+['pins.json','required-paths.json']},scope='Fresh preparation hashes, not launch-context or numerical seal.'))
print(json.dumps(dict(checks=checks,pins=len(files))))
