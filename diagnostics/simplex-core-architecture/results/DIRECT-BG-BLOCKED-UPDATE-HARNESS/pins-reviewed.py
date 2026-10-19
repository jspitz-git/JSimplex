from pathlib import Path
import json,hashlib
H=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/simplex-core-architecture/results/DIRECT-BG-BLOCKED-UPDATE-HARNESS')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,j):
 with p.open('x') as f:json.dump(j,f,indent=2);f.write('\n')
(H/'pins-reviewed.py').write_bytes(Path(__file__).read_bytes())
maps={};verified={}
for name in ['preparation-pins.json','source-check-2.json','review-first.json']:
 m=json.loads((H/name).read_text());mm={}
 for n,h in m['sha256'].items():
  p=Path(n)
  if sha(p)==h:continue
  q=H/(p.name+'.before-review')
  if not q.exists() or sha(q)!=h:raise RuntimeError(('Historical binding mismatch',name,n,h))
  mm[n]=str(q)
 maps[name]=mm;verified[name]=len(m['sha256'])
save(H/'review-fix-bindings.json',dict(all_passed=True,scope='Exact historical hashes map only to listed before-review copies; no retrospective mutation',maps=maps,verified_bindings=verified,sha256={str(H/n):sha(H/n) for n in ['driver.jl','oracle.py','control.py','audit.py','ADMISSION.md','REPORT.md','MEMORY-WORK.md','synthetic-reviewed.json','full-audit-tests-reviewed.json','source-check-final.json']}))
paths=set(json.loads((H/'required-paths.json').read_text())['paths'])
paths|={str(p) for p in H.iterdir() if p.is_file() and p.name not in ['review.json','review.md']}
req=H/'required-paths-reviewed.json';paths.add(str(req));save(req,{'paths':sorted(paths)})
save(H/'preparation-pins-reviewed.json',dict(scope='Final offline preparation, no launch admission',sha256={p:sha(Path(p)) for p in sorted(paths)}))
print('Reviewed manifest',len(paths),'exact paths; historical maps', {k:len(v) for k,v in maps.items()})
