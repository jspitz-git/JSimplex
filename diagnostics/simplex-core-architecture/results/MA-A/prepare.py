"""One-use offline synthetic oracle checks and launch manifest preparation."""
from common import *
from oracle import F,rounded,analyze
import copy

def synthetic():
 raw=dict(cases=[],errors=[],all_passed=True,ambient_restored=True,MA_source='/home/jspitz/.julia/packages/MutableArithmetics/SaQfc/src/MutableArithmetics.jl',MA_version='1.8.1',Julia_version='1.13.0')
 for bits in (128,256,512,0):
  for n,z in ((32,False),(256,False),(256,True)):
   a=[rounded(F(0) if z and i%8 else F(((17*i)%61-30)*2**80+(-1 if i%2 else 1),17),bits) for i in range(1,n+1)]
   b=[rounded(F((13*i)%47-23,19),bits) for i in range(1,n+1)]
   ex=sum(x*y for x,y in zip(a,b));mag=sum(abs(x*y) for x,y in zip(a,b));u=F(1,2**bits) if bits else F(0);seq=F(0)
   for x,y in zip(a,b):seq=rounded(seq+rounded(x*y,bits),bits)
   windows=[]
   for pair in range(1,11):
    for side in (('plain','buffered') if pair%2 else ('buffered','plain')):
     w=dict(seconds=1.0,bytes=32,allocations=32,gc_seconds=0.,compile_seconds=0.,recompile_seconds=0.,side=side,pair=pair,phase='warm' if pair<=3 else 'measured',repetitions=32,output=str(seq))
     w.update(dict.fromkeys(('same_sequential_result','exact_or_bounded','inputs_preserved','scratch_owners_preserved','precision_preserved'),True));windows.append(w)
   raw['cases'].append(dict(type='BigFloat' if bits else 'Rational{BigInt}',bits=bits,n=n,mostlyzero=z,checks=dict.fromkeys(('private_scratch','precision','outputs','input_and_owner_preservation','measured_compile_zero'),True),windows=windows,exact_dot=str(ex),absolute_error_bound=str((2*n*u)/(1-2*n*u)*mag),input_a=list(map(str,a)),input_b=list(map(str,b)),scratch_leaf_count=2 if bits else 12,scratch_graph_bytes=100,setup=dict(seconds=1.,bytes=32,allocations=2,compile_seconds=1.,recompile_seconds=0.)))
 return raw
raw=synthetic();checks={'synthetic_12_case_pass':raw_ok(raw)}
mutations={
 'missing_case':lambda r:r['cases'].pop(),
 'wrong_output':lambda r:r['cases'][0]['windows'][0].update(output='0'),
 'wrong_input':lambda r:r['cases'][0]['input_a'].__setitem__(0,'0'),
 'wrong_bound':lambda r:r['cases'][0].update(absolute_error_bound='0'),
 'owner_failure':lambda r:r['cases'][0]['windows'][0].update(scratch_owners_preserved=False),
 'precision_failure':lambda r:r['cases'][0]['windows'][0].update(precision_preserved=False),
 'measured_compile':lambda r:r['cases'][0]['windows'][6].update(compile_seconds=1.),
 'wrong_order':lambda r:r['cases'][0]['windows'][0].update(side='buffered'),
 'nonfinite_time':lambda r:r['cases'][0]['windows'][0].update(seconds=float('nan')),
 'negative_bytes':lambda r:r['cases'][0]['windows'][0].update(bytes=-1),
 'fake_truthy':lambda r:r.update(all_passed=1),
 'errors_present':lambda r:r['errors'].append('error')}
for name,mutate in mutations.items():
 r=copy.deepcopy(raw);mutate(r);checks['reject_'+name]=not raw_ok(r)
checks['nearest_even_low']=rounded(F(5,4),2)==1
checks['nearest_even_high']=rounded(F(7,4),2)==2
checks['negative_nearest_even']=rounded(F(-7,4),2)==-2
checks['full_loop_count']=(20*32+1)*(32+256+256)*4==1394816
require(all(checks.values()),'offline checks failed')
dump(D/'preparation.json',dict(all_passed=True,checks=checks,note='Synthetic Python only; not Julia syntax/runtime qualification.'))
paths=set(p for p in D.rglob('*') if p.is_file())
paths.update(R/p for p in subprocess.check_output(['git','-C',str(R),'ls-files','src','test','.github','Project.toml'],text=True).splitlines())
paths.update(R/p for p in ('Manifest.toml','LocalPreferences.toml'))
ma=Path('/home/jspitz/.julia/packages/MutableArithmetics/SaQfc')
paths.update(ma.glob('src/**/*.jl'));paths.add(ma/'Project.toml')
rt=Path('/home/jspitz/.julia/juliaup/julia-1.13.0+0.aarch64.linux.gnu')
# Concrete resolved native files; this is not a loader/cache confinement proof.
old=read(D.parent/'S4-Z/launch-pins.json')
paths.update(Path(p).resolve() for p in old['inventory'] if str(rt) in p and Path(p).is_file())
paths.update(rt/'share/julia/base'/p for p in ('gmp.jl','mpfr.jl','rational.jl','timing.jl'))
paths.update((WRAPPER,WRAPPER.parents[3]/'.superpowers/basis-chain-cost/julia.sh',Path('/usr/bin/python3'),Path('/bin/bash')))
# Parent calculation checked explicitly below.
paths.discard(WRAPPER.parents[3]/'.superpowers/basis-chain-cost/julia.sh')
paths.add(Path('/home/jspitz/.codex/worktrees/basis-update-chain-bench/JSimplex.jl/.superpowers/basis-chain-cost/julia.sh'))
required={str(p):sha(p) for p in sorted(paths)}
dump(D/'required-paths.json',required);paths.add(D/'required-paths.json')
pins={'files':sorted(map(str,paths)),'trees':[],'inputs':[],'inventory':{str(p):{'resolved':str(p.resolve(strict=True)),'sha256':sha(p)} for p in sorted(paths)}}
dump(D/'launch-pins.json',pins)
print(json.dumps(dict(checks=len(checks),pins=len(paths),manifest_sha256=sha(D/'launch-pins.json'))))
