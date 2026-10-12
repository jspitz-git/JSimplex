"""S5-I: new exclusive GREEN/master runs; no automatic retry."""
from pathlib import Path
import hashlib,json,subprocess,sys,tomllib
ROOT=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl');HERE=Path(__file__).resolve().parent
MAIN=Path('/home/jspitz/JSimplex.jl');BASE=ROOT/'.superpowers/simplex-core-architecture/S5-I'
GUARD=ROOT/'diagnostics/simplex-core-architecture/reproduce/guarded_run.py'
WRAPPER=Path('/home/jspitz/.codex/worktrees/basis-update-chain-bench/JSimplex.jl/diagnostics/basis-memory/reproduce/julia.sh')
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def main():
 mode,label=sys.argv[1:];assert label in ('green-1','master-1')
 target=ROOT if label=='green-1' else MAIN
 pins=BASE/(label+'-pins.json');out=BASE/label
 expected=tomllib.loads((HERE/'expected.toml').read_text())
 assert sha(target/'test/simplex_precision_state_tests.jl')==expected['candidate']
 if mode=='freeze':
  BASE.mkdir(parents=True,exist_ok=True)
  old=json.loads((HERE.parent/'S5-H/evidence.json').read_text())['sha256']
  for p,v in old.items():
   assert sha(p)==(expected['candidate'] if p==str(ROOT/'test/simplex_precision_state_tests.jl') else v),p
  files=set(map(Path,old))|{p for p in HERE.iterdir() if p.is_file()}
  files|={GUARD,WRAPPER,WRAPPER.parents[3]/'.superpowers/basis-chain-cost/julia.sh'}
  files|={target/p for p in ('Project.toml','Manifest.toml','LocalPreferences.toml','.vscode/settings.json')}
  files|={ROOT/'diagnostics/simplex-core-architecture/S5-PRECISION-JOURNAL-INTERRUPTION-TEST-PREPARATION-REVIEW.md'}
  runtime=Path('/home/jspitz/.julia/juliaup/julia-1.13.0+0.aarch64.linux.gnu')
  files|={runtime/'share/julia/stdlib/v1.13/Test/src/Test.jl'}
  if label=='master-1':
   green=json.loads((BASE/'green-1/pins.json').read_text())['inventory']
   accepted=json.loads((HERE/'green-1-audit.json').read_text());assert accepted['all_passed']
   relative={str(Path(p).relative_to(ROOT)):v['sha256'] for p,v in green.items() if Path(p).is_relative_to(ROOT/'src') or Path(p).is_relative_to(ROOT/'test')}
   actual={str(p.relative_to(target)) for tree in ('src','test') for p in (target/tree).rglob('*') if p.is_file()}
   current={str(p.relative_to(ROOT)) for tree in ('src','test') for p in (ROOT/tree).rglob('*') if p.is_file()}
   assert actual==current==set(relative)
   assert all(sha(target/p)==sha(ROOT/p)==v for p,v in relative.items())
   comparison=HERE/'master-source-comparison.json'
   with comparison.open('x') as f:json.dump({'all_passed':True,'sha256':relative,'GREEN_pins_sha256':sha(BASE/'green-1/pins.json'),'GREEN_audit_sha256':sha(HERE/'green-1-audit.json')},f,indent=2);f.write('\n')
   files.add(comparison)
  trees={ROOT/'src',ROOT/'test',target/'src',target/'test'}
  cmd=[sys.executable,str(GUARD),'freeze',str(pins)]
  for tree in sorted(trees):cmd+=['--tree',str(tree)]
  for p in sorted(files):cmd+=['--file',str(p)]
  for n in ('big.mps','largo.mps','AnyMOD.mps'):cmd+=['--forbidden','/home/jspitz/mps/'+n]
  subprocess.run(cmd,check=True)
 elif mode=='run':
  review=json.loads((HERE/'prelaunch-acceptance.json').read_text());assert review['accepted'] and not review['unresolved_findings']
  assert all(sha(p)==v for p,v in review['reviewed_sha256'].items())
  command=['/bin/bash',str(WRAPPER),'--compiled-modules=existing','--threads=1','--gcthreads=1,0','--heap-size-hint=2G','--project='+str(target),str(HERE/'driver.jl'),str(target),str(out/'raw')]
  raise SystemExit(subprocess.call([sys.executable,str(GUARD),'run',str(pins),str(out),'--seconds','120','--',*command]))
 else:raise ValueError(mode)
if __name__=='__main__':main()
