"""Run one bounded Julia job with pinned sources and the established memory guard."""
from pathlib import Path
import hashlib,json,subprocess,sys,time,tomllib
ROOT=Path(__file__).resolve().parents[3]
OUT=Path(sys.argv[1]).resolve();OUT.mkdir(parents=True,exist_ok=False)
assert subprocess.run(['pgrep','-x','julia'],stdout=subprocess.DEVNULL).returncode==1
effective=ROOT
for arg in sys.argv[3:]:
 if arg.startswith('--project='):effective=Path(arg.split('=',1)[1]).resolve()
files=[]
for project in {ROOT,effective}:
 files += [*project.glob('src/**/*.jl'),*project.glob('test/**/*.jl'),project/'Project.toml',project/'Manifest.toml',project/'LocalPreferences.toml',project/'test/fixtures/solver/afiro.mps']
files += list(Path(__file__).resolve().parent.glob('*'))
# This script can also be loaded through -e, so direct argument discovery misses it.
files += [ROOT/'diagnostics/simplex-data-movement/reproduce/external.jl']
files += [Path('/home/jspitz/JSimplex.jl/.worktrees/primal-direction-prices/.superpowers/primal-prices/guard.py'),Path('/home/jspitz/.codex/worktrees/basis-update-chain-bench/JSimplex.jl/diagnostics/basis-memory/reproduce/julia.sh')]
for arg in sys.argv[3:]:
 candidate=Path(arg)
 if candidate.is_file():files.append(candidate.resolve())
manifest=ROOT/'diagnostics/basis-selective-preparation/reproduce/external-inputs.toml'
files += [manifest,*[Path(e['path']) for e in tomllib.loads(manifest.read_text())['cases']]]
files += [Path('/home/jspitz/mps/runtime.mps'),Path('/home/jspitz/mps/medium.mps'),Path('/home/jspitz/.codex/worktrees/simplex-certificate-repair/JSimplex.jl/.superpowers/certificate-repair/medium-primal-handoff.bin')]
files += list(Path('/home/jspitz/.codex/worktrees/basis-update-chain-bench/JSimplex.jl/.superpowers/medium-hh-main').glob('*/attempt-1/reports/*.bin'))
files += [Path('/home/jspitz/.codex/worktrees/simplex-certificate-repair/JSimplex.jl/.superpowers/certificate-repair/medium-dual-handoff.bin')]
files += [ROOT/'.superpowers/simplex-data-movement/runtime-final-v2/solve'/f'row-0-{i}.bin' for i in (1000,10000,30000,50000)]
files += [ROOT/'.superpowers/dual-allocation-cost/census/cost-medium.toml-state-0-1000.bin']
files += list((ROOT/'.superpowers/primal-certificate-work/capture').glob('*.bin'))
files += list(Path('/home/jspitz/.codex/worktrees/basis-update-chain-bench/JSimplex.jl/.superpowers/basis-chain-cost/histories').glob('*.bin'))
files=sorted({p.resolve() for p in files if p.is_file()})
def digest(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
 return h.hexdigest()
def identity():return {str(p):digest(p) for p in files}
pinned=identity();(OUT/'preflight.json').write_text(json.dumps(pinned,indent=2)+'\n')
cmd=['/usr/bin/time','-v','python3','/home/jspitz/JSimplex.jl/.worktrees/primal-direction-prices/.superpowers/primal-prices/guard.py','--seconds',sys.argv[2],'bash','/home/jspitz/.codex/worktrees/basis-update-chain-bench/JSimplex.jl/diagnostics/basis-memory/reproduce/julia.sh','--heap-size-hint=2G','--project='+str(ROOT),*sys.argv[3:]]
r=dict(command=cmd,started=time.time(),effective_project=str(effective))
with (OUT/'run.log').open('x') as log:
 p=subprocess.Popen(cmd,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT);r['pid']=p.pid
 (OUT/'current.json').write_text(json.dumps(r,indent=2)+'\n');r['returncode']=p.wait()
r['ended']=time.time();r['sources_unchanged']=identity()==pinned
(OUT/'process.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r))
assert r['sources_unchanged']
sys.exit(r['returncode'])
