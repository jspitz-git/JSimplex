"""Offline staging only; no Julia execution, no old script invocation."""
from pathlib import Path
import hashlib,json,subprocess,shutil
R=Path(__file__).resolve().parents[4];D=Path(__file__).resolve().parent
W=R/'.superpowers/direct-lu-markowitz-admission';W.mkdir(exist_ok=False)
C=R/'diagnostics/direct-lu-markowitz/reproduce'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
files=subprocess.check_output(['git','ls-files','src','Project.toml'],cwd=R,text=True).splitlines()
source={n:sha(R/n) for n in files}
for side in ('reference','candidate'):
 root=W/side;root.mkdir()
 for n in files:
  out=root/n;out.parent.mkdir(parents=True,exist_ok=True);out.write_bytes((R/n).read_bytes())
 env=R/'.superpowers/presolve-exact-cache/reference'
 if (env/'Project.toml').read_bytes()!=(R/'Project.toml').read_bytes():raise ValueError('environment Project mismatch')
 (root/'Manifest.toml').write_bytes((env/'Manifest.toml').read_bytes())
 if (env/'LocalPreferences.toml').exists(): (root/'LocalPreferences.toml').write_bytes((env/'LocalPreferences.toml').read_bytes())
 if side=='candidate':
  for n in ('factor-export.jl','direct-factor.jl'):(root/'src'/n).write_bytes((C/n).read_bytes())
  p=root/'src/JSimplex.jl';s=p.read_bytes();a=b'include("huangfu_hall_factorization.jl")\n';b=b'include("factor-export.jl")\ninclude("direct-factor.jl")\n'
  if s.count(a)!=1 or b in s:raise ValueError('root anchor')
  p.write_bytes(s.replace(a,a+b))
 for n in ('red.jl','correctness.jl','fixtures.jl'):(root/n).write_bytes((C/n).read_bytes())
# Exact unchanged blocks, not a Julia parser or a whole-file execution claim.
selections=[('markowitz-sparse.jl','test/markowitz_tests.jl','@testset "Markowitz sparse elimination and dense core"','@testset "Markowitz fill pivots and permutations"'),('markowitz-fill.jl','test/markowitz_tests.jl','@testset "Markowitz fill pivots and permutations"','@testset "Rejected singleton rows are reconsidered"'),('markowitz-triangular.jl','test/markowitz_tests.jl','@testset "Triangular updates accumulate over a Markowitz base"','@testset "Markowitz backend retains sparse storage and solve buffers"'),('stability.jl','test/triangular_stability_tests.jl','@testset "Triangular updates recover a well-conditioned basis"','@testset "Row swaps preserve dense, indexed and transposed solves"')]
focused=D/'focused';focused.mkdir();slices=[]
for name,path,start,end in selections:
 data=(R/path).read_bytes();a=start.encode();b=end.encode()
 if data.count(a)!=1 or data.count(b)!=1:raise ValueError('nonunique block')
 startbyte=data.index(a);endbyte=data.index(b,startbyte);part=data[startbyte:endbyte]
 (focused/name).write_bytes(part);slices.append(dict(output=name,source=path,start_byte=startbyte,end_byte=endbyte,source_sha256=sha(R/path),slice_sha256=sha(focused/name)))
for name,path in [('prepared.jl','test/triangular_prepared_spike_tests.jl'),('lifecycle.jl','test/triangular_preparation_lifecycle_tests.jl')]:
 (focused/name).write_bytes((R/path).read_bytes());slices.append(dict(output=name,source=path,start_byte=0,end_byte=(R/path).stat().st_size,source_sha256=sha(R/path),slice_sha256=sha(focused/name)))
with (D/'staging.json').open('x') as f:json.dump(dict(root=str(W),source_sha256=source,focused=slices,scope='UNEXECUTED source overlays; user environments unchanged'),f,indent=2);f.write('\n')
print('Prepared two fresh ordinary overlays and six unchanged focused selections.')
