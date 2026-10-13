from pathlib import Path
import subprocess,json,hashlib
D=Path(__file__).resolve().parent;R=D.parents[3];E=D.parent/'MA-E';H=D.parent/'MA-H';F=D.parent/'MA-F-repair';O=R/'.superpowers/simplex-core-architecture/MA-I/attempt-1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
names=json.loads((D/'publication-names.json').read_text());warnings=[];bindings={};origins={}
for n in names:
 p=R/n
 if not p.exists():continue
 if subprocess.run(['git','ls-files','--error-unmatch','--',n],cwd=R,capture_output=True).returncode==0:continue
 c=subprocess.run(['git','diff','--no-index','--check','--','/dev/null',n],cwd=R,text=True,capture_output=True)
 if c.stderr:raise ValueError(c.stderr)
 if not c.stdout:continue
 origin=None
 if p.is_relative_to(D/'overlays'):
  rel=p.relative_to(D/'overlays');origin=H/'candidate-markowitz.jl' if str(rel)=='candidate/src/markowitz_factorization.jl' else E/'overlays'/rel
 elif p.is_relative_to(D/'attempt-1'):origin=O/p.relative_to(D/'attempt-1')
 elif p.name in ['reference-forward.jl']:origin=H/p.name
 elif p.name in ['kernels.jl','reference-upper.jl','test-collector.jl','tests-instrumented.jl']:origin=F/p.name
 if origin is None or p.read_bytes()!=origin.read_bytes():raise ValueError(('non-verbatim whitespace',n,c.stdout))
 warnings.extend(c.stdout.splitlines());bindings[n]=sha(p);origins[n]=dict(path=str(origin),sha256=sha(origin))
c=subprocess.run(['git','diff','--check'],cwd=R,text=True,capture_output=True)
if c.returncode!=0 or c.stdout or c.stderr:raise ValueError('authored tracked diff whitespace')
with (D/'whitespace.json').open('x') as f:json.dump(dict(all_passed=True,warnings=sorted(warnings),sha256=bindings,origins=origins,scope='Only exact verbatim source/raw-copy warnings; authored tracked diff clean.'),f,indent=2);f.write('\n')
print('verbatim warnings',len(warnings),'files',len(bindings))
