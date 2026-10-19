"""Separate canonical offline manifest; prior manifests and failed review stay frozen."""
from pathlib import Path
import sys
D=Path(__file__).resolve().parent;sys.path.insert(0,str(D));import control as c
initial=c.rd(D/'preparation-pins.json');mapping=c.rd(D/'review-fix-map.json')['mapping'];paths=set()
for n,h in initial['sha256'].items():
 preserved=mapping[n]['preserved'] if n in mapping else n
 c.require(c.sha(preserved)==h,'Initial preserved identity '+n);paths.add(preserved)
paths.update(str(p) for p in D.iterdir() if p.is_file())
# Required-list self binding is noncircular: list excludes itself, manifest adds it.
paths=sorted(paths);required=D/'required-paths-reviewed.json';manifest=D/'preparation-pins-reviewed.json'
c.require(not (D/'runs').exists() and not (D/'outers').exists(),'No runtime artifacts')
c.save(required,dict(paths=sorted(paths+[str(required)])))
paths=sorted(paths+[str(required)])
c.save(manifest,dict(sha256={p:c.sha(p) for p in paths},scope='Canonical offline preparation only; no launch admission; old identities preserved through explicit before mapping'))
print('Canonical offline paths:',len(paths))
