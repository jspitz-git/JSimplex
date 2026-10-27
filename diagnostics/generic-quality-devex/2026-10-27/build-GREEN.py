from pathlib import Path
import sys,json,shutil,hashlib
D=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/generic-quality-devex/2026-10-27')
def need(x,s):
 if not x:raise RuntimeError(s)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
red=json.loads((D/'RED-run/audit.json').read_text());need(red['accepted'] and red['expected_failures']==6,'witnessed six RED cost failures')
r=json.loads((D/'result-review.json').read_text());need(r['accepted'] and r['findings']==[],'independent measurement review')
for p,h in r['bindings'].items():need(sha(p)==h,'review binding '+p)
shutil.copytree(D/'RED',D/'GREEN');changes=json.loads((D/'changes.json').read_text())
for key in ['A1','A2','B','C']:
 x=changes[key];p=D/'GREEN/src'/x['file'];s=p.read_text();need(s.count(x['old'])==1,'unique production seam '+key);p.write_text(s.replace(x['old'],x['new']))
base={str(p.relative_to(D/'baseline')):sha(p) for p in (D/'baseline').rglob('*') if p.is_file()};green={str(p.relative_to(D/'GREEN')):sha(p) for p in (D/'GREEN').rglob('*') if p.is_file()};names=sorted(n for n in base.keys()|green.keys() if base.get(n)!=green.get(n));expected=sorted(['src/dual_simplex.jl','src/simplex_numerics.jl','src/primal_simplex.jl','test/generic_quality_devex_tests.jl','test/runtests.jl']);need(names==expected,'exact five changed paths')
for n in ['src/dual_simplex.jl','src/simplex_numerics.jl','src/primal_simplex.jl']:
 s=(D/'GREEN'/n).read_text()
 for key in reversed(['A1','A2','B','C']):
  x=changes[key]
  if n=='src/'+x['file']:need(s.count(x['new'])==1,'unique inverse '+key);s=s.replace(x['new'],x['old'])
 need(s==(D/'baseline'/n).read_text(),'whole-source exact inverse '+n)
(D/'source-inverse.json').write_text(json.dumps(dict(accepted=True,names=names,candidate_sha256={n:green[n] for n in names},whole_stage=green),indent=2,sort_keys=True)+'\n')
shutil.copyfile(__file__,D/'build-GREEN.py');print('Separate GREEN source stage exact inverse; changed',names)
