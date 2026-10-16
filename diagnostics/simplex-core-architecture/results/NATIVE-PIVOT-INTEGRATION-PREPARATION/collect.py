"""One-shot preparation evidence collection, not historical-auditor execution."""
from pathlib import Path
import json,hashlib,subprocess
D=Path(__file__).resolve().parent;R=D.parents[3];C=D.parent/'NATIVE-PIVOT-COST';Q=D.parent/'NATIVE-PIVOT-COST-PREPARATION';G=D.parent/'NATIVE-PIVOT-GREEN2-PREPARATION/runs/green2'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def path(n):return Path(n) if Path(n).is_absolute() else R/n
def require(v,m):
 if not v:raise RuntimeError(m)
def save(p,z):
 with p.open('x') as f:json.dump(z,f,indent=2);f.write('\n')
checks={};files=set(p for p in D.rglob('*') if p.is_file());records=[Q/'runs/cost/audit.json',Q/'runs/cost/result-review.json',G/'audit.json',G/'result-review.json',C/'postcheck.json',D/'source-check.json']
for rec in records:
 z=read(rec);checks[str(rec.relative_to(R))]=z.get('accepted',z.get('all_passed')) is True
 files.add(rec)
 for field in ['sha256','evidence_sha256']:
  for n,h in z.get(field,{}).items():
   p=path(n);require(sha(p)==h,'Input binding changed '+n);files.add(p)
# Preserve only current cost closure/publication continuation bindings; old maps unchanged.
preserved={'diagnostics/simplex-core-architecture/STATUS.md':D/'STATUS.md.before-integration','docs/superpowers/plans/2026-10-11-simplex-core-architecture.md':D/'roadmap.md.before-integration'};maps=[]
for rec in [C/'closure.json',C/'publication.json']:
 z=read(rec);require(z['all_passed'] is True,'Predecessor not closed');files.add(rec)
 for n,h in z['sha256'].items():
  p=path(n);rel=str(p.relative_to(R))
  if rel in preserved:
   p=preserved[rel];maps.append(dict(record=str(rec.relative_to(R)),pointer=['sha256',n],key=n,sha256=h,preserved_path=str(p.relative_to(R))))
  require(sha(p)==h,'Cost closure binding changed '+n);files.add(p)
require(len(maps)==4,'Expected four current mappings')
save(D/'continuation-mappings.json',dict(mappings=maps,scope='Only current cost closure/publication STATUS and roadmap digests. All earlier mapping files unchanged.'));files.add(D/'continuation-mappings.json')
actual=subprocess.check_output(['git','ls-files','src','test','Project.toml','.github','diagnostics/direct-lu-markowitz/reproduce'],cwd=R,text=True).splitlines()
actual_hash={}
for n in actual:
 b=subprocess.check_output(['git','show','HEAD:'+n],cwd=R)
 require((R/n).read_bytes()==b,'Actual tree changed '+n);actual_hash[n]=sha(R/n);files.add(R/n)
save(D/'actual-baseline.json',dict(sha256=actual_hash,scope='Readtime actual tracked source/test/project/CI/direct prototype bytes equal HEAD; no numerical coverage claim.'));files.add(D/'actual-baseline.json')
manifest=read(D/'overlay-manifest.json')['candidate']
for e in manifest:require(sha(e['source'])==e['sha256'],'Overlay changed');files.add(Path(e['source']))
s=read(D/'observer-seams.json');f=Path(next(e['source'] for e in manifest if e['destination']=='src/factorization.jl')).read_text();g=f
for i in s['application_order']:
 e=s['edits'][i];require(g.count(e['before'])==e['count'],'Forward anchor');g=g.replace(e['before'],e['after'])
for i in reversed(s['application_order']):
 e=s['edits'][i];require(g.count(e['after'])==e['count'],'Inverse anchor');g=g.replace(e['after'],e['before'])
checks['observer_whole_inverse']=g==f;checks['no_stage']=not (R/'.superpowers/native-pivot-integration').exists();checks['no_runs']=not (D/'runs').exists();checks['actual_baseline']=bool(actual_hash);checks['host']=not read(D/'host.json')['matches'];checks['original_failed_green']=read(D.parent/'NATIVE-PIVOT-QUALIFICATION/runs/green/audit.json')['all_passed'] is False
save(D/'author-check.json',dict(all_passed=all(checks.values()),checks=checks,scope='Offline input bindings and whole-source inverse; no Julia/runtime proof.'))
require(all(checks.values()),'Author checks failed');files.add(D/'author-check.json')
save(D/'preparation-pins.json',dict(sha256={str(p.relative_to(R)):sha(p) for p in sorted(files)},scope='Fresh readtime input/preparation bindings, NOT launch pins.'))
print(dict(checks=len(checks),pins=len(files),actual=len(actual_hash),maps=len(maps)))
