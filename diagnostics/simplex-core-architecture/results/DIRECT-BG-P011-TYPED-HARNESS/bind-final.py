"""Preserve intermediate documentation bindings, then seal final review inputs."""
from pathlib import Path
import hashlib,json
D=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(n,v):
 with (D/n).open('x') as f:json.dump(v,f,indent=2);f.write('\n')
fix=json.loads((D/'review-fix-provenance.json').read_text());maps={}
for n in ['ADMISSION.md','REPORT.md']:
 p=D/n;s=p.read_text();prefix=s[:s.rfind('\n\n')+1]
 expected=fix['after_sha256'][str(p)]
 if hashlib.sha256(prefix.encode()).hexdigest()!=expected:raise RuntimeError('Exact intermediate doc inverse '+n)
 q=D/(n+'.after-rendering-fix')
 with q.open('x') as f:f.write(prefix)
 maps[str(p)]={'sha256':expected,'preserved_path':str(q)}
for n in ['preparation-pins.json','required-paths.json']:
 p=D/n;q=D/(n+'.before-final-mapping')
 with q.open('xb') as f:f.write(p.read_bytes())
 maps[str(p)]={'sha256':sha(q),'preserved_path':str(q)}
initial=json.loads((D/'preparation-pins.json.before-review').read_text())
fcheck=json.loads((D/'review-fix-check.json').read_text())
correctedmaps={str(D/n):str(D/(n+'.before-review')) for n in ['preparation-pins.json','required-paths.json']}
correctedmaps.update({str(D/n):str(D/(n+'.after-rendering-fix')) for n in ['ADMISSION.md','REPORT.md']})
for n,h in fcheck['sha256'].items():
 if sha(Path(correctedmaps.get(n,n)))!=h:raise RuntimeError('Correction check mapping '+n)
save('final-mappings.json',dict(scope='Explicit intermediate bindings; no retroactive rewrites',correction_check_maps=correctedmaps,intermediate_manifest_maps=maps,all_correction_check_bindings_match=True))
paths=set(Path(n) for n in initial['sha256'])
paths.update(p for p in D.iterdir() if p.is_file() and p.name not in ['preparation-pins.json','review.json','review.md'])
paths.add(Path(fix['historical_rendering_source']))
(D/'required-paths.json').write_text(json.dumps(dict(paths=sorted(str(p) for p in paths)),indent=2)+'\n')
if not all(p.is_file() and not p.is_symlink() for p in paths):raise RuntimeError('Input absent/symlink')
(D/'preparation-pins.json').write_text(json.dumps(dict(scope='P011 typed harness preparation only; final reviewed correction inputs; not launch pins',sha256={str(p):sha(p) for p in sorted(paths)}),indent=2)+'\n')
print(json.dumps(dict(correction_check_bindings=len(fcheck['sha256']),manifest_inputs=len(paths),all_passed=True)))
