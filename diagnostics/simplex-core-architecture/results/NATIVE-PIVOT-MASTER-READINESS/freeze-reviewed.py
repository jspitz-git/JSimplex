"""Separate canonical readiness inventory after preserved review amendment."""
from control import *
old=rd(D/'preparation-pins.json.before-review');maps=[]
for name in ['oracle.py','control.py','audit.py','finalize.py','REPORT.md','continuation-text.md','preparation-pins.json','required-paths.json']:
 before=D/(name+'.before-review');maps.append(dict(original=str(D/name),sha256=sha(before),preserved=str(before),rule='Only this exact prior hash maps to preserved bytes; current canonical hashes bind corrected files'))
save(D/'review-amendment-mappings.json',maps)
require(rd(D/'review-amendment-tests.json')['all_passed'],'Amendment tests')
# Historical inventories remain immutable records, not current launch admissions.
files=set(old['sha256'])|{str(p) for p in D.iterdir() if p.is_file()}
files.discard(str(D/'preparation-pins.json'))
files.add(str(D/'required-paths.json'))
paths=sorted(files)
(D/'required-paths.json').write_text(json.dumps(dict(paths=paths),indent=2)+'\n')
(D/'preparation-pins.json').write_text(json.dumps(dict(scope='Corrected offline readiness inputs, not a launch seal',sha256={n:sha(path(n)) for n in paths}),indent=2)+'\n')
require(bindings(rd(D/'preparation-pins.json')),'Canonical drift')
print('Corrected canonical readiness inputs',len(paths),'all matched; no seal or run')
