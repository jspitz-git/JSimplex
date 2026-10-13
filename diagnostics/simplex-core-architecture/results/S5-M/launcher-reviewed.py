"""S5-M single exclusive admission; no automatic retry or candidate rewrite."""
from pathlib import Path
import hashlib,json,subprocess,sys
R=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl');H=Path(__file__).resolve().parent
B=R/'.superpowers/simplex-core-architecture/S5-M';OUT=B/'qualification-1';PINS=B/'pins-reviewed.json'
G=R/'diagnostics/simplex-core-architecture/reproduce/guarded_run.py'
W=Path('/home/jspitz/.codex/worktrees/basis-update-chain-bench/JSimplex.jl/diagnostics/basis-memory/reproduce/julia.sh')
C=H.parent/'S5-L/candidate.jl';EXPECTED='b553d449a0db620bfae1970861806a778bbf45d36465026e8b4a540e4b4f4288'
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def main():
 assert sha(C)==EXPECTED
 mode,=sys.argv[1:]
 if mode=='freeze':
  B.mkdir(parents=True,exist_ok=True)
  old=json.loads((H.parent/'S5-L/evidence.json').read_text())['sha256']
  assert all(sha(p)==v for p,v in old.items())
  files=set(map(Path,old))|{p for p in H.iterdir() if p.is_file()}|{C,G,W,W.parents[3]/'.superpowers/basis-chain-cost/julia.sh'}
  previous=json.loads((H.parent/'S5-I/master-1/pins.json').read_text())['inventory']
  files|={Path(p) for p in previous if not Path(p).is_relative_to(R) and not Path(p).is_relative_to('/home/jspitz/JSimplex.jl/src') and not Path(p).is_relative_to('/home/jspitz/JSimplex.jl/test')}
  files|={p for p in (H.parent/'S5-L').rglob('*') if p.is_file()}
  files|={R/'diagnostics/simplex-core-architecture/S5-DUAL-AUXILIARY-PENDING-OBSERVER-PREPARATION-REVIEW.md',R/'docs/superpowers/plans/2026-10-13-dual-auxiliary-pending-observer-qualification.md'}
  cmd=[sys.executable,str(G),'freeze',str(PINS)]
  for tree in ('src','test'):cmd+=['--tree',str(R/tree)]
  for p in sorted(files):cmd+=['--file',str(p)]
  for name in ('big.mps','largo.mps','AnyMOD.mps'):cmd+=['--forbidden','/home/jspitz/mps/'+name]
  subprocess.run(cmd,check=True)
 elif mode=='run':
  review=json.loads((H/'prelaunch-acceptance.json').read_text())
  assert review['accepted'] is True and review['unresolved_findings']==[]
  assert all(sha(p)==v for p,v in review['reviewed_sha256'].items())
  assert sha(PINS)==review['pins_sha256']
  # Exclusive guard directory reserves the only admitted attempt even on failure.
  assert not OUT.exists()
  command=['/bin/bash',str(W),'--compiled-modules=existing','--threads=1','--gcthreads=1,0','--heap-size-hint=2G','--project='+str(R),str(C),str(OUT/'report.toml')]
  raise SystemExit(subprocess.call([sys.executable,str(G),'run',str(PINS),str(OUT),'--seconds','120','--',*command]))
 else:raise ValueError(mode)
if __name__=='__main__':main()
