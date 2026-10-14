from pathlib import Path
import hashlib,json,subprocess,time
R=Path.cwd();E=R/'diagnostics/simplex-core-architecture/results/MA-S';OLD=E.parent/'MA-P'
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def save(p,o):
 with p.open('x') as f:json.dump(o,f,indent=2);f.write('\n')
old=json.loads((OLD/'pins.json').read_text());host=json.loads((E/'host.json').read_text())
files={Path(p) for p in old['files'] if not p.startswith(str(R)+'/')}
files|={R/p for p in host['master_identity']};files|={Path(p) for p in host['protected']}
files|={p for p in (E.parent/'MA-R').rglob('*') if p.is_file()}
files|={R/'docs/superpowers/plans/2026-10-14-ma-denselu-bigfloat.md',R/'docs/superpowers/specs/2026-10-14-ma-denselu-bigfloat-design.md',R/'diagnostics/simplex-core-architecture/MA-DENSELU-BIGFLOAT-PREPARATION.md'}
files|={E/n for n in ['driver.jl','audit.py','launcher.py','guard.py','commands.json','admission.md','host.json','offline-tests.py','offline-tests.json','prepare-pins.py']}
trees=old['trees']
for root in trees:files|={p for p in Path(root).rglob('*') if p.is_file()}
files=sorted(files)
inv={str(p):dict(resolved=str(p.resolve(strict=True)),sha256=sha(p)) for p in files}
save(E/'required-paths.json',[str(p) for p in files])
save(E/'pins.json',dict(files=[str(p) for p in files],trees=trees,inventory=inv,inputs=[]))
checks={'all_pins_exist':len(inv)==len(files),'R_candidate_tests_unchanged':all(sha(p)==s for p,s in json.loads((E.parent/'MA-R/publication.json').read_text())['sha256'].items() if '/results/MA-R/' in p),'guard_byteidentical':sha(E/'guard.py')==sha(OLD/'guard.py'),'protected6':all(sha(p)==s for p,s in host['protected'].items()),'production514':all(sha(R/p)==s for p,s in host['master_identity'].items()),'no_launch_seal_or_outputs':not any((E/n).exists() for n in ['launch-context.json','numerical-review.json','sequence-reservation.json','run-1','run-2','run-3'])}
save(E/'preparation-check.json',dict(checks=checks,all_passed=all(checks.values()),pin_count=len(files),readtime=time.time(),sha256={str(E/n):sha(E/n) for n in ['pins.json','required-paths.json','prepare-pins.py','offline-tests.json','admission.md']}))
print(json.dumps(dict(checks=checks,pins=len(files))))
if not all(checks.values()):raise SystemExit(1)
