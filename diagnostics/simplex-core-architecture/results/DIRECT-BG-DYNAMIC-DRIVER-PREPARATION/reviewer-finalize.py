from pathlib import Path
import hashlib,json
D=Path(__file__).resolve().parent
R=D.parents[3]
def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def resolved(n):return Path(n) if Path(n).is_absolute() else R/n
manifest=D/'preparation-pins.json'
j=json.loads(manifest.read_text())
required=json.loads((D/'required-paths.json').read_text())['paths']
assert set(j['sha256'])==set(required)
assert len(j['sha256'])==1867
assert all(digest(resolved(n))==h for n,h in j['sha256'].items())
stages=json.loads((D/'stages.json').read_text())
assert [len(stages[k]['sha256']) for k in ('red','green')]==[75,81]
for s in stages.values():
 p=Path(s['path'])
 assert {str(f.relative_to(p)) for f in p.rglob('*') if f.is_file()}==set(s['sha256'])
 assert all(digest(p/n)==h for n,h in s['sha256'].items())
assert not (D/'runs').exists()
assert not (D/'review.json').exists()
assert json.loads((D/'source-check.json').read_text())['all_passed'] is True
assert json.loads((D/'offline-tests.json').read_text())['all_passed'] is True
bound=dict(j['sha256']);bound[str(manifest)]=digest(manifest)
files={str(p) for p in D.rglob('*') if p.is_file()}
extra=sorted(files-set(bound))
evidence={n:digest(n) for n in extra}
assert files==({n for n in bound if Path(n).parent==D}|set(evidence))
v=dict(accepted=True,findings=[],scope='dynamic BG driver preparation',pins_sha256=digest(manifest),sha256=bound,evidence_sha256=evidence)
with (D/'review.json').open('x') as f:json.dump(v,f,indent=2);f.write('\n')
assert all(digest(resolved(n))==h for n,h in bound.items())
assert all(digest(n)==h for n,h in evidence.items())
assert {str(p) for p in D.rglob('*') if p.is_file()}==files|{str(D/'review.json')}
print(json.dumps(dict(accepted=True,manifest_files=len(j['sha256']),review_primary_bindings=len(bound),supplementary_bindings=len(evidence),directory_files=len(files)+1,pins_sha256=digest(manifest),review_sha256=digest(D/'review.json'))))
